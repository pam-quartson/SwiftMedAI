import random
import string
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PayloadState(Enum):
    LOCKED = "LOCKED"
    AUTH_REQUESTED = "AUTHORIZATION REQUESTED"
    VERIFYING = "VERIFYING CREDENTIALS"
    UNLOCKING = "MECHANICAL UNLOCK IN PROGRESS"
    UNLOCKED = "UNLOCKED — PAYLOAD ACCESSIBLE"


UNLOCK_SEQUENCE = [
    (PayloadState.LOCKED,         "🔒", "#ff4444", 0.0),
    (PayloadState.AUTH_REQUESTED, "📡", "#ff8800", 0.9),
    (PayloadState.VERIFYING,      "🔐", "#ffcc00", 0.9),
    (PayloadState.UNLOCKING,      "⚙️", "#00aaff", 1.2),
    (PayloadState.UNLOCKED,       "✅", "#00ff88", 0.0),
]


@dataclass
class PayloadCabinet:
    items: List[str] = field(default_factory=list)
    state: PayloadState = PayloadState.LOCKED
    auth_code: str = ""
    clinician_id: str = ""
    unlock_timestamp: Optional[float] = None

    def request_authorization(self, clinician_id: str, items: List[str]) -> str:
        self.clinician_id = clinician_id
        self.items = items
        self.state = PayloadState.AUTH_REQUESTED
        chars = string.ascii_uppercase + string.digits
        self.auth_code = "SM-" + "".join(random.choices(chars, k=6))
        return self.auth_code

    def is_unlocked(self) -> bool:
        return self.state == PayloadState.UNLOCKED
