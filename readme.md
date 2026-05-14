Goal: predict IC50/pIC50 values for dopamine D2 receptor ligands using ChEMBL bioactivity data

How to run the code:
1) Create postgres database called d2_qsar
2) Run schema.sql to create schema, tables, and indices
3) Run etl.py to pull data from ChEMBL for compounds, assays, and bioactivity associated with dopamine D2 receptor
4) Run 01_eda.ipynb