import asyncio
import json
from typing import Set, Dict, List, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Body
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    DateTime,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
from datetime import datetime
from pydantic import BaseModel, field_validator
from config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
)
# SQLAlchemy setup
DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL)
metadata = MetaData()
# Define the ProcessedAgentData table
processed_agent_data = Table(
    "processed_agent_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("road_state", String),
    Column("user_id", Integer),
    Column("x", Float),
    Column("y", Float),
    Column("z", Float),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)
SessionLocal = sessionmaker(bind=engine)


# SQLAlchemy model
class ProcessedAgentDataInDB(BaseModel):
    id: int
    road_state: str
    user_id: int
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime


# FastAPI models
class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float


class GpsData(BaseModel):
    latitude: float
    longitude: float


class AgentData(BaseModel):
    user_id: int
    accelerometer: AccelerometerData
    gps: GpsData
    timestamp: datetime

    @classmethod
    @field_validator("timestamp", mode="before")
    def check_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError(
                "Invalid timestamp format. Expected ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)."
            )


class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData

# FastAPI app setup
app = FastAPI()

# WebSocket subscriptions
subscriptions: Dict[int, Set[WebSocket]] = {}


# FastAPI WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    if user_id not in subscriptions:
        subscriptions[user_id] = set()
    subscriptions[user_id].add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions[user_id].remove(websocket)


# Function to send data to subscribed users
async def send_data_to_subscribers(user_id: int, data):
    if user_id in subscriptions:
        for websocket in subscriptions[user_id]:
            await websocket.send_json(json.dumps(data))


# FastAPI CRUDL endpoints!!!

@app.post("/processed_agent_data/")
async def create_processed_agent_data(data: List[ProcessedAgentData]):
    if not data:
        return

    flatten_data = [
        {
            "road_state": p_agent_data.road_state,
            "user_id": p_agent_data.agent_data.user_id,
            "x": p_agent_data.agent_data.accelerometer.x,
            "y": p_agent_data.agent_data.accelerometer.y,
            "z": p_agent_data.agent_data.accelerometer.z,
            "latitude": p_agent_data.agent_data.gps.latitude,
            "longitude": p_agent_data.agent_data.gps.longitude,
            "timestamp": p_agent_data.agent_data.timestamp,
        }
        for p_agent_data in data
    ]

    with SessionLocal() as session:
        try:
            session.bulk_insert_mappings(ProcessedAgentData, flatten_data)
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Failed to insert data") from e

        # Send new data to subscribers
        user_id = data[0].agent_data.user_id
        await send_data_to_subscribers(
            user_id,
            [{**d, "timestamp": d["timestamp"].isoformat()} for d in flatten_data],
        )


@app.get("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def read_processed_agent_data(processed_agent_data_id: int):
    with SessionLocal() as session:
        result = session.query(ProcessedAgentData).filter(ProcessedAgentData.id == processed_agent_data_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="ProcessedAgentData not found")
        return result


@app.get("/processed_agent_data/", response_model=list[ProcessedAgentDataInDB])
def list_processed_agent_data():
    with SessionLocal() as session:
        return session.query(ProcessedAgentData).all()


@app.put("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def update_processed_agent_data(processed_agent_data_id: int, data: ProcessedAgentData):
    agent_data = data.agent_data
    update_values = {
        "road_state": data.road_state,
        "user_id": agent_data.user_id,
        "x": agent_data.accelerometer.x,
        "y": agent_data.accelerometer.y,
        "z": agent_data.accelerometer.z,
        "latitude": agent_data.gps.latitude,
        "longitude": agent_data.gps.longitude,
        "timestamp": agent_data.timestamp,
    }
    with SessionLocal() as session:
        try:
            result = session.query(ProcessedAgentData).filter(ProcessedAgentData.id == processed_agent_data_id) \
                .update(update_values, synchronize_session=False)
            session.commit()
            if not result:
                raise HTTPException(status_code=404, detail="ProcessedAgentData not found")
            return result
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Failed to update data") from e


@app.delete("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def delete_processed_agent_data(processed_agent_data_id: int):
    with SessionLocal() as session:
        try:
            result = session.query(ProcessedAgentData).filter(ProcessedAgentData.id == processed_agent_data_id) \
                .delete(synchronize_session=False)
            session.commit()
            if not result:
                raise HTTPException(status_code=404, detail="ProcessedAgentData not found")
            return result
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Failed to delete data") from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
