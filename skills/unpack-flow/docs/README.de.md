<p align="center"><a href="https://once-email.com"><img src="../assets/unpack-flow-banner.png" alt="UnpackFlow by Once Email" width="100%"></a></p>

# UnpackFlow — verschachtelte Archive unbeaufsichtigt entpacken

[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [हिन्दी](README.hi.md) · [العربية](README.ar.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [日本語](README.ja.md) · [Русский](README.ru.md)

Wenn bei `-r` ein Ausgabename bereits existiert, ergänzt UnpackFlow den Quellordner, etwa `sample-backup-legacy-set-unpacked`, und verwendet bei weiteren Kollisionen `-2`, `-3`, ohne Ergebnisse zu überschreiben oder auszulassen.

Die kleine Suite `unpack-flow-minimal-testcases-v1.zip` deckt ZIP, TAR.GZ, Unicode, verschachtelte Archive, mehrteiliges `part01.exe` und einen erwarteten Fehler bei fehlendem Teil ab, ohne große Anwendungen oder Ausführung der SFX-Datei.

Die native Abnahme verwendet synthetische Daten unter `/data/unpack-flow-testcases`; der Pfad kann mit `UNPACK_FLOW_TEST_ROOT` geändert werden. Große Suiten sind optional und nur für Leistung oder zusätzliche Formatkompatibilität vorgesehen.

UnpackFlow verarbeitet Softwarepakete, Datensätze, Sicherungen, Medienbestände und andere große Archive. Es erkennt den ersten Teil, entpackt verschachtelte Ebenen nacheinander und zeigt Paket, Phase, Ebene und Laufzeit.

## Nutzung und Installation

Nutze `unpack-flow list 'Archive*'`, `plan`, `unpack-flow 'Archive*'`, `status`. Linux braucht Bash, Windows PowerShell und 7-Zip, macOS PowerShell 7+ und `7zz`. `scripts/build-release.sh` erstellt drei Pakete und SHA-256.

Python ist weder zum Ausführen von `unpack-flow` noch zum Entpacken erforderlich. Python 3 wird nur für die automatische Skill-Installation unter Linux/macOS mit `install_local.py` oder `install_local.sh` sowie für das Python-Audit benötigt. Windows verwendet den PowerShell-Installer `install_local.ps1`; auch manuelles Kopieren benötigt kein Python.

## Unterstützte Entpackvorgänge

UnpackFlow verarbeitet Verzeichnisse und Platzhaltermuster im Stapel, öffnet verschachtelte Archive Ebene für Ebene und erkennt den ersten Teil mehrteiliger RAR-Sätze. RAR-Selbstentpacker werden untersucht, ohne unbekannte EXE-Dateien auszuführen. Geeignet für Softwarepakete, Datensätze, Sicherungen, Medien, Protokolle sowie ISO- und WIM-Abbilder.

Standardmäßig werden bis zu 10 innere Ebenen verarbeitet. Beschädigte oder unvollständige innere Archive bleiben erhalten, werden protokolliert und übersprungen; mit `-StopOnError` wird beim ersten Fehler abgebrochen.

## Lernbeispiele

Nutze `list`, `plan`, `start`, `status`, `log` und `wait` für Sicherungen, Datensätze, Protokolle, Software oder mehrteilige Archive. Spiele sind nur ein Beispiel und keine Produktgrenze.

Auf allen drei Systemen läuft `run` mit Fortschrittsanzeige im Vordergrund; `start` startet einen Hintergrundauftrag und gibt dessen ID zurück.

Bei langen 7-Zip- oder UnRAR-Vorgängen wird die Laufzeit jede Sekunde aktualisiert und alle 30 Sekunden ein Aktivitätssignal protokolliert.

Unter macOS und Windows trennt `start` alle interaktiven Terminalströme; Hintergrundfortschritt erscheint nur im Protokoll und erzeugt keine ANSI-Sequenzen oder Signaltöne.

Mit `-r` bzw. `-Recursive` werden alle Archive in Unterordnern und deren innere Ebenen entpackt; bei Namensgleichheit wird sicher nach `Name-unpacked` geschrieben.

Auch `unpack-flow run *` wird unterstützt. Selbst nach der Shell-Erweiterung von `*` behält der Scan nur Einzelarchive und erste Teile wie `part1.exe`, `part1.rar`, `.7z.001` oder `.zip.001`; `.sha256`, fremde Dateien und Folgeteile werden verworfen.

`unpack-flow help` zeigt die gemeinsame Befehlsreferenz auf Englisch und vereinfachtem Chinesisch.

## Hintergrundaufträge und Protokolle

`unpack-flow start "Archiv" -Output "Ziel"` startet die Entpackung im Hintergrund und gibt eine Auftrags-ID zurück. Mit `unpack-flow status [ID]`, `unpack-flow log [ID]` und `unpack-flow wait [ID]` wird sie verfolgt; ohne ID gilt der neueste Auftrag. Protokolle liegen unter Windows in `%LOCALAPPDATA%\unpack-flow\state`, unter macOS/Linux in `~/.local/state/unpack-flow`.

TAR, TAR.GZ/TGZ und eigenständiges GZ werden unterstützt. Nach 7-Zip werden formatabhängig UnRAR, System-`tar`, GZip oder natives ZIP versucht; fehlgeschlagene Versuche werden bereinigt. Sind alle passenden Werkzeuge erfolglos, bleiben Archiv und Protokoll erhalten und das nächste Archiv wird ohne Endlosschleife verarbeitet.

Linux x64 enthält das offizielle UnRAR 7.23. Windows x64/ARM64 enthält das vollständige offizielle 7-Zip 26.02; x64 enthält zusätzlich UnRAR. Originalpakete und Lizenzen bleiben erhalten.

## Vollständiger Schnellstart

```bash
unpack-flow list '/data/archives/*'
unpack-flow plan '/data/archives/backup.part1.rar'
unpack-flow run '/data/archives/*' -Output '/data/extracted'
```

Für einen Hintergrundauftrag:

```bash
unpack-flow start '/data/archives/*' -Output '/data/extracted'
unpack-flow status
unpack-flow log
unpack-flow wait
```

`run` bleibt im Vordergrund; `start` gibt sofort eine Auftrags-ID zurück. Die Quellarchive bleiben in beiden Fällen erhalten.

## Befehlszeilenwerkzeug installieren

### Linux

```bash
./install-linux.sh --check
./install-linux.sh
unpack-flow version
```

### macOS

```bash
./install-macos.sh --check
./install-macos.sh
unpack-flow version
```

### Windows

```bat
install.bat -Check
install.bat
unpack-flow version
```

Die Prüfungen melden fehlende Abhängigkeiten, installieren aber keine Systemsoftware automatisch.

## Rekursion, Protokolle und Fehler

Mit `-r` oder `-Recursive` werden Unterordner durchsucht und innere Archivebenen geöffnet. Standardmäßig sind höchstens 10 innere Ebenen zulässig.

| Plattform | Standardmäßiges Statusverzeichnis |
|---|---|
| Windows | `%LOCALAPPDATA%\unpack-flow\state` |
| Linux/macOS | `${XDG_STATE_HOME:-$HOME/.local/state}/unpack-flow` |

UnpackFlow verwendet eine begrenzte Werkzeugkette: 7-Zip, UnRAR für RAR sowie passende Systemwerkzeuge für TAR, GZ oder ZIP. Unvollständige Versuche werden bereinigt. Sind alle Werkzeuge erfolglos, bleibt das Archiv erhalten, der Fehler wird protokolliert und die Verarbeitung wird fortgesetzt. `-StopOnError` stoppt ausdrücklich beim ersten Fehler.

## Tests und Installation als Agent Skill

```bash
bash tests/generate-minimal-public-suite.sh
bash tests/test-minimal-public-suite.sh
pwsh -NoProfile -File tests/test-minimal-public-suite.ps1
scripts/install_local.sh .
```

Unter Windows wird der Skill mit `scripts/install_local.ps1` installiert. Python ist zum Entpacken nicht erforderlich; es wird nur für den automatischen Linux/macOS-Skill-Installer und das Python-Audit benötigt.

## Sicherheit, Projekt und Hilfe

UnpackFlow erhält Quelldateien, überschreibt keine Ziele und führt keine unbekannten EXE-Dateien aus.

- Offizielle Website: [once-email.com](https://once-email.com)
- Erstellerin und Entwicklerin: helen.jar
- GitHub-Projekt: [pangxin12345/unpack-flow](https://github.com/pangxin12345/unpack-flow)
- Support-E-Mail: [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)

Bei Fragen schreiben Sie an [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com) oder [eröffnen Sie ein GitHub-Issue](https://github.com/pangxin12345/unpack-flow/issues).

MIT-Lizenz, Version 2.1.4.
