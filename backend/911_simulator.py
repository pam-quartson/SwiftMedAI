"""
911 Simulator — Provides mock emergency call transcripts for the SwiftMedAI demo.
"""
import time
from typing import Generator, List, Tuple

SCENARIO_TRANSCRIPTS = {
    "Search and Rescue (SAR)": [
        ("DISPATCHER", "911, what is the location of your emergency?"),
        ("CALLER", "We're in Redwood Regional Park... the West Ridge Trail."),
        ("DISPATCHER", "Okay, stay calm. What's happening?"),
        ("CALLER", "My son... he's gone. He went ahead on his bike 4 hours ago and hasn't come back."),
        ("DISPATCHER", "Is he alone? What is he wearing?"),
        ("CALLER", "Yes, alone. Blue helmet, orange shirt. Please, it's getting dark."),
        ("DISPATCHER", "I'm dispatching a SwiftSAR drone to your coordinates now. Stay on the line."),
    ],
    "Rural Heart Attack": [
        ("DISPATCHER", "911, what is the location of your emergency?"),
        ("CALLER", "Castro Valley... Canyon Road. My husband... he just collapsed."),
        ("DISPATCHER", "Is he breathing? Is he conscious?"),
        ("CALLER", "He's pale and sweaty... clutching his chest. He can barely talk."),
        ("DISPATCHER", "Okay. Do you have an AED or Aspirin nearby?"),
        ("CALLER", "No, nothing! We're miles from the hospital!"),
        ("DISPATCHER", "Stay calm. A SwiftMed drone is being authorized for immediate AED delivery."),
    ],
    "Severe Anaphylaxis": [
        ("DISPATCHER", "911, what is the location of your emergency?"),
        ("CALLER", "Redwood Trail Head. My friend... she was stung by a bee!"),
        ("DISPATCHER", "Is she allergic? Does she have an EpiPen?"),
        ("CALLER", "Yes, she's highly allergic! We don't have her pen! Her throat is closing up!"),
        ("DISPATCHER", "Help is on the way. I'm dispatching a medical drone with epinephrine now."),
    ],
    "Traumatic Hemorrhage": [
        ("DISPATCHER", "911, what is the location of your emergency?"),
        ("CALLER", "Skyline Boulevard. There's been a rollover! A car is off the road!"),
        ("DISPATCHER", "Are there injuries?"),
        ("CALLER", "Yes! The driver... his leg is bleeding really bad! It's pulsing!"),
        ("DISPATCHER", "Okay, I'm dispatching a trauma-response drone with a CAT tourniquet immediately."),
    ]
}

def stream_transcript(scenario_key: str) -> Generator[Tuple[str, str], None, None]:
    """Yields (speaker, phrase) for the given scenario."""
    if scenario_key not in SCENARIO_TRANSCRIPTS:
        return
    
    for speaker, phrase in SCENARIO_TRANSCRIPTS[scenario_key]:
        yield speaker, phrase
        # Simulate thinking/breathing time between exchanges
        time.sleep(1.2)
