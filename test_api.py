import requests
import json

def test1():

    url = "https://www.ebi.ac.uk/chembl/api/data/activity.json"

    params = {
        "target_chembl_id": "CHEMBL217",
        "standard_type": "IC50",
        "standard_units": "nM",
        "limit": 1,
        "offset": 0,
    }

    response = requests.get(url, params=params, timeout=30)
    print(response.status_code)
    print(json.dumps(response.json(), indent=2))

def test2():
    url = "https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL303519.json"
    response = requests.get(url, timeout=30)
    print(json.dumps(response.json(), indent=2))    

def test3():
    url = "https://www.ebi.ac.uk/chembl/api/data/molecule.json"
    params = {
        "molecule_chembl_id__in": "CHEMBL303519,CHEMBL1,CHEMBL2",
        "limit": 3,
    }
    response = requests.get(url, params=params, timeout=30)
    print(json.dumps(response.json(), indent=2))

def test4():
    url = "https://www.ebi.ac.uk/chembl/api/data/activity.json"

    params = {
        "target_chembl_id": "CHEMBL217",
        "standard_type": "IC50",
        "standard_units": "nM",
        "limit": 100,
        "offset": 0,
    }

    response = requests.get(url, params=params, timeout=30)
    data = response.json()

    # Check how many we got and what the pagination metadata looks like
    print("Records returned:", len(data["activities"]))
    print("Page meta:", json.dumps(data["page_meta"], indent=2))

test1()