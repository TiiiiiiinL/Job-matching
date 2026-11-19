// Gemensamt beteende för alla rapporter. Ändras här → gäller alla rapporter.
// Fungerar även när filen öppnas direkt, men knappen "Uppdatera nu" och
// listan med äldre rapporter kräver att server.py körs.

const lagra = {
  läs(nyckel, standard) { try { return JSON.parse(localStorage.getItem(nyckel)) ?? standard; } catch (e) { return standard; } },
  skriv(nyckel, värde) { try { localStorage.setItem(nyckel, JSON.stringify(värde)); } catch (e) {} },
};
const viaServer = location.protocol.startsWith('http');

// ---------- Deadline: "X dagar kvar", färg, och utgångna jobb ----------
// Jobb med data-deadline="ÅÅÅÅ-MM-DD" räknas om varje gång sidan öppnas,
// så en gammal rapport visar ändå rätt antal dagar.
const idag = new Date(); idag.setHours(0, 0, 0, 0);
document.querySelectorAll('.jobb[data-deadline]').forEach(j => {
  const slut = new Date(j.dataset.deadline + 'T00:00:00');
  if (isNaN(slut)) return;
  const dagar = Math.round((slut - idag) / 864e5);
  const rad = j.querySelector('.ansokan');
  if (dagar < 0) {
    j.classList.add('utgången');
    j.dataset.status = 'ingen';
    if (rad) rad.textContent = 'Ansökan har stängt';
    return;
  }
  if (j.dataset.status !== 'snart' && dagar <= 7) j.dataset.status = 'stänger';
  if (rad) rad.append(dagar === 0 ? ' · sista dagen idag!' : ` · ${dagar} dag${dagar === 1 ? '' : 'ar'} kvar`);
});

// ---------- "Ny"-märke ----------
document.querySelectorAll('.jobb[data-ny]').forEach(j => {
  const m = document.createElement('span');
  m.className = 'ny'; m.textContent = 'Ny';
  j.querySelector('h3')?.prepend(m);
});

// ---------- Sökt / Dölj (sparas i webbläsaren, följer med mellan rapporter) ----------
const märken = lagra.läs('jobbmärken', {});   // { länk: 'sökt' | 'dold' }
let visaDolda = false;
const nyckel = j => j.querySelector('a[href]')?.getAttribute('href') || j.querySelector('h3')?.textContent;

function ritaMärke(j) {
  const m = märken[nyckel(j)];
  j.classList.toggle('sökt', m === 'sökt');
  j.classList.toggle('dold', m === 'dold');
  j.hidden = (m === 'dold' && !visaDolda) || j.classList.contains('utgången') && !visaDolda;
  const s = j.querySelector('.sökt-knapp');
  if (s) s.textContent = m === 'sökt' ? '✓ Sökt' : 'Markera som sökt';
  const d = j.querySelector('.dölj-knapp');
  if (d) d.textContent = m === 'dold' ? 'Visa igen' : 'Dölj';
}

function märk(j, vad) {
  const k = nyckel(j);
  if (märken[k] === vad) delete märken[k]; else märken[k] = vad;
  lagra.skriv('jobbmärken', märken);
  ritaMärke(j); räkna();
}

document.querySelectorAll('.jobb').forEach(j => {
  const fot = document.createElement('div'); fot.className = 'fot';
  const länk = j.querySelector(':scope > a');
  if (länk) fot.append(länk);
  const knappar = document.createElement('div'); knappar.className = 'knappar';
  const sökt = document.createElement('button'); sökt.className = 'sökt-knapp';
  const dölj = document.createElement('button'); dölj.className = 'dölj-knapp';
  sökt.onclick = () => märk(j, 'sökt');
  dölj.onclick = () => märk(j, 'dold');
  knappar.append(sökt, dölj); fot.append(knappar); j.append(fot);
  ritaMärke(j);
});

