#!/usr/bin/env python3
"""Headless HX3D thumbnail renderer: no browser, GPU, API keys or network required.

Dependency set: NumPy + Pillow. Used only during the GitHub Pages build.
Output images are deterministic and never modify the uploaded HX3D files.

The HX3D viewer remains the authoritative interactive renderer. The preview
renderer intentionally supports flat base-color meshes, hierarchy, local
transforms, basic joints and HX3D 8.x mesh/material references, not textures.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT = 640, 440
RENDERER_VERSION = '0.2.0'


def _transform(t: dict | None) -> np.ndarray:
    t = t or {}
    p = np.asarray(t.get('position', [0, 0, 0]), dtype=np.float64)
    r = np.deg2rad(np.asarray(t.get('rotation_deg', [0, 0, 0]), dtype=np.float64))
    s = np.asarray(t.get('scale', [1, 1, 1]), dtype=np.float64)
    if any(v.shape != (3,) or not np.all(np.isfinite(v)) for v in (p, r, s)):
        raise ValueError('Invalid transform')
    cx, cy, cz = np.cos(r)
    sx, sy, sz = np.sin(r)
    rx = np.array([[1,0,0,0],[0,cx,-sx,0],[0,sx,cx,0],[0,0,0,1]], dtype=np.float64)
    ry = np.array([[cy,0,sy,0],[0,1,0,0],[-sy,0,cy,0],[0,0,0,1]], dtype=np.float64)
    rz = np.array([[cz,-sz,0,0],[sz,cz,0,0],[0,0,1,0],[0,0,0,1]], dtype=np.float64)
    scale = np.diag([*s, 1.0])
    trans = np.eye(4)
    trans[:3, 3] = p
    return trans @ rz @ ry @ rx @ scale


def _joint(j: dict | None) -> np.ndarray:
    if not isinstance(j, dict) or not j.get('enabled'):
        return np.eye(4)
    axis = str(j.get('axis', 'Z')).upper()
    if axis not in 'XYZ':
        axis = 'Z'
    i = 'XYZ'.index(axis)
    if j.get('type') == 'linear':
        m = np.eye(4)
        m[i, 3] = float(j.get('current_position', 0)) - float(j.get('rest_position', 0))
        return m
    r = [0., 0., 0.]
    r[i] = float(j.get('current_angle_deg', 0)) - float(j.get('rest_angle_deg', 0))
    return _transform({'rotation_deg': r})


def _extract(model: dict) -> list[tuple[np.ndarray, np.ndarray, np.ndarray, float]]:
    objects = model.get('objects', [])
    objmap = {obj['id']: obj for obj in objects}
    meshes = {item['id']: item['mesh'] for item in model.get('mesh_library', [])}
    materials = {item['id']: item for item in model.get('materials', [])}
    worlds: dict[str, np.ndarray] = {}
    visiting: set[str] = set()
    visible: dict[str, bool] = {}

    def world_and_visible(oid: str) -> tuple[np.ndarray, bool]:
        if oid in worlds:
            return worlds[oid], visible[oid]
        if oid in visiting:
            raise ValueError('Cyclic parent hierarchy')
        visiting.add(oid)
        o = objmap[oid]
        parentid = o.get('parent_id')
        if parentid is not None:
            if parentid not in objmap:
                raise ValueError(f'Missing parent {parentid}')
            parent, pv = world_and_visible(parentid)
        else:
            parent, pv = np.eye(4), True
        worlds[oid] = parent @ _transform(o.get('transform')) @ _joint(o.get('joint'))
        visible[oid] = pv and o.get('visible', True) is not False
        visiting.remove(oid)
        return worlds[oid], visible[oid]

    result = []
    for obj in objects:
        matrix, shown = world_and_visible(obj['id'])
        if not shown:
            continue
        src = obj.get('source') or {}
        if src.get('type') == 'instance':
            mesh = meshes[src['mesh_ref']]
        elif src.get('type') == 'mesh':
            mesh = src['mesh']
        else:
            continue
        points = np.asarray(mesh['positions'], dtype=np.float64)
        indices = np.asarray(mesh['indices'], dtype=np.int64)
        if not len(indices):
            continue
        points = points.reshape(-1, 3)
        tris = indices.reshape(-1, 3)
        # Preserve local transforms, parent rotations/scales and primitive geometry.
        homo = np.column_stack([points, np.ones(len(points))])
        world_points = (homo @ matrix.T)[:, :3]
        if not np.all(np.isfinite(world_points)):
            raise ValueError('Nonfinite transformed mesh coordinates')
        if obj.get('material_ref') is not None:
            mat = materials[obj['material_ref']]
        else:
            mat = obj.get('material') or {}
        color = np.asarray(mat.get('base_color', [0.65, 0.72, 0.77])[:3], dtype=np.float64)
        if color.shape != (3,) or not np.all(np.isfinite(color)):
            color = np.array([0.65, 0.72, 0.77])
        opacity = min(1.0, max(0.0, float(mat.get('opacity', 1.0))))
        result.append((world_points, tris, np.clip(color, 0, 1), opacity))
    return result


def _background(size: tuple[int, int]) -> Image.Image:
    w, h = size
    y, x = np.mgrid[0:h, 0:w]
    # Subtle backdrop gradient and blue-green studio light.
    glow = np.clip(1.0 - (((x - w * .51) / (w * .78))**2 + ((y - h * .27) / (h * .89))**2), 0, 1)
    vertical = y / h
    col = np.empty((h, w, 3), dtype=np.uint8)
    for i, (base, amount) in enumerate([(11, 13), (23, 22), (34, 24)]):
        col[:, :, i] = np.clip(base + amount * glow - vertical * 4, 0, 255)
    return Image.fromarray(col, 'RGB')


def draw_thumbnail(model: dict, output: Path, size: tuple[int, int] = (WIDTH, HEIGHT)) -> dict:
    """Render model at a fixed camera angle. Return metadata about this thumbnail."""
    w, h = size
    if w < 128 or h < 128:
        raise ValueError('Preview resolution is too small')
    base = _background((w, h))
    parts = _extract(model)
    if not parts:
        draw = ImageDraw.Draw(base)
        draw.text((w // 2, h // 2), 'Kein darstellbares Mesh', fill=(150, 180, 193), anchor='mm')
        output.parent.mkdir(parents=True, exist_ok=True)
        base.save(output, format='PNG', optimize=True)
        return {'width': w, 'height': h, 'triangles': 0}

    all_points = np.concatenate([p for p, _, _, _ in parts], axis=0)
    xyzmin, xyzmax = all_points.min(axis=0), all_points.max(axis=0)
    target = (xyzmin + xyzmax) / 2

    # Matches the offline viewer's Z-up orientation and default yaw/pitch.
    yaw, pitch = -0.59, 0.45
    direction = np.array([math.cos(pitch) * math.sin(yaw),
                          -math.cos(pitch) * math.cos(yaw), math.sin(pitch)])
    forward = -direction
    right = np.cross(forward, np.array([0, 0, 1.0]))
    right /= max(1e-12, np.linalg.norm(right))
    up = np.cross(right, forward)
    up /= max(1e-12, np.linalg.norm(up))
    rel = all_points - target
    proj_xy = np.column_stack([rel @ right, rel @ up])
    xmin, ymin = proj_xy.min(axis=0)
    xmax, ymax = proj_xy.max(axis=0)
    sx = max(xmax - xmin, 1e-9)
    sy = max(ymax - ymin, 1e-9)
    # Slightly more generous framing for slender vertical figures.
    pixels_per_unit = min(w * .77 / sx, h * .77 / sy)
    xcenter = (xmin + xmax) * .5
    ycenter = (ymin + ymax) * .5

    # Small projected ground contact guide, drawn behind the model.
    draw = ImageDraw.Draw(base, 'RGBA')
    floor_z = float(xyzmin[2])
    floor_origin = np.array([target[0], target[1], floor_z])
    floor_y = int(round(h * .50 - ((floor_origin - target) @ up - ycenter) * pixels_per_unit))
    floor_y = max(int(h * .15), min(int(h * .9), floor_y))
    draw.ellipse((w*.23, floor_y-7, w*.77, floor_y+16), fill=(0, 0, 0, 39))
    draw.line((w*.10, floor_y+17, w*.90, floor_y+17), fill=(104, 165, 182, 23), width=1)
    for offset in [-100, -50, 0, 50, 100]:
        xx=w*.5+offset
        draw.line((xx, floor_y+10, xx+offset*.45, h-14), fill=(109, 163, 182, 15), width=1)

    # A per-pixel depth buffer avoids painter-order artefacts on overlapping components.
    rgb = np.asarray(base, dtype=np.float32).copy()
    depth_buffer = np.full((h, w), -np.inf, dtype=np.float64)
    light = np.array([-0.45, -0.65, 1.30], dtype=np.float64)
    light /= np.linalg.norm(light)

    face_batches = []
    for pts, indices, color, opacity in parts:
        if opacity <= 0:
            continue
        delta = pts - target
        xx = w*.5 + ((delta @ right) - xcenter) * pixels_per_unit
        yy = h*.5 - ((delta @ up) - ycenter) * pixels_per_unit
        zz = delta @ direction  # larger = closer to the camera
        screen = np.column_stack((xx, yy, zz))
        face_batches.append((screen, pts, indices, color, opacity))

    # Transparent triangles are sorted back-to-front after opaque ones.
    translucent = []
    for screen, world, indices, color, alpha in face_batches:
        for i0, i1, i2 in indices:
            tri = screen[[i0, i1, i2]]
            world_tri = world[[i0, i1, i2]]
            normal = np.cross(world_tri[1]-world_tri[0], world_tri[2]-world_tri[0])
            length = np.linalg.norm(normal)
            if not length or not np.isfinite(length):
                continue
            normal /= length
            # Two-sided previews: visible even when imported mesh winding differs.
            dotl = float(abs(np.dot(normal, light)))
            brightness = min(1.35, .38 + .69 * dotl)
            shade = np.clip(color * 235 * brightness + 13, 0, 255)
            if alpha < 0.999:
                translucent.append((float(np.mean(tri[:, 2])), tri, shade, alpha))
            else:
                _rasterize(tri, shade, 1.0, rgb, depth_buffer)
    for _, tri, shade, alpha in sorted(translucent, key=lambda item: item[0]):
        _rasterize(tri, shade, alpha, rgb, depth_buffer, transparent=True)

    image = Image.fromarray(np.asarray(np.clip(rgb, 0, 255), dtype=np.uint8), 'RGB')
    # Minimal corner treatment, outside the projected model region.
    d = ImageDraw.Draw(image, 'RGBA')
    d.line((18, 18, 47, 18), fill=(112, 201, 214, 82), width=2)
    d.line((18, 18, 18, 47), fill=(112, 201, 214, 82), width=2)
    d.line((w-18, h-18, w-47, h-18), fill=(112, 201, 214, 52), width=2)
    d.line((w-18, h-18, w-18, h-47), fill=(112, 201, 214, 52), width=2)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format='PNG', optimize=True)
    return {'width': w, 'height': h, 'triangles': int(sum(len(i) for _,i,_,_ in parts))}


def _rasterize(tri: np.ndarray, shade: np.ndarray, alpha: float,
               rgb: np.ndarray, depth_buffer: np.ndarray, transparent: bool=False) -> None:
    h, w, _ = rgb.shape
    x0 = max(0, int(math.floor(float(np.min(tri[:, 0])))))
    x1 = min(w, int(math.ceil(float(np.max(tri[:, 0])))) + 1)
    y0 = max(0, int(math.floor(float(np.min(tri[:, 1])))))
    y1 = min(h, int(math.ceil(float(np.max(tri[:, 1])))) + 1)
    if x0 >= x1 or y0 >= y1:
        return
    a, b, c = tri
    det = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
    if not np.isfinite(det) or abs(det) < 1e-12:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    px, py = xx+.5, yy+.5
    wa = ((b[1]-c[1])*(px-c[0]) + (c[0]-b[0])*(py-c[1]))/det
    wb = ((c[1]-a[1])*(px-c[0]) + (a[0]-c[0])*(py-c[1]))/det
    wc = 1-wa-wb
    mask = (wa >= -1e-7) & (wb >= -1e-7) & (wc >= -1e-7)
    if not np.any(mask):
        return
    zz = wa*a[2] + wb*b[2] + wc*c[2]
    z_region = depth_buffer[y0:y1, x0:x1]
    mask &= zz >= z_region - 1e-9
    if not np.any(mask):
        return
    region = rgb[y0:y1, x0:x1]
    if transparent:
        # For transparent mesh triangles, blend without modifying opaque Z.
        region[mask] = region[mask] * (1.0 - alpha) + shade * alpha
    else:
        region[mask] = shade
        z_region[mask] = zz[mask]
