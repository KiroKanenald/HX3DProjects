# Projektlabor 0.2 · HX3D Asset Workshop

Eine bewusst kleine, deutschsprachige und statische GitHub-Pages-Projektübersicht. **Die HX3D-Bibliothek erzeugt ab Version 0.2 bei jedem Build automatisch Modellvorschaubilder.** Für neue Modelle genügt es, eine freigegebene `.hx3d` in den Modellordner zu legen und zu pushen. Planet Miner und Cristal Wars bleiben **nur Platzhalter**; es wird kein Spiele-Entwicklungsquellcode veröffentlicht.

## Was neu ist (0.2)

- **Automatische PNG-Vorschaubilder** aus der tatsächlichen HX3D-Geometrie (640 × 440 Pixel, feste Studioansicht). Kein Screenshot, keine Vorschau-Uploads, kein Browser und kein GPU-Treiber für den Build erforderlich.
- **HX3D 8.1:** Renderer berücksichtigt Parent-Transformationen, Gelenkstellung, Inline-Meshes, `mesh_library`/`mesh_ref`, `material_ref`, Base Color und Transparenz näherungsweise. Z-Puffer verhindert die meisten Verdeckungsfehler.
- Katalog zeigt Dreiecke, Meshes, Materialien, Instanzen, HX3D-Version und Dateigröße.
- **Optionale manuelle Vorschaubilder** bleiben per `model-info.json` möglich, falls du später ein bestimmtes Motiv willst.
- GitHub Actions installiert die zwei benötigten **Build-Abhängigkeiten** (NumPy und Pillow), generiert Vorschaubilder und den Katalog, testet, veröffentlicht.
- Im Repository liegt **nur das HX3D-Modell**. Die generierten Bilder landen ausschließlich in der öffentlichen Build-Ausgabe `_site/hx3d/previews/generated/`.

## Struktur

```text
site/
  index.html
  assets/style.css
  hx3d/
    index.html                 Galerie
    viewer.html               Neutraler HX3D-8.1-Betrachter
    gallery.js                Katalog, Suche, Kategorien
    model-info.json           Optionale Titel, Kategorien, Beschreibung, manuelle Bilder
    models/
      characters/
        cristal-wars-basisfigur.hx3d
    previews/                 Nur manuell gewählte Vorschaubilder, falls gewünscht
  planet-miner/index.html     Platzhalter
  cristal-wars/index.html     Platzhalter
scripts/build_site.py        Kataloggenerator und Website-Kopie
scripts/render_previews.py   Automatischer HX3D-Thumbnail-Renderer
requirements-build.txt      NumPy und Pillow (nur für Build)
tests/                      8 automatisierte Tests
.github/workflows/pages.yml GitHub Pages Build + Deploy
```

## Neues Modell veröffentlichen

1. **Nur selbst erstellte oder ausdrücklich freigegebene** `.hx3d` in `site/hx3d/models/` ablegen. Beispielsweise `site/hx3d/models/vehicles/pm09-manta.hx3d`.
2. Optional eintragen in `site/hx3d/model-info.json`:

   ```json
   {
     "models/vehicles/pm09-manta.hx3d": {
       "title": "PM-09 MANTA",
       "category": "Raumschiffe",
       "description": "Leichtes Abbauschiff für Planet Miner."
     }
   }
   ```

3. Dateien committen und auf Branch `main` pushen.
4. GitHub Actions baut die Website automatisch. Das Bild landet im veröffentlichten Build unter `hx3d/previews/generated/vehicles/pm09-manta.png`, der Eintrag erscheint in der Galerie.

**Hinweis:** Namen von Modellordnern und Dateien für die öffentliche Galerie nur aus ASCII-Buchstaben, Ziffern, `_`, `-`, `.` verwenden (keine Leerzeichen oder Umlaute). Metadaten dürfen selbstverständlich Umlaute enthalten. Bildgenerierung ist von Titeln/Metadaten unabhängig.

### Manuelles Bild als Ausnahme

Ein Modell kann im Metadateneintrag optional `"image": "previews/manual.png"` setzen. Das Bild muss zusätzlich unter `site/hx3d/previews/manual.png` liegen. Der Build erstellt **trotzdem** die automatisch berechnete Vorschau; angezeigt wird das manuell gewählte Bild. Ohne `image` erscheint immer die automatisch berechnete Vorschau.

## GitHub Pages einrichten / aktualisieren

- Den **Inhalt** dieses Starterordners in dein bestehendes öffentliches Projektlabor-Repository übernehmen (die bestehenden Dateien ersetzen/ergänzen, nicht den ZIP-Ordner als Unterordner hochladen).
- Settings → Pages → Source: **GitHub Actions**.
- Auf `main` pushen. Der Workflow testet, baut und veröffentlicht `_site`.
- Falls GitHub Actions Berechtigungen zur Pages-Veröffentlichung fehlen, Repository-Einstellungen und Workflow-Berechtigungen prüfen.
- Die Website funktioniert als Projektseite unter `https://BENUTZERNAME.github.io/REPOSITORY/` dank relativer Pfade.
- Die Bilder selbst und alle `.hx3d` im Modellordner sind **öffentlich downloadbar**.

## Lokal testen

Python 3.10+; benötigt NumPy und Pillow zum Rendern der Vorschaubilder:

```sh
python -m pip install -r requirements-build.txt
python -m unittest discover -s tests -v
python scripts/build_site.py
python -m http.server 8000 --directory _site
```

Anschließend `http://localhost:8000/` öffnen. Der öffentliche Viewer ist auch ohne Modell über `hx3d/viewer.html` nutzbar. Die Galerie benötigt HTTP(S), nicht `file://`.

## Technische Grenzen

- Statischer JSON-Katalog, **keine serverseitige Datenbank**. Der Build durchsucht beim Push den Modellordner und erstellt das Verzeichnis.
- Thumbnail-Renderer ist eine eigenständige **Softwarevorschau** und kein pixelidentischer HexaForge-Renderer. Keine Texturen, PBR, Lichtquellen, Bones, Animationen oder komplexe glTF-Materialeffekte. Halbtransparenz wird angenähert.
- Parent-Transformationsreihenfolge, Mesh-Instanzen, Materialzuordnung und sichtbare Gruppen werden berücksichtigt.
- Der Build prüft HX3D-Grundstruktur und Referenzen; dies ersetzt nicht die vollständige Formatvalidierung in HexaForge.
- Der Server kann nicht auf lokale Dateien anderer Nutzer zugreifen. Bei lokaler Dateiauswahl werden diese nur im Browser gerendert und **nicht hochgeladen**.
- Statische Spiel-Demos könnten später freigegeben werden, aber Browser-JavaScript/WASM ist immer herunterladbar und analysierbar. Private Entwicklungs-Repositories gehören nicht in dieses öffentliche Repository.
- GitHub Pages hat Ressourcenlimits; für sehr große Assetpakete gegebenenfalls später einen separaten Download-Host nutzen.

**Status:** Lokale Version 0.2, fertig zum Push in das bereits funktionierende GitHub-Pages-Repository. Nicht automatisch in dein GitHub-Repository hochgeladen.
