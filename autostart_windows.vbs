' Startar jobbsok-servern osynligt i WSL. Dubbelklicka för att starta nu,
' eller lägg en kopia i Windows Autostart-mapp (Win+R → shell:startup)
' så startar den varje gång du loggar in. Ta bort kopian för att stänga av.
CreateObject("Wscript.Shell").Run "wsl.exe -d Ubuntu-24.04 -- bash -lc ""cd ~/projects/jobbsok && python3 server.py""", 0, False
