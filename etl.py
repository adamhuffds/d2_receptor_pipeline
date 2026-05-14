# ==============================
# Imports
# ==============================

import os
import logging
import requests

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# ==============================
# Logging
# ==============================

logging.basicConfig( # configure logging params
    level=logging.INFO, # show INFO and above
    format="%(asctime)s  %(levelname)s  %(message)s", # format of acutal log - timestamp, log level, message
    datefmt="%H:%M:%S", # date time format
)

log = logging.getLogger(__name__) # create logger instance

# ==============================
# Configuration
# ==============================

load_dotenv()

DB_URL = (
    f"postgresql+psycopg2://"
    f"{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}"
    f"/{os.environ['DB_NAME']}"
)

BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
D2_TARGET_ID = "CHEMBL217"

# ==============================
# Fetch activity data from ChEMBL
# ==============================

def fetch_activity_data() -> list[dict]:
    log.info("Fetching activity data...")
    records = []
    params = {
        "target_chembl_id": D2_TARGET_ID,
        "standard_type": "IC50",
        "standard_units": "nM",
        "limit": 100,
        "offset": 0,
    }

    while True:
        r = requests.get(f"{BASE_URL}/activity.json", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        records.extend(data["activities"])
        log.info(f"  Fetched {len(records)}/{data['page_meta']['total_count']}")
        if data["page_meta"]["next"] is None:
            break
        params["offset"] += params["limit"]

    log.info(f"Total activity records: {len(records)}")
    return records

# ==============================
# Fetch molecule data from ChEMBL
# ==============================

def fetch_molecule_data(chembl_ids: list[str]) -> dict[str, dict]:
    log.info(f"Fetching molecule properties for {len(chembl_ids)} compounds...")
    mol_map = {}
    batch_size = 100

    for i in range(0, len(chembl_ids), batch_size):
        batch = chembl_ids[i:i + batch_size]
        params = {
            "molecule_chembl_id__in": ",".join(batch),
            "limit": batch_size,
            "offset": 0,
        }

        while True:
            r = requests.get(f"{BASE_URL}/molecule.json", params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            for mol in data["molecules"]:
                cid = mol.get("molecule_chembl_id")
                if cid:
                    mol_map[cid] = mol
            if data["page_meta"]["next"] is None:
                break
            params["offset"] += params["limit"]

        log.info(f"  Processed {min(i + batch_size, len(chembl_ids))}/{len(chembl_ids)}")

    log.info(f"Total molecule records: {len(mol_map)}")
    return mol_map

# ==============================
# Load ChEMBL data into Database
# ==============================

def load_data(activity_records: list[dict], mol_map: dict[str, dict], engine) -> None:
    compound_id_map: dict[str, int] = {}
    assay_id_map: dict[str, int] = {}

    with Session(engine) as session:

        log.info("Upserting compounds...")
        for rec in activity_records:
            chembl_id = rec.get("molecule_chembl_id")
            if not chembl_id or chembl_id in compound_id_map:
                continue

            mol = mol_map.get(chembl_id, {})
            props = mol.get("molecule_properties") or {}

            result = session.execute(
                text("""
                    INSERT INTO qsar.compounds
                        (chembl_id, canonical_smiles, pref_name,
                         mw, alogp, hbd, hba, psa, rtb, ro5_violations)
                    VALUES
                        (:chembl_id, :canonical_smiles, :pref_name,
                         :mw, :alogp, :hbd, :hba, :psa, :rtb, :ro5_violations)
                    ON CONFLICT (chembl_id) DO NOTHING
                    RETURNING id
                """),
                {
                    "chembl_id":        chembl_id,
                    "canonical_smiles": rec.get("canonical_smiles"),
                    "pref_name":        mol.get("pref_name"),
                    "mw":               props.get("mw_freebase"),
                    "alogp":            props.get("alogp"),
                    "hbd":              props.get("hbd"),
                    "hba":              props.get("hba"),
                    "psa":              props.get("psa"),
                    "rtb":              props.get("rtb"),
                    "ro5_violations":   props.get("num_ro5_violations"),
                },
            )

            row = result.fetchone()
            if row:
                compound_id_map[chembl_id] = row[0]
            else:
                existing = session.execute(
                    text("SELECT id FROM qsar.compounds WHERE chembl_id = :cid"),
                    {"cid": chembl_id},
                ).fetchone()
                if existing:
                    compound_id_map[chembl_id] = existing[0]

        log.info(f"Compounds processed: {len(compound_id_map)}")

        log.info("Upserting assays...")
        for rec in activity_records:
            assay_chembl_id = rec.get("assay_chembl_id")
            if not assay_chembl_id or assay_chembl_id in assay_id_map:
                continue

            result = session.execute(
                text("""
                    INSERT INTO qsar.assays
                        (chembl_id, assay_type, description)
                    VALUES
                        (:chembl_id, :assay_type, :description)
                    ON CONFLICT (chembl_id) DO NOTHING
                    RETURNING id
                """),
                {
                    "chembl_id":   assay_chembl_id,
                    "assay_type":  rec.get("assay_type"),
                    "description": rec.get("assay_description"),
                },
            )

            row = result.fetchone()
            if row:
                assay_id_map[assay_chembl_id] = row[0]
            else:
                existing = session.execute(
                    text("SELECT id FROM qsar.assays WHERE chembl_id = :cid"),
                    {"cid": assay_chembl_id},
                ).fetchone()
                if existing:
                    assay_id_map[assay_chembl_id] = existing[0]

        log.info(f"Assays processed: {len(assay_id_map)}")

        log.info("Inserting bioactivity records...")
        inserted = 0
        skipped = 0
        for rec in activity_records:
            compound_id = compound_id_map.get(rec.get("molecule_chembl_id", ""))
            assay_id = assay_id_map.get(rec.get("assay_chembl_id", ""))

            if not compound_id or not assay_id:
                skipped += 1
                continue

            session.execute(
                text("""
                    INSERT INTO qsar.bioactivity
                        (compound_id, assay_id, activity_type,
                         value, units, pic50, relation, activity_comment)
                    VALUES
                        (:compound_id, :assay_id, :activity_type,
                         :value, :units, :pic50, :relation, :activity_comment)
                """),
                {
                    "compound_id":      compound_id,
                    "assay_id":         assay_id,
                    "activity_type":    rec.get("standard_type"),
                    "value":            rec.get("standard_value"),
                    "units":            rec.get("standard_units"),
                    "pic50":            rec.get("pchembl_value"),
                    "relation":         rec.get("standard_relation"),
                    "activity_comment": rec.get("activity_comment"),
                },
            )
            inserted += 1

        session.commit()
        log.info(f"Bioactivity inserted: {inserted}, skipped: {skipped}")

# ==============================
# Main
# ==============================

if __name__ == "__main__":
    log.info("Connecting to database...")
    engine = create_engine(DB_URL, echo=False)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    log.info("Database connection OK.")

    activity_records = fetch_activity_data()

    chembl_ids: list[str] = list({
        rec["molecule_chembl_id"]
        for rec in activity_records
        if rec.get("molecule_chembl_id") is not None
    })

    mol_map = fetch_molecule_data(chembl_ids)
    load_data(activity_records, mol_map, engine)
    log.info("ETL complete.")