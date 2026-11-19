"""
server.py — visar rapporterna i webbläsaren och låter knappen "Uppdatera nu"
köra hela /jobb-sökningen utan att du behöver öppna Claude själv.

Kan starta av sig själv när du loggar in i Windows: lägg en kopia av
autostart_windows.vbs i Windows Autostart-mapp (Win+R → shell:startup).
Manuellt: python3 server.py
Öppna: http://localhost:8765   (visar alltid senaste rapporten)

Knappen startar `claude -p /jobb` i bakgrunden (samma flöde som när du
skriver /jobb). Sidan visar vad Claude gör just nu och laddar om sig själv
med den nya rapporten när det är klart. Loggen hamnar i data/uppdatering.log.

Servern lyssnar bara på din egen dator (127.0.0.1).
"""

import json
import shutil
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
RAPPORTER = ROOT / "rapporter"
LOGG = ROOT / "data" / "uppdatering.log"
PORT = 8765

# Det headless-Claude får göra — inget mer. Allt annat nekas automatiskt.
TILLÅTET = [
    "Read", "Write", "Edit", "Glob", "Grep", "WebSearch", "WebFetch",
    "Bash(python3 fetch_jobtech.py)", "Bash(python3 fetch_foretag.py)",
    "Bash(python3 visa.py:*)",
]
# Vid autostart från Windows saknas ibland ~/.local/bin i PATH
CLAUDE = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")
KOMMANDO = [CLAUDE, "-p", "/jobb", "--output-format", "stream-json", "--verbose",
            "--permission-mode", "acceptEdits", "--allowedTools", *TILLÅTET]

# Delat läge mellan körningen och /status
läge = {"kör": False, "start": None, "slut": None, "ok": None, "nu": "", "steg": 0}
lås = threading.Lock()


def beskriv(verktyg: dict) -> str:
    """Gör om ett verktygsanrop till en kort statusrad på svenska."""
    namn, inp = verktyg.get("name"), verktyg.get("input") or {}
    if namn == "WebSearch":
        return f"Söker på webben: {inp.get('query', '')}"
    if namn == "WebFetch":
        return f"Läser {inp.get('url', '')}"
    if namn == "Bash":
        cmd = inp.get("command", "")
        if "fetch_jobtech" in cmd:
            return "Hämtar annonser från Platsbanken"
        if "fetch_foretag" in cmd:
            return "Hämtar från företagens jobbsidor"
        if "visa.py" in cmd:
            return "Läser hela annonser"
        return cmd[:80]
    if namn in ("Write", "Edit"):
        fil = Path(inp.get("file_path", "")).name
        return "Skriver rapporten" if fil.endswith(".html") else f"Uppdaterar {fil}"
    if namn == "Read":
        return f"Läser {Path(inp.get('file_path', '')).name}"
    return namn or ""


def kör_sökning() -> None:
    with LOGG.open("w") as logg:
        try:
            proc = subprocess.Popen(KOMMANDO, cwd=ROOT, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
        except FileNotFoundError:
            with lås:
                läge.update(kör=False, ok=False, slut=time.time(),
                            nu="Hittar inte programmet 'claude' — är Claude Code installerat?")
            return
        ok = None
        for rad in proc.stdout:
            logg.write(rad)
            logg.flush()
            try:
                h = json.loads(rad)
            except ValueError:
                continue
            if h.get("type") == "assistant":
                for del_ in h["message"].get("content", []):
                    if del_.get("type") == "tool_use":
                        with lås:
                            läge["nu"] = beskriv(del_)
                            läge["steg"] += 1
            elif h.get("type") == "result":
                ok = not h.get("is_error")
                if not ok:
                    with lås:
                        läge["nu"] = str(h.get("result") or h.get("subtype"))[:200]
        proc.wait()
        with lås:
            läge.update(kör=False, slut=time.time(), ok=bool(ok and proc.returncode == 0))
            if läge["ok"]:
                läge["nu"] = "Klar!"
            elif not läge["nu"]:
                läge["nu"] = "Något gick fel — se data/uppdatering.log"


def senaste_rapport() -> str | None:
    filer = sorted(p.name for p in RAPPORTER.glob("20*.html"))
    return filer[-1] if filer else None


class Hanterare(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(RAPPORTER), **kw)

    def svara_json(self, data, kod=200):
        kropp = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(kropp)))
        self.end_headers()
        self.wfile.write(kropp)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/" + (senaste_rapport() or "_mall.html"))
            self.end_headers()
        elif self.path == "/status":
            with lås:
                self.svara_json({**läge, "rapport": senaste_rapport()})
        elif self.path == "/rapporter":
            self.svara_json(sorted((p.name for p in RAPPORTER.glob("20*.html")), reverse=True))
        else:
            super().do_GET()

    def do_POST(self):
        # Egen header krävs: då kan ingen annan webbsida du besöker trycka
        # på knappen åt dig (webbläsaren skickar inte sådana headers mellan sajter).
        if self.path != "/uppdatera" or self.headers.get("X-Jobbsok") != "1":
            return self.svara_json({"fel": "nej"}, 403)
        with lås:
            if läge["kör"]:
                return self.svara_json({"fel": "En sökning körs redan"}, 409)
            läge.update(kör=True, start=time.time(), slut=None, ok=None,
                        nu="Startar…", steg=0)
        threading.Thread(target=kör_sökning, daemon=True).start()
        self.svara_json({"ok": True})

    def end_headers(self):
        # Rapporterna ändras — låt inte webbläsaren visa en gammal version
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass  # håll terminalen ren


if __name__ == "__main__":
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Hanterare)
    except OSError:
        raise SystemExit(f"Servern kör redan: http://localhost:{PORT}")
    print(f"Jobbrapporten: http://localhost:{PORT}   (Ctrl+C för att stänga)")
    server.serve_forever()
