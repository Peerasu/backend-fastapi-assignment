from fastapi import FastAPI, HTTPException, Body
from datetime import date, datetime
from pymongo import MongoClient
from pydantic import BaseModel

from dotenv import load_dotenv
import os
import urllib
load_dotenv('.env')

user = os.getenv('username')
password = urllib.parse.quote(os.getenv('password'))

DATABASE_NAME = "exceed07"
COLLECTION_NAME = "reservation_Peerasu"
MONGO_DB_URL = "mongodb://exceed07:8td6VF6w@mongo.exceed19.online:8443/?authMechanism=DEFAULT"
MONGO_DB_PORT = 8443

class Reservation(BaseModel):
    name : str
    start_date: date
    end_date: date
    room_id: int


client = MongoClient(f"{MONGO_DB_URL}")

db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]

app = FastAPI()

def room_avaliable(room_id: int, start_date: str, end_date: str):
    query={"room_id": room_id,
           "$or": 
                [{"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": start_date}}]},
                 {"$and": [{"start_date": {"$lte": end_date}}, {"end_date": {"$gte": end_date}}]},
                 {"$and": [{"start_date": {"$gte": start_date}}, {"end_date": {"$lte": end_date}}]}]
            }
    
    result = collection.find(query, {"_id": 0})
    list_cursor = list(result)

    return not len(list_cursor) > 0

@app.get("/reservation/by-name/{name}")
def get_reservation_by_name(name:str):
    result = list(collection.find({"name": name}, {"_id": 0}))
    if len(result) < 0:
        raise HTTPException(status_code=400)
    return {"result": result}

@app.get("/reservation/by-room/{room_id}")
def get_reservation_by_room(room_id: int):
    result = list(collection.find({"room_id": room_id}, {"_id": 0}))
    return {"result": result}

@app.post("/reservation")
def reserve(reservation : Reservation):
    s = reservation.start_date
    e = reservation.end_date
    rid = reservation.room_id

    if s > e or rid > 10 or rid < 1:
        raise HTTPException(status_code=400)
    if not room_avaliable(rid, str(s), str(e)):
        raise HTTPException(status_code=400)
    
    collection.insert_one({"name": reservation.name,
                             "start_date": reservation.start_date.strftime("%Y-%m-%d"),
                             "end_date": reservation.end_date.strftime("%Y-%m-%d"), 
                             "room_id": reservation.room_id})


@app.put("/reservation/update")
def update_reservation(reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()):
    ns = new_start_date.strftime("%Y-%m-%d")
    ne = new_end_date.strftime("%Y-%m-%d")
    rid = reservation.room_id

    if (not room_avaliable(rid, str(ns), str(ne))) or ns > ne:
        raise HTTPException(status_code=400)
    collection.update_one({"room_id": rid}, {"$set": {"start_date": ns, "end_date": ne}})

@app.delete("/reservation/delete")
def cancel_reservation(reservation: Reservation):
    result = list(collection.find_one({ "name": reservation.name,
                                    "start_date": reservation.start_date.strftime("%Y-%m-%d"),
                                    "end_date": reservation.end_date.strftime("%Y-%m-%d"),
                                    "room_id": reservation.room_id}))
    if len(result) < 0:
        raise HTTPException(status_code=400)
    collection.delete_one({"name": reservation.name})