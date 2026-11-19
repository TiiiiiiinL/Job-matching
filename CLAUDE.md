# jobbsok

Letar jobb (främst internships, även studentjobb och timjobb) som passar
användarens CV och sammanfattar dem i en HTML-rapport.

- Kör med `/jobb` (`.claude/commands/jobb.md` beskriver hela flödet).
- `profil.md` = önskemål, nej tack-lista, kända företag. Ändras av användaren.
  Personlig — committas inte. `profil.exempel.md` är en mall att kopiera.
- `cv/` = användarens CV. Personligt — committas aldrig (se `.gitignore`).
- `fetch_jobtech.py` hämtar från Arbetsförmedlingens JobTech-API → `data/raw.json` + `data/lista.txt`.
- `fetch_foretag.py` lägger till praktik från kända företags jobbsidor (Greenhouse/Lever/Ashby/Teamtailor) i samma filer.
- `visa.py <id>...` visar hela annonser ur `raw.json`.
- `data/seen.json` = redan genomgångna annonser, så bara nya visas.
- Rapporter i `rapporter/<datum>.html`, utifrån `rapporter/_mall.html`. Stil/beteende delas i `rapporter/jobb.css` + `jobb.js`.
- `server.py` visar rapporterna på http://localhost:8765; knappen "Uppdatera nu" kör `claude -p /jobb` i bakgrunden.

Kodkommentarer på svenska. Bara Pythons standardbibliotek.
