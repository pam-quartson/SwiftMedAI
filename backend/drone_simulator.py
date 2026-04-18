import math
from dataclasses import dataclass, field
from typing import List, Tuple

DRONE_BASE = [37.7213, -122.2208]  # Oakland Int'l Airport Medical Hub
DRONE_SPEED_MPH = 65
CRUISE_ALTITUDE_FT = 400
ANIMATION_STEPS = 60


def haversine_miles(p1: List[float], p2: List[float]) -> float:
    R = 3958.8
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def calc_heading(p1: List[float], p2: List[float]) -> float:
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


@dataclass
class DroneSimulator:
    incident_coords: List[float]
    base_coords: List[float] = field(default_factory=lambda: list(DRONE_BASE))

    def __post_init__(self):
        self.distance_miles = haversine_miles(self.base_coords, self.incident_coords)
        self.total_eta_seconds = int((self.distance_miles / DRONE_SPEED_MPH) * 3600)
        self.heading = calc_heading(self.base_coords, self.incident_coords)
        self.waypoints = self._compute_waypoints()

    def _compute_waypoints(self) -> List[Tuple[float, float]]:
        waypoints = []
        for i in range(ANIMATION_STEPS + 1):
            t = i / ANIMATION_STEPS
            # Slight lateral arc for visual realism
            arc = math.sin(t * math.pi) * 0.004
            lat = self.base_coords[0] + (self.incident_coords[0] - self.base_coords[0]) * t
            lon = self.base_coords[1] + (self.incident_coords[1] - self.base_coords[1]) * t + arc
            waypoints.append((lat, lon))
        return waypoints

    def get_eta_at_step(self, step: int) -> int:
        progress = step / max(len(self.waypoints) - 1, 1)
        return max(0, int(self.total_eta_seconds * (1 - progress)))

    def get_status_label(self, step: int) -> str:
        progress = step / max(len(self.waypoints) - 1, 1)
        if progress < 0.05:
            return "🚁  Launching from Oakland base..."
        elif progress < 0.25:
            return "📡  En route — cruising at 400 ft"
        elif progress < 0.55:
            return "🧭  Navigating — route optimized by AI"
        elif progress < 0.80:
            return "📍  Approaching incident site"
        elif progress < 0.97:
            return "⬇️  Initiating landing sequence"
        else:
            return "✅  DRONE LANDED — Payload ready for unlock"

    def get_altitude_ft(self, step: int) -> int:
        progress = step / max(len(self.waypoints) - 1, 1)
        if progress < 0.12:
            return int(CRUISE_ALTITUDE_FT * (progress / 0.12))
        elif progress > 0.88:
            return int(CRUISE_ALTITUDE_FT * ((1 - progress) / 0.12))
        return CRUISE_ALTITUDE_FT
