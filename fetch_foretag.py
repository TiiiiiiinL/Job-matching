"""
fetch_foretag.py — hämtar praktik-/studentjobb direkt från kända företags jobbsidor
-----------------------------------------------------------------------------------
Många företag lägger sina jobb i ett rekryteringssystem med öppet API:
Greenhouse, Lever, Ashby eller Teamtailor. De annonserna syns ofta inte
på Platsbanken, så de hämtas här direkt. Gratis, ingen nyckel.

Kör efter fetch_jobtech.py (den skriver om raw.json från början):
      python3 fetch_foretag.py
Ut:   lägger till annonser i data/raw.json + data/lista.txt (spår "företag").

Bara rubriker som ser ut som praktik/student/sommar behålls. Resten
(ort, nivå, passform) bedöms av Claude i /jobb.
"""

import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "data" / "raw.json"
LISTA = ROOT / "data" / "lista.txt"
SEEN = ROOT / "data" / "seen.json"

# Företag per system. Namnet är det som står i företagets jobb-URL.
# Lägg till fler: testa t.ex. https://boards-api.greenhouse.io/v1/boards/<namn>/jobs
FORETAG = {
    "greenhouse": ["stripe", "figma", "anthropic", "databricks", "airbnb",
                   "cloudflare", "discord", "monzo", "wise", "mongodb",
                   "datadog", "duolingo", "dropbox", "pinterest", "reddit",
                   "asana", "vercel", "epicgames", "truecaller"],
    "lever": ["spotify", "palantir"],
    "ashby": ["notion", "linear", "openai", "elevenlabs", "perplexity",
              "cursor", "supabase", "lovable", "legora"],
    # Teamtailor: värdnamnet till karriärsidan (svenska bolag använder det mycket)
    "teamtailor": ["jobs.storytel.com", "career.qliro.com", "careers.voi.com",
                   "career.paradoxplaza.com", "jobs.tibber.com", "career.hemnet.se"],
}

# Rubriken måste träffa detta...
STUDENT = re.compile(
    r"\b(intern|interns|internship|summer|sommar\w*|student\w*|trainee|"
    r"praktik\w*|working student|werkstudent|apprentice\w*|early career)\b",
    re.IGNORECASE,
)
# ...men inte detta (för hög nivå eller fel spår)
NEJ = re.compile(r"\b(phd|ph\.d|doctoral|postdoc|mba|thesis|examensarbete|"
                 r"senior|manager|lead|director|internal|high school|master'?s)\b",
                 re.IGNORECASE)
# Orter utanför Europa slängs: där krävs nästan alltid lokalt arbetstillstånd.
# Står det även en europeisk ort (t.ex. "London; New York") behålls annonsen.
UTANFOR = re.compile(
    r"united states|\busa?\b|, (ca|ny|wa|tx|ma|co|pa|nc|il|ga|or)\b|california|"
    r"new york|san francisco|seattle|boston|austin|denver|chicago|pittsburgh|"
    r"mountain view|bellevue|palo alto|cary|honolulu|d\.c\.|canada|toronto|vancouver|montreal|"
    r"india|bengaluru|bangalore|singapore|japan|tokyo|australia|sydney|"
    r"brazil|são paulo|mexico|korea|china|hong kong",
    re.IGNORECASE,
)
EUROPA = re.compile(
    r"sweden|sverige|stockholm|göteborg|malmö|london|united kingdom|\buk\b|"
    r"dublin|ireland|paris|france|berlin|munich|germany|amsterdam|netherlands|"
    r"zurich|switzerland|madrid|barcelona|spain|milan|italy|copenhagen|aarhus|"
    r"denmark|oslo|norway|helsinki|finland|warsaw|poland|bucharest|belgrade|"
    r"lisbon|vienna|prague|delft|novi sad|zurich|europe|emea",
    re.IGNORECASE,
)


