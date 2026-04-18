"""
SwiftMedAI FastAPI backend — production REST interface.
Run: uvicorn backend.api:app --reload --port 8000
"""
import os
import sys
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.drone_simulator import DRONE_BASE, DroneSimulator
from backend.gemini_triage import triage_incident
from backend.omnicell import PayloadCabinet

app = FastAPI(
    title="SwiftMedAI API",
    description="Autonomous Emergency Medical Supply Dispatch System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class IncidentRequest(BaseModel):
    location: str
    coords: Optional[List[float]] = None
    symptoms: str
    vitals: str
    scenario_name: Optional[str] = ""
    api_key: Optional[str] = None


class DroneRouteRequest(BaseModel):
    incident_coords: List[float]


class AuthRequest(BaseModel):
    clinician_id: str
    items: List[str]


@app.get("/health")
def health_check():
    return {"status": "operational", "service": "SwiftMedAI", "version": "1.0.0"}


@app.post("/triage")
def triage_endpoint(incident: IncidentRequest):
    return triage_incident(
        symptoms=incident.symptoms,
        location=incident.location,
        vitals=incident.vitals,
        scenario_name=incident.scenario_name or "",
        api_key=incident.api_key or os.getenv("GEMINI_API_KEY"),
    )


@app.post("/drone/route")
def plan_drone_route(request: DroneRouteRequest):
    sim = DroneSimulator(incident_coords=request.incident_coords)
    return {
        "base_coords": DRONE_BASE,
        "incident_coords": request.incident_coords,
        "distance_miles": round(sim.distance_miles, 2),
        "eta_seconds": sim.total_eta_seconds,
        "heading_degrees": round(sim.heading, 1),
        "waypoint_count": len(sim.waypoints),
    }


@app.post("/omnicell/authorize")
def authorize_payload(request: AuthRequest):
    cabinet = PayloadCabinet()
    auth_code = cabinet.request_authorization(request.clinician_id, request.items)
    return {
        "auth_code": auth_code,
        "status": cabinet.state.value,
        "items": request.items,
        "clinician": request.clinician_id,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