// ---------- Flikar ----------
const flikknappar = document.querySelectorAll('.flikar button');
function visa(id) {
  flikknappar.forEach(b => b.setAttribute('aria-selected', b.dataset.flik === id));
  document.querySelectorAll('.flik').forEach(s => s.hidden = s.id !== id);
  lagra.skriv('jobbflik', id);
}
function räkna() {
  flikknappar.forEach(b => {
    b.querySelector('.antal').textContent =
      document.querySelectorAll(`#${b.dataset.flik} .jobb:not([data-status="ingen"]):not(.dold)`).length;
  });
  const n = document.querySelectorAll('.jobb.dold, .jobb.utgången').length;
  const v = document.getElementById('visa-dolda-text');
  if (v) v.textContent = `Visa dolda och stängda (${n})`;
}
flikknappar.forEach(b => b.addEventListener('click', () => visa(b.dataset.flik)));
const sparad = lagra.läs('jobbflik', null);
if (sparad && document.getElementById(sparad)) visa(sparad);

document.getElementById('visa-dolda')?.addEventListener('change', e => {
  visaDolda = e.target.checked;
  document.querySelectorAll('.jobb').forEach(ritaMärke);
});
räkna();

// ---------- Uppdatera nu ----------
const knapp = document.getElementById('uppdatera');
const status = document.getElementById('status');
const arkiv = document.getElementById('arkiv');

function minuter(sek) { const m = Math.round(sek / 60); return m < 1 ? 'nyss' : `${m} min`; }

async function hämtaStatus() {
  const r = await fetch('/status', { cache: 'no-store' });
  return r.json();
}

let pågår = false;
async function följ() {
  try {
    const s = await hämtaStatus();
    status.classList.toggle('fel', s.ok === false);
    if (s.kör) {
      pågår = true;
      knapp.disabled = true;
      knapp.textContent = 'Söker…';
      status.textContent = `${s.nu} (${minuter(Date.now() / 1000 - s.start)}, steg ${s.steg})`;
      setTimeout(följ, 3000);
      return;
    }
    knapp.disabled = false;
    knapp.textContent = 'Uppdatera nu';
    if (pågår && s.ok) {        // nyss klar → visa nya rapporten
      status.textContent = 'Klar! Laddar nya rapporten…';
      location.href = '/' + s.rapport;
      return;
    }
    if (s.ok === false) status.textContent = 'Senaste sökningen misslyckades: ' + s.nu;
    else if (s.slut) status.textContent = `Senast uppdaterad för ${minuter(Date.now() / 1000 - s.slut)} sedan`;
    pågår = false;
  } catch (e) {
    knapp.disabled = false;
    status.textContent = 'Tappade kontakten med servern — körs server.py?';
  }
}

if (knapp) {
  if (!viaServer) {
    // Öppnad som fil → knappen tar dig till serverversionen av sidan
    status.textContent = 'Du har öppnat filen direkt. Klicka för att gå till http://localhost:8765, där knappen fungerar.';
    knapp.addEventListener('click', () => location.href = 'http://localhost:8765/');
  } else {
    knapp.addEventListener('click', async () => {
      knapp.disabled = true;
      status.classList.remove('fel');
      status.textContent = 'Startar… (en hel sökning tar ofta 10–20 min, du kan stänga fliken under tiden)';
      const r = await fetch('/uppdatera', { method: 'POST', headers: { 'X-Jobbsok': '1' } });
      if (!r.ok) status.textContent = (await r.json()).fel || 'Kunde inte starta';
      pågår = true;
      setTimeout(följ, 1500);
    });
    följ();
  }
}

// ---------- Äldre rapporter ----------
if (arkiv) {
  if (!viaServer) arkiv.hidden = true;
  else fetch('/rapporter').then(r => r.json()).then(filer => {
    const här = location.pathname.split('/').pop();
    for (const f of filer) {
      const o = new Option(f.replace('.html', '') + (f === filer[0] ? ' (senaste)' : ''), f);
      o.selected = f === här;
      arkiv.add(o);
    }
    arkiv.onchange = () => location.href = '/' + arkiv.value;
  }).catch(() => arkiv.hidden = true);
}
