# StudyLog

Ein leichtgewichtiges Konsolentool mit GUI (Textual), zur Verwaltung von Modulen und Noten innerhalb eines Studienplans.

## Funktionen

- Import von Modulen via JSON-Datei
- Manuelles Anlegen und Zuweisen von Modulen zu Semestern
- Eingabe und Speicherung von Noten mit Gewichtung
- Anzeige aller Module samt Berechnungen (Assessment, EN, MSP, Schnitt)
- Anzeige Semesterübergreifender Mittelwerte wie Notendurchschnitt, TOR, verbuchte ECTS-Punkte und erreichte ECTS-Punkte
- Abhängigkeitspruefung bei Semesterverschiebung
- Grafische Visualisierung von ECTS-Punkten und Semesternoten über alle Semester
- Hinweise bez. Assessment und ECTS-Punkten werden eingeblendet.
- Konsolen-GUI basierend auf [Textual](https://github.com/Textualize/textual)
- Multi-User-Funktionalität, damit die Applikation als Webservice betrieben werden kann.
- Kann als Docker deployed werden

## Voraussetzungen

- Python 3.9+
- Windows-Betriebssystem sofern EXE-Dateien erzeugt werden sollen. (Repo. nur unter Windows getestet)

## Installation

### 1. Klonen des Repos
```bash
git clone https://github.com/dein-nutzername/studienmanager.git
cd studienmanager
```

### 2. Erstellen eines virtual Environments
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Installieren der Abhängigkeiten des Repos
```bash
pip install -r requirements.txt
```

### 4. Starten der Applikation
```bash
python main.py
```

### 5. (optional) Kompilieren einer EXE
```bash
pyinstaller --noconfirm --onefile --console app.py
```

### 6. (optional) Signieren der EXE (Notwendig, da die exe ansonsten als nicht vertrauenswürdig gekennzeichnet wird.)
Für diesen Schritt ist das ["Windows SDK"](https://developer.microsoft.com/de-de/windows/downloads/windows-sdk/) erforderlich.
```bash
signtool sign /a /tr http://timestamp.digicert.com /td sha256 /fd sha256 dist\main.exe
```

### 7. (optional) Docker-Image bauen und starten
Um die App als Docker-Container zu deployen, kann das Image direkt von diesem Repo gebaut werden.
```bash
docker build -t studylog-web .
```
Anschliessend kann das Image als Container gestartet werden.
Als APP_PUBLIC_URL Variable muss die IP des Docker-Hosts bzw. beim Einsatz eines Revereproxys die öffentliche IP/URL angegeben werden.
```bash
docker run -e APP_PUBLIC_URL=http://192.168.1.30:8000 -p 192.168.1.30:8000:8000 studylog-web
```

### Struktur des JSON-Files, welches die Module enthält.
Wichtig ist hierbei, der Abschnitt "dependingModulesIDs". Dieser definiert die Abhängigkeiten unter den Modulen.

```bash
[
  {
        "bezeichnung": "aet2",
        "id": 6007772,
        "name": "Allgemeine Elektrotechnik 2",
        "sgAbbreviation": "EIT21",
        "sgId": 9447275,
        "ects": 3,
        "description": "Harmonische Zeitabhängigkeit von Strom und Spannung und deren Beschreibung ...",
        "dependingModulesIDs": [
            6007771,
            9746777,
            6008331,
            6008327
        ],
        "hasMsp": true,
        "profileAbbreviations": [],
        "difficulty": "BASIC",
        "status": "m.Aktiv",
        "dataScienceInformation": {
            "moduleType": "UNKNOWN"
        },
        "assessment": true,
        "gruppenAnrechnung": 0,
        "childModulegroups": []
    },
]
```
