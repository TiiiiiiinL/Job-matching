---
description: Leta jobb som passar mitt CV och gör en rapport
---

Hitta jobb som passar mig och sammanfatta dem i en rapport. Följ stegen.

## 1. Läs in mig
- Läs `profil.md` (önskemål, nej tack-lista, kända företag, betygsgräns).
- Läs alla filer i `cv/` utom `README.md`. Finns inget CV: fortsätt med bara
  `profil.md`, men skriv överst i rapporten att CV saknas.

## 2. Sverige — Platsbanken
- Kör `python3 fetch_jobtech.py` (hämtar nya annonser, hoppar över redan sedda).
- Kör sedan `python3 fetch_foretag.py` (lägger till praktik-/studentroller
  direkt från kända företags jobbsidor — Greenhouse, Lever, Ashby,
  Teamtailor — med spår `företag`). De hör hemma i Sverige- eller
  Utomlands-fliken beroende på ort.
- Läs `data/lista.txt` (en rad per annons). Välj ut de som ser lovande ut
  utifrån rubrik och företag. Var **generös**: släng bara det som uppenbart
  inte passar (nej tack-listan, kräver examen/flera års erfarenhet, fel
  bransch). Hellre en 3:a för mycket än ett missat jobb.
- Läs hela annonsen för de utvalda: `python3 visa.py <id> <id> ...`
  (många id:n per anrop).

## 3. Sverige — sommarjobb/sommarpraktik hos kända företag (huvudfokus)
Platsbanken missar de flesta stora sommarprogram, så sök på webben också:
- Ericsson, Spotify, Scania, Saab, SEB, Volvo Cars, ABB, Atlas Copco, Klarna,
  King, Axis, IKEA m.fl. — "<företag> summer internship <år>" / "sommarjobb <år>"
- "sommarjobb <år> IT student Stockholm", "summer internship <år> Stockholm tech"
Hämta **officiella** sidan (WebFetch) när det går och läs av exakt
ansökningsperiod och vilka studieår som får söka.

## 4. Utomlands — kända företag
Gör webbsökningar efter internships för studenter som passar profilen, t.ex.
- "summer internship <år> UX design student Europe"
- "software engineering intern summer <år> Europe students"
- "hardware / embedded intern <år>"
- karriärsidor för företagen i `profil.md` (internship / student programs)
Ta **bara** med företag från listan i `profil.md` eller i samma klass.

## Extra arbetsgivare att kolla
Sök också efter jobb hos arbetsgivarna under "Kolla alltid" i `profil.md`
(Platsbanken + webben, även på arbetsgivarens eget språk, t.ex.
"中国驻瑞典大使馆 招聘"). Hittas något läggs det in som ett vanligt jobb i rätt
flik. Hittas inget nämns de inte alls.

## Giltighet (gäller steg 3 och 4)
- Ta bara med det som är **öppet nu** eller har ett **känt kommande
  ansökningsfönster**. Stängda ansökningar och "kanske, oklart" tas inte med.
- Kolla behörighet: kräver de att man går näst sista/sista året passar det
  inte (se studieår och examen i `profil.md`).
- Skriv alltid ansökningsperioden: "Öppen nu – stänger X", "Öppnar X – stänger Y",
  eller "Väntas öppna X (förra året: …)" om datumet bara är uppskattat.
Hoppa över id:n som redan finns i `data/seen.json`.

## 5. Betygsätt
Ge varje kandidat 1–5 på hur väl den passar **just mig** (CV + profil):
- 5 = träffar både intresse och nivå (student, ingen lång erfarenhet), gärna design + kod
- 4 = bra match på ett av spåren, realistisk att få
- 3 = okej / värt en titt: rätt typ av jobb men t.ex. utanför Stockholm,
  vill ha lite vana, eller bara delvis rätt inriktning
- ≤2 = tas inte med
Timjobb: alla bar-, serverings-, bankett- och eventjobb i Stockholmsområdet
som inte kräver flera års erfarenhet är minst en 3:a.
Sverige: passform går före företagsstorlek. Utomlands: krav på känt företag.
Ta aldrig med något från nej tack-listan.

## 6. Skriv rapporten
- Kopiera `rapporter/_mall.html` till `rapporter/<dagens datum>.html` och
  fyll i. Ändra inte `jobb.css` / `jobb.js` och lägg ingen egen stil eller
  script i rapporten.
- **Ta med förra rapportens jobb som fortfarande gäller.** Läs den senaste
  `rapporter/20*.html` före dagens. Varje jobb där ansökan inte har stängt
  (och som du inte vet har tagits bort) kopieras med, utan `data-ny`.
  Annars försvinner bra jobb bara för att de redan finns i `seen.json`.
  Nya jobb från dagens sökning får `data-ny`.
- Sätt `data-deadline="ÅÅÅÅ-MM-DD"` på varje jobb där sista ansökningsdag
  är känd (för "Öppnar snart": dagen ansökan stänger, om den är känd). Fyra flikar: **Sverige** (sommarjobb, praktik, studentjobb — störst
  fokus), **Timjobb**, **Utomlands**, **Obetalt** (alla obetalda roller,
  oavsett land — de ska aldrig ligga i de andra flikarna).
- Inom Sverige och Utomlands: rubrikerna "Sök nu" och "Öppnar snart".
  Sortera på deadline (närmast först) och sedan betyg.
- 3:or läggs sist i varje flik under rubriken "Fler att kolla", med en
  kortare motivering (en mening räcker).
- Per jobb: titel, företag, ort, ansökningsperiod (`data-status` = öppen /
  snart / stänger om < 7 dagar), betyg, 1–2 meningar om *varför det passar
  mig*, länk.
- Längst upp: datum, antal genomgångna annonser, antal som kom med (varav nya).

## 7. Kom ihåg vad jag sett
Lägg till **alla** genomgångna id:n (även de som inte kom med) i
`data/seen.json` som `{"<id>": "<datum>"}`. För webbresultat, använd
`web:<företag>:<rollnamn>` som id.

## 8. Avsluta
Skriv i chatten: sökvägen till rapporten och topp 3 i en mening var.
