"""
SwiftMedAI — Autonomous Emergency Supply Dashboard
Run: streamlit run app.py
"""
import math
import os
import sys
import time
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from PIL import Image
from backend.drone_simulator import DRONE_BASE, DroneSimulator
from backend.gemini_triage import DEMO_RESPONSES, triage_incident
from backend.omnicell import UNLOCK_SEQUENCE, PayloadCabinet, PayloadState
from backend.dispatch_911 import stream_transcript, SCENARIO_TRANSCRIPTS

load_dotenv()

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SwiftMedAI — Emergency Response",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* Dark theme base */
.stApp { background-color: #05070a; color: #e8eaf6; }
section[data-testid="stSidebar"] { background-color: #080c14; border-right: 1px solid #1e2d4d; }
.block-container { padding-top: 1.5rem; }

/* Glassmorphism Metric cards */
[data-testid="metric-container"] {
    background: rgba(20, 25, 40, 0.4);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 16px;
    padding: 16px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    transition: transform 0.3s ease, border-color 0.3s ease;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    border-color: rgba(0, 212, 255, 0.5);
}
[data-testid="stMetricLabel"] { color: #8892a4 !important; font-size: 0.8em !important; letter-spacing: 1px; }
[data-testid="stMetricValue"] { color: #00d4ff !important; font-weight: 900; }

/* Severity badges */
.badge {
    display: inline-block;
    padding: 6px 20px;
    border-radius: 20px;
    font-weight: 800;
    font-size: 0.9em;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.badge-CRITICAL { background: linear-gradient(135deg,#ff1a1a,#cc0000); color:#fff; box-shadow:0 0 20px rgba(255,26,26,0.5); }
.badge-HIGH     { background: linear-gradient(135deg,#ff6600,#cc4400); color:#fff; box-shadow:0 0 15px rgba(255,102,0,0.4); }
.badge-MODERATE { background: linear-gradient(135deg,#ffcc00,#cc9900); color:#111; }
.badge-LOW      { background: linear-gradient(135deg,#00aa44,#007730); color:#fff; }

/* Glassmorphism Info Cards */
.info-card {
    background: rgba(20, 25, 40, 0.4);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(30, 45, 77, 0.4);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
}
.card-title {
    color: #00d4ff;
    font-size: 0.8em;
    font-weight: 800;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-bottom: 12px;
    border-left: 3px solid #00d4ff;
    padding-left: 10px;
}

/* Mission phase list */
.phase { display: flex; align-items: center; gap: 12px; padding: 8px 0; font-size: 0.95em; }
.phase-dot-done    { width:12px; height:12px; border-radius:50%; background:#00ff88; flex-shrink:0; box-shadow: 0 0 8px #00ff88; }
.phase-dot-active  { width:12px; height:12px; border-radius:50%; background:#00d4ff; flex-shrink:0; animation:pulse-glow 2s infinite; }
.phase-dot-pending { width:12px; height:12px; border-radius:50%; background:#1a2235; flex-shrink:0; border: 1px solid #2a3555; }
@keyframes pulse-glow { 0%,100%{opacity:1; box-shadow: 0 0 15px #00d4ff;} 50%{opacity:0.5; box-shadow: 0 0 5px #00d4ff;} }

/* Command Center feed */
.vision-feed {
    border: 2px solid #1e2d4d;
    border-radius: 12px;
    overflow: hidden;
    position: relative;
    background: #000;
    box-shadow: 0 0 30px rgba(0,0,0,0.8);
}

/* HUD elements */
.hud-overlay {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    z-index: 10;
    font-family: 'Courier New', monospace;
    color: #00ff88;
}
.hud-corner {
    position: absolute;
    width: 20px; height: 20px;
    border: 2px solid rgba(0, 255, 136, 0.4);
}
.top-left { top: 20px; left: 20px; border-right: 0; border-bottom: 0; }
.top-right { top: 20px; right: 20px; border-left: 0; border-bottom: 0; }
.bottom-left { bottom: 20px; left: 20px; border-right: 0; border-top: 0; }
.bottom-right { bottom: 20px; right: 20px; border-left: 0; border-top: 0; }

/* Altitude & Speed Tapes */
.tape-container {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    width: 50px;
    height: 180px;
    background: rgba(0,0,0,0.4);
    border: 1px solid rgba(0, 255, 136, 0.3);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.alt-tape { right: 30px; }
.spd-tape { left: 30px; }
.tape-tick {
    height: 30px;
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 0.7em;
    border-bottom: 1px solid rgba(0, 255, 136, 0.1);
}

/* Dynamic Crosshair */
.crosshair {
    position: absolute;
    top: 50%; left: 50%;
    width: 100px; height: 100px;
    transform: translate(-50%, -50%);
    animation: sway 4s ease-in-out infinite;
}
.cross-line {
    position: absolute;
    background: rgba(0, 255, 136, 0.6);
}
.cross-h { top: 50%; left: 0; width: 100%; height: 1px; }
.cross-v { left: 50%; top: 0; height: 100%; width: 1px; }
.cross-circle {
    position: absolute;
    top: 50%; left: 50%;
    width: 40px; height: 40px;
    border: 1px solid rgba(0, 255, 136, 0.4);
    border-radius: 50%;
    transform: translate(-50%, -50%);
}
@keyframes sway {
    0%, 100% { transform: translate(-50%, -50%) rotate(0deg); }
    25% { transform: translate(-48%, -52%) rotate(0.5deg); }
    75% { transform: translate(-52%, -48%) rotate(-0.5deg); }
}

/* Glitch/Scanline */
.scanline {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 2px;
    background: rgba(0, 255, 136, 0.1);
    z-index: 11;
    animation: scanline 8s linear infinite;
}
@keyframes scanline {
    0% { top: 0%; }
    100% { top: 100%; }
}

/* Phase Transitions */
.transition-screen {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(5, 7, 10, 0.95);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    backdrop-filter: blur(20px);
}
.loader-ring {
    width: 60px; height: 60px;
    border: 3px solid rgba(0, 212, 255, 0.1);
    border-top: 3px solid #00d4ff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 20px;
}
@keyframes spin { 100% { transform: rotate(360deg); } }

/* Audio Wave Visualizer */
.waveform {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 50px;
  margin: 15px 0;
}
.bar {
  width: 4px;
  height: 10px;
  background: linear-gradient(to top, #00d4ff, #00ff88);
  border-radius: 4px;
  animation: pulse-wave 1.2s ease-in-out infinite;
}
.bar:nth-child(2) { animation-delay: 0.1s; }
.bar:nth-child(3) { animation-delay: 0.2s; }
.bar:nth-child(4) { animation-delay: 0.3s; }
.bar:nth-child(5) { animation-delay: 0.4s; }
.bar:nth-child(6) { animation-delay: 0.5s; }
@keyframes pulse-wave { 0%, 100% { height: 12px; } 50% { height: 45px; } }
</style>
""",
    unsafe_allow_html=True,
)

# ── DEMO SCENARIOS ─────────────────────────────────────────────────────────────
SCENARIOS = {
    "Search and Rescue (SAR)": {
        "icon": "🛰️",
        "label": "Search and Rescue",
        "subtitle": "Missing Hiker · Oakland Hills · SAR-1 Drone",
        "location": "Redwood Regional Park, Oakland Hills (37.8075°N, 122.1943°W)",
        "coords": [37.8075, -122.1943],
        "symptoms": (
            "Missing hiker reported 4 hours ago. Suspected dehydration or fall. "
            "Drone-view analysis required for visual identification."
        ),
        "vitals": "N/A — Search phase active",
        "color": "#00d4ff",
    },
    "Rural Heart Attack": {
        "icon": "❤️",
        "label": "Rural Heart Attack",
        "subtitle": "STEMI · Oakland Hills · 45 min ambulance",
        "location": "Castro Valley Canyon Road, Oakland Hills (37.7042°N, 122.0818°W)",
        "coords": [37.7042, -122.0818],
        "symptoms": (
            "Severe crushing chest pain radiating to left arm and jaw. Diaphoresis, "
            "nausea, shortness of breath. 58M, conscious but disoriented. "
            "Onset ~20 minutes ago."
        ),
        "vitals": "BP: 180/110 mmHg | HR: 112 bpm (irregular) | O2 Sat: 91% | RR: 22/min | Temp: 37.1°C",
        "color": "#ff4444",
    },
    "Anaphylaxis": {
        "icon": "🐝",
        "label": "Severe Anaphylaxis",
        "subtitle": "Bee stings · Redwood Park · 38 min ambulance",
        "location": "Redwood Regional Park Trail Head, Oakland Hills (37.7984°N, 122.1485°W)",
        "coords": [37.7984, -122.1485],
        "symptoms": (
            "Bee stings x3 while hiking, rapidly developing urticaria, throat tightening, "
            "stridor, severe dizziness, near-syncope. 24F, known bee allergy, no EpiPen on person."
        ),
        "vitals": "BP: 82/50 mmHg | HR: 145 bpm | O2 Sat: 87% | RR: 32/min | Temp: 36.8°C",
        "color": "#ff8800",
    },
    "Traumatic Hemorrhage": {
        "icon": "🚗",
        "label": "Traumatic Hemorrhage",
        "subtitle": "Vehicle rollover · Skyline Blvd · 52 min ambulance",
        "location": "Skyline Blvd at Pinehurst Rd, Oakland Hills (37.8075°N, 122.1943°W)",
        "coords": [37.8075, -122.1943],
        "symptoms": (
            "Vehicle rollover on mountain road. Deep laceration to right femoral region, "
            "uncontrolled arterial bleeding, suspected femur fracture. "
            "32M, semi-conscious, pale, cold extremities."
        ),
        "vitals": "BP: 88/58 mmHg | HR: 134 bpm | O2 Sat: 92% | RR: 26/min | Est. blood loss: 1.5L",
        "color": "#aa44ff",
    },
}

CLINICIANS = [
    "Dr. Sarah Chen — Emergency Medicine",
    "Dr. Marcus Rivera — Cardiology",
    "Dr. Aisha Okonkwo — Trauma Surgery",
    "Dr. James Park — Critical Care",
]

PHASES = [
    "911 Call",
    "Incident Detected",
    "AI Triage",
    "Clinical Authorization",
    "Drone Deployment",
    "On-Site Arrival",
    "Payload Delivery",
]

PHASE_MAP = {
    "idle":        0,
    "calling":     0,
    "triaging":    2,
    "triage_done": 3,
    "approved":    4,
    "flying":      4,
    "landed":      5,
    "unlocking":   5,
    "complete":    6,
}


# ── SESSION STATE ──────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "stage": "idle",
        "scenario_key": None,
        "triage": None,
        "auth_code": None,
        "sim": None,
        "auto_approve": True,
        "call_transcript": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── MAP BUILDER ────────────────────────────────────────────────────────────────
def build_map(
    drone_pos=None,
    incident_coords=None,
    waypoints=None,
    step: int = 0,
    show_route: bool = True,
) -> go.Figure:
    fig = go.Figure()

    base = DRONE_BASE
    inc = incident_coords or base

    # Planned route (faint)
    if show_route and waypoints:
        lats = [w[0] for w in waypoints]
        lons = [w[1] for w in waypoints]
        fig.add_trace(go.Scattermapbox(
            lat=lats, lon=lons,
            mode="lines",
            line=dict(width=2, color="rgba(0,180,255,0.25)"),
            name="Planned Route",
            hoverinfo="skip",
        ))

    # Completed path (bright)
    if waypoints and step > 0:
        done = waypoints[: step + 1]
        fig.add_trace(go.Scattermapbox(
            lat=[w[0] for w in done],
            lon=[w[1] for w in done],
            mode="lines",
            line=dict(width=4, color="#00ff88"),
            name="Flight Path",
            hoverinfo="skip",
        ))

    # Drone base marker
    fig.add_trace(go.Scattermapbox(
        lat=[base[0]], lon=[base[1]],
        mode="markers+text",
        marker=dict(size=16, color="#4488ff"),
        text=["🏥 Medical Hub"],
        textposition="top right",
        textfont=dict(color="#aaccff", size=12),
        name="Drone Base",
    ))

    # Incident marker
    if incident_coords:
        fig.add_trace(go.Scattermapbox(
            lat=[inc[0]], lon=[inc[1]],
            mode="markers+text",
            marker=dict(size=18, color="#ff3333"),
            text=["🚨 Incident"],
            textposition="top left",
            textfont=dict(color="#ffaaaa", size=12),
            name="Incident",
        ))

    # Drone position (animated)
    if drone_pos:
        fig.add_trace(go.Scattermapbox(
            lat=[drone_pos[0]], lon=[drone_pos[1]],
            mode="markers+text",
            marker=dict(size=22, color="#ffdd00", symbol="circle"),
            text=["🚁"],
            textposition="top center",
            textfont=dict(size=18),
            name="Drone",
        ))

    # Map center and zoom
    if incident_coords:
        center_lat = (base[0] + inc[0]) / 2
        center_lon = (base[1] + inc[1]) / 2
    else:
        center_lat, center_lon = base[0], base[1]

    dist = math.sqrt((base[0] - inc[0]) ** 2 + (base[1] - inc[1]) ** 2)
    zoom = 11.5 if dist > 0.05 else 12.5

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        uirevision="stable",
    )
    return fig


# ── HELPER COMPONENTS ──────────────────────────────────────────────────────────
def render_phases(current_stage: str):
    active_idx = PHASE_MAP.get(current_stage, 0)
    html = '<div class="info-card"><div class="card-title">Mission Timeline</div>'
    for i, phase in enumerate(PHASES):
        if i < active_idx:
            dot = '<div class="phase-dot-done"></div>'
            color = "#00ff88"
        elif i == active_idx:
            dot = '<div class="phase-dot-active"></div>'
            color = "#00d4ff"
        else:
            dot = '<div class="phase-dot-pending"></div>'
            color = "#2a3555"
        html += f'<div class="phase">{dot}<span style="color:{color}">{phase}</span></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_hud_elements(alt: int = 400, spd: int = 65, heading: float = 0.0, status: str = "SCANNING"):
    """Renders the Ultra-UX HUD overlay for the vision feed."""
    return f"""
<div class="hud-overlay">
    <div class="hud-corner top-left"></div>
    <div class="hud-corner top-right"></div>
    <div class="hud-corner bottom-left"></div>
    <div class="hud-corner bottom-right"></div>
    
    <div class="tape-container spd-tape">
        <div style="font-size:0.6em;color:#8892a4">SPD</div>
        <div style="font-weight:900">{spd}</div>
        <div class="tape-tick">70</div>
        <div class="tape-tick" style="color:#00ff88">60</div>
        <div class="tape-tick">50</div>
    </div>
    
    <div class="tape-container alt-tape">
        <div style="font-size:0.6em;color:#8892a4">ALT</div>
        <div style="font-weight:900">{alt}</div>
        <div class="tape-tick">500</div>
        <div class="tape-tick" style="color:#00ff88">400</div>
        <div class="tape-tick">300</div>
    </div>
    
    <div class="crosshair">
        <div class="cross-line cross-h"></div>
        <div class="cross-line cross-v"></div>
        <div class="cross-circle"></div>
    </div>
    
    <div class="scanline"></div>
    
    <div style="position:absolute; bottom:20px; left:50%; transform:translateX(-50%); text-align:center;">
        <div style="font-size:0.7em; letter-spacing:2px; color:#00ff88; text-shadow:0 0 5px #00ff88;">{status}</div>
        <div style="font-size:0.6em; color:#8892a4; margin-top:2px;">HDG: {heading:.1f}° | LAT: 37.80N | LON: 122.19W</div>
    </div>
</div>
"""


def render_transition(message: str, duration: float = 1.5):
    """Shows a high-end transition screen with a message."""
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(
            f"""
<div class="transition-screen">
    <div class="loader-ring"></div>
    <div style="color:#00d4ff; font-weight:800; letter-spacing:3px; text-transform:uppercase; font-size:0.9em;">
        {message}
    </div>
    <div style="color:#8892a4; font-size:0.75em; margin-top:10px; font-family:monospace;">
        Establishing Secure Satellite Link...
    </div>
</div>""",
            unsafe_allow_html=True,
        )
        time.sleep(duration)
    placeholder.empty()


def render_triage_card(triage: dict):
    sev = triage.get("severity", "HIGH")
    score = triage.get("severity_score", 0)
    diag = triage.get("primary_diagnosis", "")
    proto = triage.get("protocol", "")
    notes = triage.get("clinician_notes", "")
    payload = triage.get("drone_payload", [])

    st.markdown(
        f"""
<div class="info-card">
  <div class="card-title">AI Triage Assessment — Gemini 1.5</div>
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
    <span class="badge badge-{sev}">{sev}</span>
    <span style="color:#8892a4;font-size:0.85em">Severity Score: <b style="color:#e8eaf6">{score}/10</b></span>
  </div>
  <div style="margin-bottom:6px"><span style="color:#8892a4;font-size:0.8em">DIAGNOSIS</span><br/>
    <b style="color:#e8eaf6">{diag}</b></div>
  <div style="margin-bottom:6px"><span style="color:#8892a4;font-size:0.8em">PROTOCOL</span><br/>
    <span style="color:#c8d8ff">{proto}</span></div>
  <div style="margin-bottom:6px"><span style="color:#8892a4;font-size:0.8em">DRONE PAYLOAD</span><br/>
    <span style="color:#00ff88">{" · ".join(payload)}</span></div>
  <div><span style="color:#8892a4;font-size:0.8em">CLINICIAN NOTES</span><br/>
    <span style="color:#c8d8ff;font-size:0.88em">{notes}</span></div>
</div>""",
        unsafe_allow_html=True,
    )


def render_omnicell_card(state_label: str, icon: str, color: str, auth_code: str, items: list):
    items_html = " · ".join(items)
    st.markdown(
        f"""
<div class="info-card">
  <div class="card-title">Omnicell Secure Payload Cabinet</div>
  <div class="omnicell-state" style="border-color:{color}; color:{color}">
    {icon}&nbsp;&nbsp;{state_label}
  </div>
  <div style="margin-top:10px;color:#8892a4;font-size:0.8em">AUTH CODE&nbsp;&nbsp;
    <code style="color:#ffcc00;background:#1a1e30;padding:2px 8px;border-radius:4px">{auth_code}</code>
  </div>
  <div style="margin-top:8px;color:#8892a4;font-size:0.8em">CONTENTS</div>
  <div style="color:#c8d8ff;font-size:0.85em">{items_html}</div>
</div>""",
        unsafe_allow_html=True,
    )


# ── MAIN APP ───────────────────────────────────────────────────────────────────
def main():
    init_state()
    stage = st.session_state.stage

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            '<div style="text-align:center;padding:8px 0 20px">'
            '<div style="font-size:2em">🚁</div>'
            '<div style="font-size:1.3em;font-weight:900;color:#00d4ff">SwiftMedAI</div>'
            '<div style="color:#8892a4;font-size:0.8em">Autonomous Emergency Response</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        st.divider()

        st.markdown('<div style="color:#8892a4;font-size:0.75em;font-weight:700;letter-spacing:2px">CONFIGURATION</div>', unsafe_allow_html=True)
        gemini_key = st.text_input(
            "Gemini API Key",
            value=os.getenv("GEMINI_API_KEY", ""),
            type="password",
            placeholder="AIza... (optional, uses demo mode)",
            help="Get a key at aistudio.google.com",
        )
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key

        clinician = st.selectbox("Authorizing Clinician", CLINICIANS, index=0)
        st.session_state.clinician = clinician

        auto = st.toggle("Auto-Approve (Demo Mode)", value=True)
        st.session_state.auto_approve = auto

        st.divider()
        st.markdown(
            """
<div style="color:#8892a4;font-size:0.75em;font-weight:700;letter-spacing:2px;margin-bottom:12px">MARKET POSITIONING</div>
<style>
.comp-table { width:100%; border-collapse:collapse; font-size:0.75em; color:#c8d8ff; }
.comp-table th { text-align:left; color:#8892a4; padding:4px; border-bottom:1px solid #1e2d4d; }
.comp-table td { padding:8px 4px; border-bottom:1px solid #1e2d4d; }
.check { color:#00ff88; font-weight:bold; }
.cross { color:#ff4444; opacity:0.5; }
</style>
<table class="comp-table">
  <tr><th>Feature</th><th>Zipline</th><th>SwiftMed</th></tr>
  <tr><td>Logistics</td><td class="check">✓</td><td class="check">✓</td></tr>
  <tr><td>911 Reactive</td><td class="cross">✗</td><td class="check">✓</td></tr>
  <tr><td>AI Triage</td><td class="cross">✗</td><td class="check">✓</td></tr>
  <tr><td>Live Clinic</td><td class="cross">✗</td><td class="check">✓</td></tr>
  <tr><td>SAR Vision</td><td class="cross">✗</td><td class="check">✓</td></tr>
</table>
<div style="margin-top:16px;color:#8892a4;font-size:0.7em;line-height:1.4">
  <b style="color:#00ff88">MARKET IMPACT (RURAL CA)</b><br/>
  Avg. Saved Cost: <span style="color:#e8eaf6">$12,400 / mission</span><br/>
  Response Delta: <span style="color:#00d4ff">-86% vs. Ground</span><br/>
  Clinician Approval: <span style="color:#e8eaf6">100% Mandatory</span>
</div>
<div style="margin-top:12px;color:#8892a4;font-size:0.7em;line-height:1.4">
  <b>Position:</b> Zipline is a delivery company. SwiftMedAI is a <b>Digital First Responder</b>.
</div>
""",
            unsafe_allow_html=True,
        )

        if stage != "idle":
            st.divider()
            if st.button("↺  Reset Demo", use_container_width=True):
                for key in ["stage", "scenario_key", "triage", "auth_code", "sim"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    # ── HEADER ────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="main-header">'
        '<div class="main-title">SwiftMedAI</div>'
        '<div class="main-sub">Autonomous Emergency Medical Supply · Governments · NGOs · Military Defense</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    # ── SCENARIO SELECTOR (idle only) ─────────────────────────────────────────
    if stage == "idle":
        st.markdown(
            '<div style="text-align:center;color:#8892a4;font-size:0.85em;margin-bottom:16px">'
            "Select an emergency scenario to trigger the live demo →</div>",
            unsafe_allow_html=True,
        )
        cols = st.columns(len(SCENARIOS))
        for idx, (key, sc) in enumerate(SCENARIOS.items()):
            with cols[idx]:
                label = f"{sc['icon']} {sc['label']}\n{sc['subtitle']}"
                if st.button(label, use_container_width=True, type="primary", key=f"sc_{idx}"):
                    st.session_state.scenario_key = key
                    st.session_state.stage = "calling"
                    st.rerun()

    # ── MAIN LAYOUT ───────────────────────────────────────────────────────────
    if stage == "idle":
        # Default map centered on Oakland
        fig = build_map(drone_pos=DRONE_BASE, incident_coords=None)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(
            '<div style="text-align:center;color:#2a3555;font-size:0.8em;margin-top:-10px">'
            "Oakland Medical Hub · 37.7213°N, 122.2208°W</div>",
            unsafe_allow_html=True,
        )
        return

    scenario_key = st.session_state.scenario_key
    sc = SCENARIOS[scenario_key]

    left, right = st.columns([4, 6], gap="large")

    # ── LEFT PANEL ────────────────────────────────────────────────────────────
    with left:
        # ─── 911 CALL SIMULATION ──────────────────────────────────────────────
        if stage == "calling":
            st.markdown(
                """
<div class="info-card">
  <div class="card-title">Live Communication Feed — 911 DISPATCH</div>
  <div class="waveform">
    <div class="bar"></div><div class="bar"></div><div class="bar"></div>
    <div class="bar"></div><div class="bar"></div><div class="bar"></div>
    <div class="bar"></div><div class="bar"></div><div class="bar"></div>
  </div>
  <div id="transcript-box" style="height:140px; overflow-y:auto; border-left:1px solid #1e2d4d; padding-left:12px; font-family:monospace; font-size:0.85em;">
""",
                unsafe_allow_html=True,
            )
            
            transcript_placeholder = st.empty()
            full_text = ""
            
            for speaker, phrase in stream_transcript(scenario_key):
                color = "#00d4ff" if speaker == "DISPATCHER" else "#ffcc00"
                line = f'<div style="margin-bottom:6px"><span style="color:{color};font-weight:700">{speaker}:</span> {phrase}</div>'
                full_text += line
                transcript_placeholder.markdown(full_text, unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)
            st.info("💡 AI Triage engine is analyzing the live audio stream...")
            time.sleep(2.0)
            
            render_transition("Initializing AI Triage")
            st.session_state.stage = "triaging"
            st.rerun()

        # Incident card (only show after call)
        if stage not in ("idle", "calling"):
            st.markdown(
                f"""
<div class="info-card">
  <div class="card-title">Active Incident — {sc['label']}</div>
  <div style="display:flex;gap:8px;margin-bottom:10px">
    <span style="font-size:1.8em">{sc['icon']}</span>
    <div>
      <div style="font-weight:700;color:#e8eaf6">{sc['label']}</div>
      <div style="color:#8892a4;font-size:0.82em">📍 {sc['location']}</div>
    </div>
  </div>
  <div style="color:#8892a4;font-size:0.78em;margin-bottom:4px">SYMPTOMS</div>
  <div style="color:#c8d8ff;font-size:0.87em;margin-bottom:8px">{sc['symptoms']}</div>
  <div style="color:#8892a4;font-size:0.78em;margin-bottom:4px">VITALS</div>
  <div style="color:#ffcc00;font-size:0.85em;font-family:monospace">{sc['vitals']}</div>
</div>""",
                unsafe_allow_html=True,
            )

        # Triage
        if stage == "triaging":
            img_file = None
            if scenario_key == "Search and Rescue (SAR)":
                st.markdown('<div class="card-title">Drone SAR Vision Feed</div>', unsafe_allow_html=True)
                img_file = st.file_uploader("Upload Drone Search Imagery", type=["jpg", "jpeg", "png"])
                if img_file:
                    v_label = "THERMAL SCANNER ACTIVE" if scenario_key == "Search and Rescue (SAR)" else "BIO-SENSOR LINK"
                    v_metric = "DISTRESS DETECTOR: ON" if scenario_key == "Search and Rescue (SAR)" else "VITAL STREAM: ESTABLISHED"
                    st.markdown(
                        f"""
<div class="vision-feed">
  {render_hud_elements(alt=120, status="THERMAL SCAN ACTIVE", heading=142.5)}
  <style>
    .detection-box {{
        position: absolute;
        border: 2px solid #00ff88;
        background: rgba(0, 255, 136, 0.1);
        color: #00ff88;
        font-family: monospace;
        font-size: 0.7em;
        padding: 4px 8px;
        animation: blink 0.5s infinite;
        z-index: 20;
    }}
    @keyframes blink {{ 0%, 100% {{ opacity: 1; border-color:#00ff88; }} 50% {{ opacity: 0.5; border-color:transparent; }} }}
  </style>
  <div class="detection-box" style="top:40%; left:35%; width:80px; height:120px;">
    ID: HUMAN_01<br/>CONF: 98.4%<br/>DISTRESS: HIGH
  </div>
</div>""",
                        unsafe_allow_html=True,
                    )
                    st.image(img_file, use_container_width=True)
            
            trigger_triage = True
            if scenario_key == "Search and Rescue (SAR)" and not img_file:
                trigger_triage = False
                st.warning("Please upload drone imagery to initiate SAR triage.")

            if trigger_triage:
                with st.spinner("🧠 Gemini AI Triage in progress..."):
                    pil_img = Image.open(img_file) if img_file else None
                    result = triage_incident(
                        symptoms=sc["symptoms"],
                        location=sc["location"],
                        vitals=sc["vitals"],
                        scenario_name=scenario_key,
                        api_key=os.getenv("GEMINI_API_KEY"),
                        image=pil_img,
                    )
                st.session_state.triage = result
                st.session_state.stage = "triage_done"
                st.rerun()

        if stage in ("triage_done", "approved", "flying", "landed", "unlocking", "complete"):
            triage = st.session_state.triage
            render_triage_card(triage)

        # Clinician authorization
        if stage == "triage_done":
            clinician_name = st.session_state.get("clinician", CLINICIANS[0])
            auto = st.session_state.get("auto_approve", True)

            if auto:
                st.info(f"🔄 Auto-approving as **{clinician_name}** (Demo Mode)...")
                render_transition("Authorizing Deployment")
                cabinet = PayloadCabinet()
                auth_code = cabinet.request_authorization(
                    clinician_name,
                    st.session_state.triage.get("drone_payload", []),
                )
                st.session_state.auth_code = auth_code
                st.session_state.stage = "approved"
                st.rerun()
            else:
                st.markdown(
                    f'<div style="color:#8892a4;font-size:0.85em;margin-bottom:8px">'
                    f"Clinician: <b style='color:#e8eaf6'>{clinician_name}</b></div>",
                    unsafe_allow_html=True,
                )
                if st.button("✅  AUTHORIZE DEPLOYMENT", use_container_width=True, type="secondary"):
                    cabinet = PayloadCabinet()
                    auth_code = cabinet.request_authorization(
                        clinician_name,
                        st.session_state.triage.get("drone_payload", []),
                    )
                    st.session_state.auth_code = auth_code
                    st.session_state.stage = "approved"
                    st.rerun()

        if stage in ("approved", "flying"):
            st.markdown(
                f'<div class="info-card" style="border-color:#00ff88">'
                f'<span style="color:#00ff88;font-weight:700">✅ AUTHORIZED</span>'
                f'<span style="color:#8892a4;font-size:0.85em;margin-left:12px">'
                f'{st.session_state.get("clinician", "")} · Code: '
                f'<code style="color:#ffcc00">{st.session_state.auth_code}</code></span>'
                f"</div>",
                unsafe_allow_html=True,
            )

        if stage in ("landed", "unlocking", "complete"):
            triage = st.session_state.triage
            drone_eta = triage.get("drone_eta_seconds", 270)
            mins = drone_eta // 60
            secs = drone_eta % 60
            amb_eta = triage.get("ambulance_eta_min", 45)

            col_a, col_b = st.columns(2)
            col_a.metric("🚁 Drone ETA", f"{mins}:{secs:02d}", delta="Delivered")
            col_b.metric("🚑 Ambulance ETA", f"{amb_eta} min", delta=f"Saved ~{amb_eta - mins} min", delta_color="inverse")

            # Omnicell state rendering
            if "omnicell_state" in st.session_state:
                state_info = st.session_state.omnicell_state
                render_omnicell_card(
                    state_label=state_info["label"],
                    icon=state_info["icon"],
                    color=state_info["color"],
                    auth_code=st.session_state.auth_code or "SM-DEMO1",
                    items=triage.get("drone_payload", []),
                )

        render_phases(stage)

    # ── RIGHT PANEL ───────────────────────────────────────────────────────────
    with right:
        incident_coords = sc["coords"]

        if stage == "triaging":
            fig = build_map(incident_coords=incident_coords, show_route=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(
                '<div style="text-align:center;color:#00d4ff;font-size:0.85em">'
                "📡 GPS Lock Acquired · AI Triage in progress...</div>",
                unsafe_allow_html=True,
            )

        elif stage == "triage_done":
            fig = build_map(incident_coords=incident_coords, show_route=False)
            st.plotly_chart(fig, use_container_width=True)
            triage = st.session_state.triage
            drone_eta = triage.get("drone_eta_seconds", 270)
            mins = drone_eta // 60
            secs = drone_eta % 60
            amb = triage.get("ambulance_eta_min", 45)

            c1, c2, c3 = st.columns(3)
            c1.metric("Drone ETA", f"{mins}:{secs:02d} min")
            c2.metric("Ambulance ETA", f"{amb} min")
            c3.metric("Lives at Risk", "1", delta="Critical")

        elif stage in ("approved", "flying"):
            # ─── FLIGHT ANIMATION ────────────────────────────────────────────
            m_type = "search" if scenario_key == "Search and Rescue (SAR)" else "medical"
            sim = DroneSimulator(incident_coords=incident_coords, mission_type=m_type)
            st.session_state.sim = sim

            eta_slot = st.empty()
            status_slot = st.empty()
            prog_slot = st.empty()
            map_slot = st.empty()

            for step, waypoint in enumerate(sim.waypoints):
                eta_remaining = sim.get_eta_at_step(step)
                mins = eta_remaining // 60
                secs = eta_remaining % 60
                alt = sim.get_altitude_ft(step)
                label = sim.get_status_label(step)
                progress = step / max(len(sim.waypoints) - 1, 1)

                with eta_slot.container():
                    c1, c2, c3 = st.columns(3)
                    c1.metric("ETA", f"{mins}:{secs:02d}")
                    c2.metric("Altitude", f"{alt} ft")
                    c3.metric("Speed", "65 mph")

                status_slot.markdown(
                    f'<div style="color:#00d4ff;text-align:center;font-size:0.9em;padding:4px">{label}</div>',
                    unsafe_allow_html=True,
                )
                prog_slot.progress(progress, text="")

                # Map Render
                fig = build_map(
                    drone_pos=waypoint,
                    incident_coords=incident_coords,
                    waypoints=sim.waypoints,
                    step=step,
                )
                map_slot.plotly_chart(fig, use_container_width=True)

                # HUD Render within Map Slot (overlay trick)
                hud_html = render_hud_elements(
                    alt=alt,
                    spd=65,
                    heading=sim.heading,
                    status=label.upper()
                )
                status_slot.markdown(
                    f'<div class="vision-feed" style="height:120px;margin-bottom:10px;">{hud_html}</div>',
                    unsafe_allow_html=True
                )

                time.sleep(0.08)

            # Animation complete — transition to omnicell unlock
            triage = st.session_state.triage
            auth_code = st.session_state.auth_code or "SM-DEMO1"
            items = triage.get("drone_payload", [])

            # Run omnicell unlock inline
            omnicell_slot = left.empty()
            for p_state, icon, color, delay in UNLOCK_SEQUENCE:
                st.session_state.omnicell_state = {
                    "label": p_state.value,
                    "icon": icon,
                    "color": color,
                }
                with omnicell_slot.container():
                    render_omnicell_card(p_state.value, icon, color, auth_code, items)
                if delay > 0:
                    time.sleep(delay)

            st.session_state.stage = "complete"
            st.rerun()

        elif stage in ("landed", "unlocking", "complete"):
            sim = st.session_state.sim
            if sim:
                fig = build_map(
                    drone_pos=incident_coords,
                    incident_coords=incident_coords,
                    waypoints=sim.waypoints,
                    step=len(sim.waypoints) - 1,
                )
            else:
                fig = build_map(incident_coords=incident_coords)

            st.plotly_chart(fig, use_container_width=True)

            triage = st.session_state.triage
            drone_eta = triage.get("drone_eta_seconds", 270)
            amb_eta = triage.get("ambulance_eta_min", 45)
            mins = drone_eta // 60
            secs = drone_eta % 60
            time_saved = amb_eta - mins

            st.markdown(
                f"""
<div class="info-card">
  <div class="card-title">Mission Complete — Impact Analysis</div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;text-align:center">
    <div>
      <div style="font-size:1.8em;font-weight:900;color:#00ff88">{mins}:{secs:02d}</div>
      <div style="color:#8892a4;font-size:0.8em">SwiftMedAI ETA</div>
    </div>
    <div>
      <div style="font-size:1.8em;font-weight:900;color:#ff4444">{amb_eta} min</div>
      <div style="color:#8892a4;font-size:0.8em">Ambulance ETA</div>
    </div>
    <div>
      <div style="font-size:1.8em;font-weight:900;color:#00d4ff">~{time_saved} min</div>
      <div style="color:#8892a4;font-size:0.8em">Response Saved</div>
    </div>
  </div>
  <div style="margin-top:14px;padding:10px;background:#0a1a0a;border-radius:8px;border:1px solid #00ff8844">
    <span style="color:#00ff88;font-size:0.85em">
      ⚡ For cardiac arrest, survival drops ~10% per minute without intervention.
      SwiftMedAI delivered critical supplies <b>{time_saved} minutes earlier</b> than traditional EMS.
    </span>
  </div>
</div>""",
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
