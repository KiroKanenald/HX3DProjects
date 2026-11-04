"""Regression tests for automatic thumbnails, resource sharing and isolation."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from build_site import build
from render_previews import draw_thumbnail


def sample_model() -> dict:
    # One triangle, 2 scene instances, mirrored/rotated parent group.
    return {
        'format': 'HexaForge3D', 'format_version': 8, 'format_revision': 1,
        'mesh_library': [{'id': 'triangle_res', 'mesh': {
            'positions': [-.4, 0, 0, .4, 0, 0, 0, 0, 1], 'indices': [0, 1, 2]}}],
        'materials': [{'id':'material_1','base_color':[.1,.8,.6],'opacity':1}],
        'objects': [
            {'id':'root','parent_id':None,'type':'group',
             'transform':{'position':[1,0,0], 'rotation_deg':[0,0,18], 'scale': [1,1,1]}},
            {'id':'one','parent_id':'root','material_ref':'material_1',
             'source':{'type':'instance','mesh_ref':'triangle_res'},
             'transform':{'position':[-.7,0,0],'rotation_deg':[0,0,0],'scale':[1,1,1]}},
            {'id':'two','parent_id':'root','material_ref':'material_1',
             'source':{'type':'instance','mesh_ref':'triangle_res'},
             'transform':{'position':[.7,0,0],'rotation_deg':[0,0,0],'scale':[1,1,1]}},
        ],
    }


class PreviewTests(unittest.TestCase):
    def test_sample_renders_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as t:
            a, b = Path(t)/'a.png', Path(t)/'b.png'
            data=sample_model()
            self.assertEqual(draw_thumbnail(data, a)['triangles'],2)
            self.assertEqual(draw_thumbnail(data, b)['triangles'],2)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with Image.open(a) as img:
                self.assertEqual(img.size,(640,440))
                self.assertEqual(img.format,'PNG')

    def test_new_file_creates_automatic_preview_and_catalog_entry(self):
        with tempfile.TemporaryDirectory() as t:
            src=Path(t)/'source'
            dst=Path(t)/'out'
            (src/'hx3d/models/vehicles').mkdir(parents=True)
            (src/'hx3d').mkdir(parents=True,exist_ok=True)
            p=src/'hx3d/models/vehicles/my_vehicle.hx3d'
            p.write_text(json.dumps(sample_model()), encoding='utf-8')
            out=build(source=src,destination=dst)
            self.assertEqual(out['models'],1)
            catalog=json.loads((dst/'hx3d/catalog.json').read_text())
            rec=catalog['models'][0]
            self.assertEqual(rec['triangles'],2)
            self.assertEqual(rec['instances'],2)
            self.assertEqual(rec['mesh_resources'],1)
            self.assertEqual(rec['materials'],1)
            self.assertEqual(rec['image'], 'previews/generated/vehicles/my_vehicle.png')
            self.assertTrue((dst/'hx3d'/rec['image']).exists())
            self.assertFalse((src/'hx3d/previews').exists(), 'Build must not modify the source repo')

    def test_optional_manual_preview_override(self):
        with tempfile.TemporaryDirectory() as t:
            src=Path(t)/'source';dst=Path(t)/'out'
            (src/'hx3d/models/vehicles').mkdir(parents=True)
            (src/'hx3d/previews').mkdir(parents=True)
            (src/'hx3d/models/vehicles/test.hx3d').write_text(json.dumps(sample_model()))
            (src/'hx3d/model-info.json').write_text(json.dumps({'models/vehicles/test.hx3d': {'image':'previews/manual.png'}}))
            Image.new('RGB',(16,16),(20,40,60)).save(src/'hx3d/previews/manual.png')
            build(source=src,destination=dst)
            rec=json.loads((dst/'hx3d/catalog.json').read_text())['models'][0]
            self.assertEqual(rec['image'],'previews/manual.png')
            self.assertTrue((dst/'hx3d/previews/generated/vehicles/test.png').exists())

    def test_cyclic_hierarchy_rejected_before_output(self):
        d=sample_model();d['objects'][0]['parent_id']='one'
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,'Cyclic parent'):
                draw_thumbnail(d,Path(t)/'fail.png')


if __name__=='__main__':
    unittest.main()
