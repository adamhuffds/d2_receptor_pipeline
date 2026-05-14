CREATE SCHEMA IF NOT EXISTS qsar;

CREATE TABLE IF NOT EXISTS qsar.compounds (
    id SERIAL PRIMARY KEY, 
    chembl_id VARCHAR(20) UNIQUE NOT NULL,
    canonical_smiles TEXT,
    pref_name VARCHAR(255),
    mw NUMERIC,
    alogp NUMERIC,
    hbd INTEGER,
    hba INTEGER,
    psa NUMERIC,
    rtb INTEGER,
    ro5_violations INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS qsar.assays (
    id SERIAL PRIMARY KEY,
    chembl_id VARCHAR(20) UNIQUE NOT NULL,
    assay_type VARCHAR(10),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS qsar.bioactivity (
    id SERIAL PRIMARY KEY,
    compound_id INTEGER NOT NULL REFERENCES qsar.compounds(id),
    assay_id INTEGER NOT NULL REFERENCES qsar.assays(id),
    activity_type VARCHAR(50),
    value NUMERIC,
    relation VARCHAR(5),
    units VARCHAR(20),
    pic50 NUMERIC,
    activity_comment VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bioactivity_compound_id
    ON qsar.bioactivity(compound_id);

CREATE INDEX IF NOT EXISTS idx_bioactivity_assay_id
    ON qsar.bioactivity(assay_id);

CREATE INDEX IF NOT EXISTS id_compounds_chembl_id
    ON qsar.compounds(chembl_id);