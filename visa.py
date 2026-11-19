"""
visa.py — skriver ut hela annonsen för ett eller flera id:n ur data/raw.json

Kör:  python3 visa.py jobtech:31685055 jobtech:31690001
"""

import json
import sys
from pathlib import Path

RAW = Path(__file__).parent / "data" / "raw.json"

jobs = {j["id"]: j for j in json.loads(RAW.read_text())}
for i in sys.argv[1:]:
    j = jobs.get(i)
    if not j:
        print(f"## {i}: hittades inte\n")
        continue
    print(f"## {j['titel']} — {j['företag']} ({j['ort']})")
    print(f"id: {i} | deadline: {j['deadline']} | {j['omfattning']} | erfarenhet krävs: {j['erfarenhet_krävs']}")
    print(f"länk: {j['länk']}\n{j['beskrivning']}\n")
