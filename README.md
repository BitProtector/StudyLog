# StudyLog

Ein leichtgewichtiges Konsolentool mit GUI (Textual), zur Verwaltung von Modulen und Noten innerhalb eines Studienplans.

## Funktionen

- Import von Modulen via JSON-Datei
- Manuelles Anlegen und Zuweisen von Modulen zu Semestern
- Eingabe und Speicherung von Noten mit Gewichtung
- Anzeige aller Module samt Berechnungen (EN, MSP, Schnitt)
- Abhaengigkeitspruefung bei Semesterverschiebung
- Konsolen-GUI basierend auf [Textual](https://github.com/Textualize/textual)

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

### 6. (optional) Signieren der EXE (Notwendig, da die exe ansonsten als nicht vertrauenswürdig gekennzechnet wird.)
Für diesen Schritt ist das ["Windows SDK"](https://developer.microsoft.com/de-de/windows/downloads/windows-sdk/) erforderlich.
```bash
signtool sign /a /tr http://timestamp.digicert.com /td sha256 /fd sha256 dist\main.exe
```

### Struktur des JSON-Files, welches die Module enthällt.
```bash
[
  {
    "short": "ET1",
    "name": "Einführung Elektrotechnik",
    "ects": 5,
    "dependencies": {
      "de": []
    }
  }
]
```
