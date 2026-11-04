import json
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_site import build, model_details


class ProjectLabTests(unittest.TestCase):
    def test_fixture_is_hx3d(self):
        f = ROOT / 'site/hx3d/models/characters/cristal-wars-basisfigur.hx3d'
        info = model_details(f)
        self.assertEqual(info['version'], '8.1')
        self.assertEqual(info['triangles'], 3208)
        self.assertEqual(info['objects'], 48)

    def test_catalog_and_site_are_generated(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / 'public'
            result = build(destination=dst)
            cat = json.loads((dst/'hx3d/catalog.json').read_text(encoding='utf-8'))
            self.assertEqual(cat['schema_version'], 1)

            # Die Bibliothek wächst durch neue HX3D-Dateien: Anzahl nicht fest verdrahten.
            model_root = ROOT / 'site/hx3d'
            expected_paths = {
                path.relative_to(model_root).as_posix()
                for path in (model_root / 'models').rglob('*')
                if path.is_file() and path.suffix.lower() == '.hx3d'
            }
            catalog_models = cat['models']
            catalog_by_path = {model['path']: model for model in catalog_models}
            self.assertEqual(result['models'], len(expected_paths))
            self.assertEqual(len(catalog_models), len(catalog_by_path), 'Doppelte Katalogeinträge')
            self.assertEqual(set(catalog_by_path), expected_paths)

            for model in catalog_models:
                self.assertTrue((dst / 'hx3d' / model['path']).is_file())
                self.assertTrue((dst / 'hx3d' / model['image']).is_file())

            # Das ursprüngliche Testmodell muss weiterhin korrekt verarbeitet werden.
            fixture = catalog_by_path['models/characters/cristal-wars-basisfigur.hx3d']
            self.assertEqual(fixture['triangles'], 3208)
            self.assertEqual(fixture['image'], 'previews/generated/characters/cristal-wars-basisfigur.png')
            self.assertTrue((dst/'hx3d/viewer.html').exists())
            self.assertTrue((dst/'.nojekyll').exists())

    def test_additional_model_does_not_break_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / 'source'
            shutil.copytree(ROOT / 'site', source)
            original_count = len(list((source / 'hx3d/models').rglob('*.hx3d')))
            added_model = source / 'hx3d/models/vehicles/second-model.hx3d'
            added_model.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(
                source / 'hx3d/models/characters/cristal-wars-basisfigur.hx3d',
                added_model,
            )

            destination = tmp / 'public'
            result = build(source=source, destination=destination)
            self.assertEqual(result['models'], original_count + 1)
            cat = json.loads((destination / 'hx3d/catalog.json').read_text(encoding='utf-8'))
            added = next(x for x in cat['models'] if x['path'] == 'models/vehicles/second-model.hx3d')
            self.assertEqual(added['triangles'], 3208)
            self.assertEqual(added['image'], 'previews/generated/vehicles/second-model.png')
            self.assertTrue((destination / 'hx3d' / added['image']).is_file())

    def test_bad_reference_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = Path(tmp)/'broken.hx3d'
            m.write_text(json.dumps({
                'format': 'HexaForge3D', 'format_version': 8, 'format_revision': 1,
                'mesh_library': [], 'objects': [{'id':'a','source':{'type':'instance','mesh_ref':'missing'}}]
            }), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Unresolved mesh reference'):
                model_details(m)

    def test_single_use_resource_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = Path(tmp)/'single.hx3d'
            m.write_text(json.dumps({
                'format':'HexaForge3D','format_version':8,'format_revision':1,
                'mesh_library':[{'id':'one-use','mesh':{'positions':[0,0,0,1,0,0,0,1,0],'indices':[0,1,2]}}],
                'objects':[{'id':'a','source':{'type':'instance','mesh_ref':'one-use'}}]
            }), encoding='utf-8')
            self.assertEqual(model_details(m)['triangles'], 1)


if __name__ == '__main__':
    unittest.main()
