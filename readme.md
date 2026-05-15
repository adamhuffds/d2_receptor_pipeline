# D2 Receptor Bioactivity Ingestion Pipeline

A data ingestion and exploratory analysis pipeline for human D2 dopamine receptor (CHEMBL217) bioactivity data sourced from the ChEMBL REST API. This project demonstrates multi-endpoint API integration, relational data modeling, and exploratory analysis of pharmaceutical bioactivity data.

## Project Structure

    d2-receptor-pipeline/
    ├── notebooks/             
    │   └── 01_eda.ipynb       # Exploratory data analysis
    ├── pipeline/
    │   ├── etl.py             # ChEMBL data ingestion pipeline
    │   └── schema.sql         # PostgreSQL schema definition
    ├── .env                   # Environment variable template
    ├── .env.example
    ├── .gitignore
    ├── requirements.txt       # Python dependencies
    └── README.md

## Stack

- **Python** — core pipeline language
- **requests** — ChEMBL REST API calls
- **SQLAlchemy 2.0** — PostgreSQL ORM and query layer
- **PostgreSQL** — relational storage for compounds, assays, and bioactivity
- **pandas** — data loading and analysis
- **matplotlib / seaborn** — visualization

## Data Sources

| Source | Endpoint | Data Retrieved |
|--------|----------|----------------|
| ChEMBL Activity API | `/activity` | IC50 values, assay metadata, standard relations |
| ChEMBL Molecule API | `/molecule` | Lipinski descriptors, SMILES, compound names |

ChEMBL REST API docs: https://www.ebi.ac.uk/chembl/api/data/docs

## Pipeline

### 1. Schema creation

```bash
psql -U your_user -d d2_qsar -f schema.sql
```

Creates a `qsar` schema with three tables:
- `qsar.compounds` — unique compounds with Lipinski descriptors
- `qsar.assays` — assay metadata
- `qsar.bioactivity` — IC50 measurements linking compounds and assays

### 2. Data ingestion

```bash
python etl.py
```

The ETL pipeline:
1. Fetches all IC50 records for CHEMBL217 from the ChEMBL activity endpoint (paginated, 100 records/page)
2. Extracts unique compound IDs and batch-fetches Lipinski descriptors from the molecule endpoint
3. Upserts compounds and assays, then inserts bioactivity records
4. Stores raw IC50 values, pIC50 (where provided by ChEMBL), and standard relation (`=`, `>`, `<`)

### 3. Exploratory analysis
Open `01_eda.ipynb` in Jupyter. Reads directly from PostgreSQL — no intermediate files required.

## Setup

```bash
# Clone and set up environment
git clone https://github.com/adamhuffds/d2-receptor-pipeline
cd d2-receptor-pipeline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure database credentials
cp .env.example .env
# edit .env with your PostgreSQL credentials

# Create schema and run ETL
psql -U your_user -d d2_qsar -f schema.sql
python etl.py

# Launch notebook
jupyter notebook
```

## Dataset Summary

| Metric | Value |
|--------|-------|
| Total IC50 records | 1,580 |
| Unique compounds | ~1,100 |
| Unique assays | ~30 |
| Records with pIC50 | 1,091 |
| pIC50 mean | 6.81 |
| pIC50 std | 1.22 |

## Key EDA Findings

- pIC50 is approximately normally distributed (mean 6.81, std 1.22), well suited for regression modeling
- Lipinski descriptors are consistent with CNS drug-like compounds — low PSA (mean 54 Å²) and low HBD (mean 1.0) support blood-brain barrier penetration
- Individual descriptor correlations with pIC50 are weak, suggesting nonlinear modeling will outperform linear approaches
- ~31% of records lack pIC50 due to censored measurements (`>`, `<`) or implausible values — documented for preprocessing

## Status

**Phase 1 complete** — ChEMBL ingestion pipeline and exploratory data analysis.

**Phase 2 (data preprocessing and QSAR modeling)** - to follow.

## Author

Adam Huff — [github.com/adamhuffds](https://github.com/adamhuffds)