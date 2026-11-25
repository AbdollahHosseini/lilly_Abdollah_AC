"""
FastAPI application for managing a list of medicines.

Endpoints:
- GET  /medicines             - all medicines (read from data.json)
- GET  /medicines/unreliable  - same data, but fails ~30% of the time
- GET  /medicines/{name}      - a single medicine by name
- POST /create               - create a medicine (not part of the tasks)
- POST /update               - update a medicine's price (not part of the tasks)
- DELETE /delete             - delete a medicine (not part of the tasks)
"""
import json
import random
import time

from fastapi import FastAPI, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends

import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

FAILURE_RATE = 0.3


def _load_medicines():
    with open("data.json") as meds:
        data = json.load(meds)
        for med in data["medicines"]:
            try:
                if med.get("name") is None:
                    med["name"] = "Unknown"
                print({"error": "Invalid medicine name format."})

                if len(med["name"]) == 0:
                    med["name"] = "Unknown"
                    print({"error": "Invalid medicine name format."})

                if type(med["price"]) is not float:
                    try:
                        med["price"] = float(med["price"])
                    except (ValueError, TypeError):
                        med["price"] = -1
                        print({"error": "Invalid medicine price format."})

                elif med["price"] is None:
                    med["price"] = 0.0
                    print({"error": "Invalid medicine price format."})

                else:
                    if med["price"] < 0:
                        med["price"] = abs(med["price"])
                        print({"error": "Invalid medicine price format."})

            except KeyError:
                med["name"] = "Missing Keys, Ignore this record."
                med["price"] = -1
                print({"error": "Invalid medicine data format."})
                    
    return data["medicines"]


@app.get("/medicines")
def get_all_meds():
    return {"medicines": _load_medicines()}


@app.get("/medicines/unreliable")
def get_unreliable_meds(response: Response):
    if random.random() < FAILURE_RATE:
        response.status_code = 500
        time.sleep(1)  # Simulate a delay for the unreliable endpoint
        return {"error": "Too many requests, try reloading the page momentarily.", "medicines": get_unreliable_meds(response).get("medicines", [])} 
    return {"medicines": _load_medicines()}


@app.get("/medicines/{name}")
def get_single_med(name: str):
    for med in _load_medicines():
        if med.get("name") == name:
            return med
    return {"error": "Medicine not found"}


@app.post("/create")
def create_med(name: str = Form(...), price: float = Form(...)):
    with open("data.json", "r+") as meds:
        current_db = json.load(meds)
        new_med = {"name": name, "price": price}
        current_db["medicines"].append(new_med)
        meds.seek(0)
        json.dump(current_db, meds)
        meds.truncate()

    return {"message": f"Medicine created successfully with name: {name}"}


@app.post("/update")
def update_med(name: str = Form(...), price: float = Form(...)):
    with open("data.json", "r+") as meds:
        current_db = json.load(meds)
        for med in current_db["medicines"]:
            if med.get("name") == name:
                med["price"] = price
                meds.seek(0)
                json.dump(current_db, meds)
                meds.truncate()
                return {"message": f"Medicine updated successfully with name: {name}"}
    return {"error": "Medicine not found"}


@app.delete("/delete")
def delete_med(name: str = Form(...)):
    with open("data.json", "r+") as meds:
        current_db = json.load(meds)
        for med in current_db["medicines"]:
            if med.get("name") == name:
                current_db["medicines"].remove(med)
                meds.seek(0)
                json.dump(current_db, meds)
                meds.truncate()
                return {"message": f"Medicine deleted successfully with name: {name}"}
    return {"error": "Medicine not found"}


# Add your average-price function here
@app.get('/average-price')
def average_price():
    medicines = _load_medicines()
    if not medicines:
        return {"error": "No medicines found."}
    
    total_price = sum(med.get("price", 0) for med in medicines if med.get("price") is not None and med.get("price") >= 0)
    average = total_price / len(medicines)
    
    return {"average_price": average}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
