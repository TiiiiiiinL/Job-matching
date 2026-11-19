"""
fetch_jobtech.py — hämtar svenska jobbannonser från Arbetsförmedlingen
----------------------------------------------------------------------------
Använder JobTechs öppna JobSearch-API (samma annonser som Platsbanken).
Gratis, ingen nyckel. Bara standardbiblioteket — inget att installera.

Kör:  python3 fetch_jobtech.py          (bara annonser du inte sett)
      python3 fetch_jobtech.py --alla   (även redan sedda, för att bedöma om)
Ut:   data/raw.json  — en lista med förfiltrerade annonser som /jobb sedan
                       betygsätter mot ditt CV.

Skriptet är medvetet "dumt": det samlar brett och slänger bara det som
uppenbart inte passar (kassa, lager, telefonsälj...). Själva bedömningen
av om ett jobb passar *dig* görs av Claude i /jobb.
"""

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://jobsearch.api.jobtechdev.se/search"
ROOT = Path(__file__).parent
OUT = ROOT / "data" / "raw.json"
LISTA = ROOT / "data" / "lista.txt"
SEEN = ROOT / "data" / "seen.json"

# Sökord delade i två spår. Lägg till/ta bort fritt.
QUERIES = {
    "internship": [
        "praktik student", "internship", "sommarpraktik", "sommarjobb student",
        "trainee", "UX designer", "UI designer", "produktdesign", "frontend",
        "mjukvaruutvecklare student", "embedded student", "hårdvara student",
        "examensarbete", "student datateknik", "deltid student utvecklare",
        # Bredare studentroller — inte bara stora bolag
        "praktikant", "studentmedarbetare", "amanuens", "IT-student",
        "extrajobb student IT", "studentjobb utvecklare", "marketing intern",
        "praktik grafisk design", "instruktör programmering", "student developer",
        # Fler student- och extrajobb
        "sommarjobb 2027", "studentjobb", "extrajobb student", "deltid student",
        "läxhjälp", "mattecoach", "studentambassadör", "IT-support student",
        "testare", "webbutvecklare deltid", "grafisk designer deltid",
        "UX praktik", "social media student", "content creator", "foto video student",
    ],
    "timjobb": [
        "bartender", "servitör", "servitris", "restaurang extra",
        "fotomodell", "modell extra", "event personal",
        # Fler timjobb inom bar, servering, event och nöje
        "hovmästare", "runner restaurang", "barback", "cocktailbar", "nattklubb",
        "bankett", "festvåning", "extrapersonal servering", "konferens servering",
        "hotell extra", "eventvärd", "eventpersonal", "garderob", "arena event",
        "mässa personal", "statist", "helgjobb", "behovsanställning", "timanställning",
    ],
}

# Rubriker/arbetsgivare som innehåller något av detta slängs direkt.
NEJ_TACK = re.compile(
    r"kassa|kassör|butikssälj|butiksbiträde|lager|truck|telefonsälj|"
    r"telemarketing|dörrknack|städ|diskare|kökbiträde|kockbiträde|"
    r"provision|säljare|kundtjänst|callcenter|budbil|chaufför|"
    r"ica |coop|willys|hemköp|lidl|mcdonald|max hamburgare|burger king|"
    r"cleaner|snickare|veterinär|phd|doktorand|postdoc|sjuksköterska|"
    r"undersköterska|lärare|förskol|elevassistent|personlig assistent|"
    r"barnvakt|hemtjänst|vårdbiträde|ekonomiassistent|rekrytering",
    re.IGNORECASE,
)

PER_QUERY = 100  # max annonser per sökord (API:ts tak)


def search(q: str) -> list[dict]:
    params = urllib.parse.urlencode({"q": q, "limit": PER_QUERY})
    req = urllib.request.Request(f"{API}?{params}", headers={"accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["hits"]


def simplify(hit: dict, track: str) -> dict:
    """Plockar ut det som behövs för bedömning — hela annonsen är onödigt stor."""
    addr = hit.get("workplace_address") or {}
    desc = (hit.get("description") or {}).get("text") or ""
    return {
        "id": f"jobtech:{hit['id']}",
        "spår": track,
        "titel": hit.get("headline"),
        "företag": (hit.get("employer") or {}).get("name"),
        "ort": addr.get("municipality") or addr.get("city") or addr.get("country"),
        "deadline": (hit.get("application_deadline") or "")[:10],
        "omfattning": (hit.get("working_hours_type") or {}).get("label"),
        "erfarenhet_krävs": hit.get("experience_required"),
        "länk": hit.get("webpage_url"),
        "beskrivning": desc[:1500],  # räcker för att bedöma, sparar plats
    }


def main() -> None:
    seen = json.loads(SEEN.read_text()) if SEEN.exists() and "--alla" not in sys.argv else {}
    jobs: dict[str, dict] = {}
    dups: set[tuple] = set()
    for track, queries in QUERIES.items():
        for q in queries:
            try:
                hits = search(q)
            except Exception as e:  # ett trasigt sökord ska inte stoppa resten
                print(f"  ! {q}: {e}")
                continue
            for h in hits:
                job = simplify(h, track)
                text = f"{job['titel']} {job['företag']}"
                # Samma rubrik hos samma företag i flera städer = en annons
                dup = (job["titel"], job["företag"])
                if job["id"] in seen or dup in dups or NEJ_TACK.search(text):
                    continue
                dups.add(dup)
                jobs[job["id"]] = job
            print(f"  {track:10} {q:30} {len(hits):3} träffar")

    OUT.write_text(json.dumps(list(jobs.values()), ensure_ascii=False, indent=1))
    # Kompakt översikt, en rad per annons — /jobb sållar på den först och
    # läser bara hela beskrivningen för de som ser lovande ut.
    LISTA.write_text("\n".join(
        f"{j['id']} | {j['spår']} | {j['titel']} | {j['företag']} | {j['ort']} | {j['deadline']}"
        for j in jobs.values()
    ))
    print(f"\n{len(jobs)} nya kandidater → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