def hamta(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "jobbsok"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def text(s: str) -> str:
    """HTML → ren text, kort nog för att bedöma."""
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    return re.sub(r"\s+", " ", html.unescape(s)).strip()[:1500]


def passar(titel: str) -> bool:
    return bool(STUDENT.search(titel)) and not NEJ.search(titel)


def i_europa(ort) -> bool:
    """Okänd ort behålls — Claude får bedöma."""
    return not ort or not UTANFOR.search(ort) or bool(EUROPA.search(ort))


def jobb(system, foretag, jid, titel, ort, lank, beskr) -> dict:
    return {
        "id": f"{system}:{foretag}:{jid}",
        "spår": "företag",
        "titel": titel,
        "företag": foretag,
        "ort": ort,
        "deadline": "",
        "omfattning": None,
        "erfarenhet_krävs": None,
        "länk": lank,
        "beskrivning": beskr,
    }


def greenhouse(namn):
    data = json.loads(hamta(f"https://boards-api.greenhouse.io/v1/boards/{namn}/jobs"))
    for j in data["jobs"]:
        if passar(j["title"]):
            # Listan saknar beskrivning — hämta den bara för de som passar
            d = json.loads(hamta(f"https://boards-api.greenhouse.io/v1/boards/{namn}/jobs/{j['id']}"))
            yield jobb("greenhouse", namn, j["id"], j["title"],
                       (j.get("location") or {}).get("name"), j["absolute_url"],
                       text(d.get("content")))


def lever(namn):
    for j in json.loads(hamta(f"https://api.lever.co/v0/postings/{namn}?mode=json")):
        if passar(j["text"]):
            yield jobb("lever", namn, j["id"], j["text"],
                       (j.get("categories") or {}).get("location"), j["hostedUrl"],
                       (j.get("descriptionPlain") or "")[:1500])


def ashby(namn):
    for j in json.loads(hamta(f"https://api.ashbyhq.com/posting-api/job-board/{namn}"))["jobs"]:
        if passar(j["title"]):
            yield jobb("ashby", namn, j["id"], j["title"], j.get("location"),
                       j["jobUrl"], (j.get("descriptionPlain") or "")[:1500])


def teamtailor(host):
    namn = host.split(".")[1]  # jobs.storytel.com → storytel
    for item in ET.fromstring(hamta(f"https://{host}/jobs.rss")).iter("item"):
        titel = item.findtext("title") or ""
        if passar(titel):
            lank = item.findtext("link") or ""
            # Orter ligger i Teamtailors egna taggar, t.ex. <tt:city>
            orter = {e.text for e in item.iter() if e.tag.endswith("city") and e.text}
            yield jobb("teamtailor", namn, lank.rstrip("/").split("/")[-1], titel,
                       ", ".join(sorted(orter)) or None, lank,
                       text(item.findtext("description")))


def main() -> None:
    seen = json.loads(SEEN.read_text()) if SEEN.exists() else {}
    befintliga = json.loads(OUT.read_text()) if OUT.exists() else []
    ids = {j["id"] for j in befintliga}
    nya = []
    for system, lista in FORETAG.items():
        hamtare = globals()[system]
        for namn in lista:
            try:
                traffar = [j for j in hamtare(namn) if i_europa(j["ort"])
                           and j["id"] not in seen and j["id"] not in ids]
            except Exception as e:  # ett trasigt företag ska inte stoppa resten
                print(f"  ! {system} {namn}: {e}")
                continue
            ids.update(j["id"] for j in traffar)
            nya += traffar
            print(f"  {system:10} {namn:28} {len(traffar):3} nya")

    OUT.write_text(json.dumps(befintliga + nya, ensure_ascii=False, indent=1))
    with LISTA.open("a") as f:
        for j in nya:
            f.write(f"\n{j['id']} | {j['spår']} | {j['titel']} | {j['företag']} | {j['ort']} | {j['deadline']}")
    print(f"\n{len(nya)} nya från företagens jobbsidor → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
