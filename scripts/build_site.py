#!/usr/bin/env python3
"""Builds a static GitHub Pages site and discovers public HX3D models.
No external Python dependencies. Nothing is uploaded by this script.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
BUILD = ROOT / '_site'
MAX_MODEL_BYTES = 32 * 1024 * 1024  # Browser-friendly catalog size guideline


def get_meta(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(raw, dict):
        raise ValueError('model-info.json must be an object.')
    return raw


def model_details(path: Path, mesh_size_limit: int = MAX_MODEL_BYTES) -> dict:
    if path.stat().st_size > mesh_size_limit:
        raise ValueError(f'Model too large ({mesh_size_limit} byte limit): {path}')
    model = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(model, dict) or model.get('format') != 'HexaForge3D':
        raise ValueError(f'Not a HX3D model: {path}')
    version = model.get('format_version')
    if not isinstance(version, int) or isinstance(version, bool) or not (1 <= version <= 8):
        raise ValueError(f'Unsupported HX3D version: {path}')
    revision = model.get('format_revision', 0)
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0 or (version == 8 and revision > 1):
        raise ValueError(f'Unsupported HX3D revision: {path}')
    objects = model.get('objects')
    if not isinstance(objects, list):
        raise ValueError(f'Missing objects array: {path}')
    mesh_entries = model.get('mesh_library', [])
    if not isinstance(mesh_entries, list):
        raise ValueError(f'Invalid mesh library: {path}')
    refs = {}
    for entry in mesh_entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('id'), str) or entry['id'] in refs:
            raise ValueError(f'Invalid/duplicate mesh ID in {path}')
        refs[entry['id']] = entry.get('mesh')
    material_entries = model.get('materials', [])
    if not isinstance(material_entries, list):
        raise ValueError(f'Invalid material library: {path}')
    material_ids = set()
    for mat in material_entries:
        if not isinstance(mat, dict) or not isinstance(mat.get('id'), str) or mat['id'] in material_ids:
            raise ValueError(f'Invalid/duplicate material ID in {path}')
        material_ids.add(mat['id'])
    triangles = 0
    meshes = 0
    instances = 0
    object_ids = set()
    for obj in objects:
        if not isinstance(obj, dict) or not isinstance(obj.get('id'), str) or obj['id'] in object_ids:
            raise ValueError(f'Invalid/duplicate object ID in {path}')
        object_ids.add(obj['id'])
        if 'material_ref' in obj and obj['material_ref'] not in material_ids:
            raise ValueError(f'Unresolved material: {path} {obj["id"]}')
        src = obj.get('source') or {}
        mesh = None
        if src.get('type') == 'instance':
            instances += 1
            r = src.get('mesh_ref')
            if r not in refs:
                raise ValueError(f'Unresolved mesh reference: {path} {obj["id"]}')
            mesh = refs[r]
        elif src.get('type') == 'mesh':
            mesh = src.get('mesh')
        if mesh is None:
            continue
        if not isinstance(mesh, dict) or not isinstance(mesh.get('indices'), list) or len(mesh['indices']) % 3:
            raise ValueError(f'Invalid triangle index list: {path} {obj["id"]}')
        meshes += 1
        triangles += len(mesh['indices']) // 3
    version_str = f'{version}.{revision}' if version == 8 else str(version)
    return {
        'version': version_str,
        'objects': len(objects),
        'meshes': meshes,
        'instances': instances,
        'triangles': triangles,
        'size_bytes': path.stat().st_size,
    }


def build(source: Path = SITE, destination: Path = BUILD) -> dict:
    if not source.is_dir():
        raise ValueError(f'Site source is missing: {source}')
    if destination.resolve() == source.resolve() or source.resolve() in destination.resolve().parents:
        raise ValueError('Build destination must be separate from the source.')
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, symlinks=False)
    gallery = destination / 'hx3d'
    models = gallery / 'models'
    meta = get_meta(gallery / 'model-info.json')
    catalog = []
    for path in sorted(models.rglob('*')):
        if not path.is_file() or path.suffix.lower() != '.hx3d':
            continue
        rel = path.relative_to(gallery).as_posix()
        details = model_details(path)
        info = meta.get(rel, {})
        if not isinstance(info, dict):
            raise ValueError(f'Invalid metadata entry: {rel}')
        image = info.get('image')
        if image is not None:
            if not isinstance(image, str) or not image.startswith('previews/') or '..' in Path(image).parts or not (gallery/image).is_file():
                raise ValueError(f'Invalid preview image for {rel}: {image}')
        record = {
            'path': rel,
            'title': str(info.get('title') or path.stem.replace('-', ' ').replace('_', ' ')),
            'category': str(info.get('category') or path.parent.name.capitalize()),
            'description': str(info.get('description') or 'HX3D-Modell aus der Werkstatt.'),
            'image': image,
            **details,
        }
        catalog.append(record)
    (gallery / 'catalog.json').write_text(json.dumps({'schema_version': 1, 'models': catalog}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (destination / '.nojekyll').touch()
    return {'models': len(catalog), 'triangles': sum(x['triangles'] for x in catalog), 'output': str(destination)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build the static project lab + HX3D catalog')
    parser.add_argument('--source', type=Path, default=SITE)
    parser.add_argument('--output', type=Path, default=BUILD)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2, ensure_ascii=False))
