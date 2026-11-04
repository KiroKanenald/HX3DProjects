import json
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
            self.assertEqual(result['models'], 1)
            cat = json.loads((dst/'hx3d/catalog.json').read_text(encoding='utf-8'))
            self.assertEqual(cat['schema_version'], 1)
            model = cat['models'][0]
            self.assertEqual(model['triangles'], 3208)
            self.assertTrue((dst/'hx3d'/model['path']).exists())
            self.assertEqual(model['image'], 'previews/generated/characters/cristal-wars-basisfigur.png')
            self.assertTrue((dst/'hx3d'/model['image']).exists())
            self.assertTrue((dst/'hx3d/viewer.html').exists())
            self.assertTrue((dst/'.nojekyll').exists())

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
