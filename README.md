# Projektlabor · GitHub-Pages-Starter

Eine bewusst kleine, deutschsprachige, statische Projektübersicht mit HX3D-8.1-Modellbibliothek. Planet Miner und Cristal Wars sind zunächst **nur Platzhalter**. Keine Spiele-Quellcodes oder privaten Entwicklungsdateien enthalten.

## Inhalt

```text
site/
  index.html                 Startseite
  assets/style.css           Gemeinsames Layout
  hx3d/
    index.html               Öffentliche Modellbibliothek
    viewer.html              Neutraler HX3D 8.1 Viewer (kein eingebettetes Modell)
    gallery.js               Suche, Filter und Modelllinks
    model-info.json          Optionale Titel, Beschreibungen, Vorschaubilder
    models/characters/       Hier hinein kommen freigegebene .hx3d-Dateien
    previews/                 Vorschaubilder
  planet-miner/index.html    Platzhalter, noch kein Spielcode
  cristal-wars/index.html    Platzhalter, noch kein Spielcode
scripts/build_site.py        Validiert Modelle und erstellt catalog.json
.github/workflows/pages.yml  Automatischer Build + GitHub-Pages-Deployment
tests/test_build.py           Katalog- und Formatprüfungen
```

### Ein neues Modell hinzufügen

1. Eine **zur Veröffentlichung freigegebene** `.hx3d` unter `site/hx3d/models/` in einen passenden Unterordner legen, z. B. `vehicles/` oder `characters/`.
2. Optional einen Eintrag unter dem relativen Modellpfad in `site/hx3d/model-info.json` hinzufügen. `image` muss auf eine bestehende PNG-Datei innerhalb `site/hx3d/previews/` zeigen. Ohne Metadaten wird ein Titel aus dem Dateinamen gebildet.
3. In `main` committen/pushen. GitHub Actions baut den gesamten Katalog bei jedem Push **neu**, validiert Dateien und veröffentlicht die Website.

Dateien sind im Modellordner **öffentlich**. Keine Original-Game-Sources, API-Keys, privaten Dokumente oder ungeklärten Fremdassets hinzufügen. Der Build verwirft eine fehlerhafte HX3D-Datei und verhindert dadurch ein fehlerhaftes Deployment.

### GitHub Pages veröffentlichen

1. Ein neues Repository auf GitHub anlegen, z. B. `projektlabor` (für GitHub Free: **öffentlich**).
2. Den **Inhalt** dieses Starterordners in das Repository übernehmen. `main` als Standardbranch verwenden.
3. Auf GitHub im Repository **Settings → Pages → Build and deployment → Source → GitHub Actions** wählen.
4. Unter **Actions** den Workflow `Projektlabor auf GitHub Pages veröffentlichen` prüfen; bei Bedarf manuell per `Run workflow` starten. Die Actions-Umgebung benötigt Pages-Deployment-Berechtigung; für den Workflow wurden `pages: write` und `id-token: write` gesetzt.
5. Nach erfolgreichem Deployment lautet die Adresse bei einem Projekt-Repository üblicherweise `https://BENUTZERNAME.github.io/projektlabor/` (Repo-Name beachten).

**Achtung:** Ein öffentliches Repository und seine Dateien sind einsehbar. Auch bereitgestelltes JavaScript/WASM ist im Browser analysierbar; Minifizierung bietet keinen Schutz für Spielcode. Deshalb bleiben die Spielquellen privat und nur gesondert freigegebene Builds kommen später in dieses Repository.

### Lokal testen

Python 3.10+ genügt, keine Pakete installieren:

```sh
python -m unittest discover -s tests -v
python scripts/build_site.py
python -m http.server 8000 --directory _site
```

Dann `http://localhost:8000/` öffnen. **Nicht** `site/index.html` direkt doppelklicken: Die Galerie lädt `catalog.json` per HTTP und benötigt einen lokalen Webserver.

Der ursprüngliche HX3D-Viewer bleibt zusätzlich ohne Webserver für **lokale Dateiimporte** nutzbar, wenn `viewer.html` direkt geöffnet wird. Modell-Direktlinks (`?model=models/...`) funktionieren dagegen nur per HTTP(S). Der Viewer lädt ausschließlich Modelle aus seinem eigenen öffentlichen `models/`-Verzeichnis.

### Technische Notizen

- Die Modellbibliothek ist ein **statischer JSON-Katalog**, keine beschreibbare Datenbank. GitHub Pages bietet keine serverseitige Ordnerauflistung oder Schreibfunktion für Website-Besucher.
- `catalog.json` wird im Build erstellt und **muss nicht** ins Repository eingecheckt werden.
- Es werden nur `.hx3d`-Dateien automatisch aufgenommen. Dateien werden beim Build auf Grundstruktur, Version, referenzierte Meshes/Materialien und Tris-Zahlen geprüft; der Build ersetzt keinen vollständigen HexaForge-Konformitätstest.
- Die Viewer-Datei ist weiterhin eine eigenständige HTML ohne externe JavaScript-Abhängigkeiten. Ein URL-Parameter kann ein Modell aus `models/` laden; ohne diesen Parameter beginnt sie leer.
- `model-info.json` ist kein versteckter Speicher. Es ist eine öffentliche Metadatendatei.
- Um später die Spiele zu veröffentlichen, sollten freigegebene und gebaute Web-Distributionen **separat** aus privaten Entwicklungs-Repositories in die entsprechenden Verzeichnisse kopiert werden. Keine Entwicklungs-Repositories in das öffentliche Projektlabor importieren.

**Status:** Lokales Startpaket. Noch **nicht** mit deinem GitHub-Konto verbunden und **nicht** veröffentlicht.
