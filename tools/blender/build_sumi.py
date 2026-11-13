# -*- coding: utf-8 -*-
"""
Pipeline de producción del avatar SUMI (Blender headless).

Genera proceduralmente el avatar oficial estilo Pixar chibi:
  malla multi-material -> UVs -> texturas PBR 1K -> rig -> shape keys
  (parpadeo, cejas, 15 visemas Oculus) -> clips idle/curious/thinking
  -> exportación GLB a public/models/sumi/base/sumi.glb

Uso:
  blender -b -P tools/blender/build_sumi.py
"""

import math
import os
import struct
import tempfile
import zlib

import bpy
import numpy as np
from mathutils import Euler, Vector

# ---------------------------------------------------------------- paleta
CREAM = (0.949, 0.913, 0.874, 1.0)        # F2E9DF
PINK = (0.910, 0.706, 0.722, 1.0)         # E8B4B8
NOSE_PINK = (0.851, 0.627, 0.659, 1.0)    # D9A0A8
VIOLET = (0.463, 0.396, 0.910, 1.0)       # 7665E8
DEEP_VIOLET = (0.141, 0.078, 0.361, 1.0)  # 24145C
LILAC = (0.725, 0.686, 0.941, 1.0)        # punta de cola

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
EXPORT_PATH = os.path.join(REPO_ROOT, 'public', 'models', 'sumi', 'base', 'sumi.glb')

FPS = 24


# ---------------------------------------------------------------- utilidades
def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = FPS


def sphere(name, location, radius, scale=(1, 1, 1), rotation=(0, 0, 0), segments=32, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=radius, location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler = Euler([math.radians(a) for a in rotation], 'XYZ')
    bpy.ops.object.transform_apply(rotation=True, scale=True)
    return obj


def ear_petal(name, location, size, rotation, taper=0.45, segments=28, rings=22):
    """Oreja orgánica tipo pétalo a partir de esfera unitaria deformada en local.

    size: semiejes (ancho, profundidad, alto/2). La punta se afina y curva atrás.
    """
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=1.0, location=(0, 0, 0)
    )
    obj = bpy.context.active_object
    obj.name = name
    rx, ry, rz = size
    for v in obj.data.vertices:
        rel = v.co.z  # esfera unitaria: -1 base .. +1 punta
        v.co.x *= rx
        v.co.y *= ry
        v.co.z *= rz
        if rel > 0:
            t = rel * rel
            pinch = 1.0 - t * (1.0 - taper)
            v.co.x *= pinch
            # aplana hacia la punta y la curva ligeramente hacia atrás
            v.co.y = v.co.y * (pinch * 0.9 + 0.1) + t * rz * 0.12
    obj.rotation_euler = Euler([math.radians(a) for a in rotation], 'XYZ')
    obj.location = location
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def octahedron(name, location, size):
    mesh = bpy.data.meshes.new(name)
    s = size
    verts = [(0, 0, s), (0, 0, -s), (s, 0, 0), (-s, 0, 0), (0, s, 0), (0, -s, 0)]
    faces = [(0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2),
             (1, 4, 2), (1, 3, 4), (1, 5, 3), (1, 2, 5)]
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    bpy.context.collection.objects.link(obj)
    # UVs mínimos para el exportador
    obj.data.uv_layers.new(name='UVMap')
    return obj


# ---------------------------------------------------------------- texturas PBR
def value_noise(size, cell, seed):
    rng = np.random.default_rng(seed)
    grid = rng.random((size // cell + 2, size // cell + 2))
    big = np.kron(grid, np.ones((cell, cell)))[:size, :size]
    # suavizado box blur
    for _ in range(10):
        big = (big + np.roll(big, 1, 0) + np.roll(big, -1, 0)
               + np.roll(big, 1, 1) + np.roll(big, -1, 1)) / 5.0
    return big


def write_png(path, rgb_uint8):
    """Escribe un PNG RGB8 sin dependencias externas."""
    h, w, _ = rgb_uint8.shape
    raw = b''.join(b'\x00' + rgb_uint8[y].tobytes() for y in range(h))

    def chunk(tag, payload):
        c = tag + payload
        return struct.pack('>I', len(payload)) + c + struct.pack('>I', zlib.crc32(c))

    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
           + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)


def make_image(name, pixels_rgba, non_color=False):
    rgb = (np.clip(pixels_rgba[..., :3], 0, 1) * 255).astype(np.uint8)
    path = os.path.join(tempfile.gettempdir(), f'{name}.png')
    write_png(path, rgb)
    img = bpy.data.images.load(path)
    img.name = name
    img.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'
    img.pack()
    return img


def build_fur_textures(size=1024):
    noise = value_noise(size, 32, seed=7)
    fine = value_noise(size, 8, seed=21)

    albedo = np.empty((size, size, 4), dtype=np.float32)
    base = np.array(CREAM[:3])
    variation = ((noise - 0.5) * 0.035 + (fine - 0.5) * 0.015)[..., None]
    albedo[..., :3] = np.clip(base + variation, 0, 1)
    albedo[..., 3] = 1.0

    rough = np.empty((size, size, 4), dtype=np.float32)
    rough_val = np.clip(0.75 + (noise - 0.5) * 0.12, 0, 1)[..., None]
    rough[..., :3] = rough_val
    rough[..., 3] = 1.0

    # normal map sutil a partir del gradiente del ruido fino (micro-pelaje)
    height = fine * 0.5 + noise * 0.5
    gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 2.0
    gy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 2.0
    nz = np.ones_like(gx)
    length = np.sqrt(gx * gx + gy * gy + nz * nz)
    normal = np.empty((size, size, 4), dtype=np.float32)
    normal[..., 0] = (-gx / length) * 0.5 + 0.5
    normal[..., 1] = (-gy / length) * 0.5 + 0.5
    normal[..., 2] = (nz / length) * 0.5 + 0.5
    normal[..., 3] = 1.0

    return (make_image('sumi_fur_albedo', albedo),
            make_image('sumi_fur_roughness', rough, non_color=True),
            make_image('sumi_fur_normal', normal, non_color=True))


def simple_material(name, color, roughness, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    if emission:
        bsdf.inputs['Emission Color'].default_value = emission
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    return mat


def fur_material(albedo_img, rough_img, normal_img):
    mat = bpy.data.materials.new('sumi_fur')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes['Principled BSDF']

    tex_a = nodes.new('ShaderNodeTexImage')
    tex_a.image = albedo_img
    tex_a.location = (-500, 300)
    links.new(tex_a.outputs['Color'], bsdf.inputs['Base Color'])

    tex_r = nodes.new('ShaderNodeTexImage')
    tex_r.image = rough_img
    tex_r.location = (-500, 0)
    links.new(tex_r.outputs['Color'], bsdf.inputs['Roughness'])

    tex_n = nodes.new('ShaderNodeTexImage')
    tex_n.image = normal_img
    tex_n.location = (-600, -320)
    nmap = nodes.new('ShaderNodeNormalMap')
    nmap.inputs['Strength'].default_value = 0.2
    nmap.location = (-300, -320)
    links.new(tex_n.outputs['Color'], nmap.inputs['Color'])
    links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


# ---------------------------------------------------------------- construcción de malla
def build_body_parts():
    """Crea las partes y devuelve (lista_pelaje, dict_partes_especiales)."""
    fur = []

    body = sphere('body', (0, 0, 0.66), 0.62, scale=(0.82, 0.74, 1.0), segments=48, rings=36)
    fur.append(body)

    head = sphere('head', (0, 0, 1.42), 0.48, scale=(1.0, 0.94, 0.96), segments=56, rings=42)
    fur.append(head)

    muzzle = sphere('muzzle', (0, -0.41, 1.31), 0.145, scale=(1.12, 0.72, 0.72), segments=28, rings=20)
    fur.append(muzzle)

    for side, sx in (('L', 1), ('R', -1)):
        # orejas de zorro: base ancha, punta definida, inclinadas hacia afuera
        ear = ear_petal(f'ear_{side}', (sx * 0.315, 0.02, 1.96), (0.21, 0.065, 0.29),
                        (-6, 24 * sx, 0), taper=0.18)
        fur.append(ear)
        # interior rosa casi del tamaño de la oreja, adelantado para llenar el frente
        inner = ear_petal(f'ear_inner_{side}', (sx * 0.31, -0.035, 1.965), (0.175, 0.048, 0.25),
                          (-6, 24 * sx, 0), taper=0.16, segments=22, rings=18)
        fur.append(inner)
        arm = sphere(f'arm_{side}', (sx * 0.56, -0.02, 0.86), 0.13,
                     scale=(0.85, 0.85, 1.9), segments=24, rings=16)
        fur.append(arm)
        leg = sphere(f'leg_{side}', (sx * 0.22, -0.02, 0.17), 0.155,
                     scale=(1.0, 1.15, 1.1), segments=24, rings=16)
        fur.append(leg)

    # cola esponjosa curvada hacia arriba, asomando junto a la cabeza (lado derecho)
    tail_specs = [
        ('tail_1', (0.08, 0.48, 0.50), 0.20, (1, 1.25, 1)),
        ('tail_2', (0.24, 0.68, 0.72), 0.24, (1, 1.2, 1.1)),
        ('tail_3', (0.42, 0.76, 1.04), 0.22, (1, 1, 1.25)),
    ]
    for name, loc, rad, scl in tail_specs:
        fur.append(sphere(name, loc, rad, scale=scl, segments=28, rings=20))
    tail_tip = sphere('tail_tip', (0.56, 0.74, 1.34), 0.17, scale=(1, 0.9, 1.2), segments=28, rings=20)

    special = {
        'eye_L': sphere('eye_L', (0.19, -0.40, 1.50), 0.105, scale=(1, 0.55, 1), segments=20, rings=14),
        'eye_R': sphere('eye_R', (-0.19, -0.40, 1.50), 0.105, scale=(1, 0.55, 1), segments=20, rings=14),
        'nose': sphere('nose', (0, -0.535, 1.345), 0.045, scale=(1.2, 0.7, 0.9), segments=16, rings=10),
        'gem': octahedron('gem', (0, -0.40, 1.74), 0.085),
        'tail_tip': tail_tip,
    }
    return fur, special


def assign_materials(obj, fur_mat, materials):
    obj.data.materials.append(fur_mat)                 # 0 pelaje
    obj.data.materials.append(materials['inner'])      # 1 interior oreja
    obj.data.materials.append(materials['eye'])        # 2 ojos
    obj.data.materials.append(materials['nose'])       # 3 nariz
    obj.data.materials.append(materials['gem'])        # 4 gema
    obj.data.materials.append(materials['lilac'])      # 5 punta cola


def join_all(fur, special, fur_mat, materials):
    """Une todo en un solo objeto conservando índices de material."""
    part_material = {}
    for o in fur:
        part_material[o.name] = 1 if o.name.startswith('ear_inner') else 0
    part_material[special['eye_L'].name] = 2
    part_material[special['eye_R'].name] = 2
    part_material[special['nose'].name] = 3
    part_material[special['gem'].name] = 4
    part_material[special['tail_tip'].name] = 5

    everything = fur + list(special.values())
    for o in everything:
        o.data.materials.clear()

    bpy.ops.object.select_all(action='DESELECT')
    for o in everything:
        o.select_set(True)
    bpy.context.view_layer.objects.active = everything[0]

    # marca cada parte para reasignar material tras unir
    for o in everything:
        layer = o.data.attributes.new('mat_tag', 'INT', 'FACE')
        values = [part_material[o.name]] * len(o.data.polygons)
        layer.data.foreach_set('value', values)

    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = 'SUMI'
    obj.data.name = 'SUMI'

    assign_materials(obj, fur_mat, materials)
    tags = obj.data.attributes['mat_tag']
    values = [0] * len(obj.data.polygons)
    tags.data.foreach_get('value', values)
    for poly, tag in zip(obj.data.polygons, values):
        poly.material_index = tag
    obj.data.attributes.remove(obj.data.attributes['mat_tag'])

    # saneamiento: normales consistentes hacia afuera y malla válida
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.validate()

    bpy.ops.object.shade_smooth()
    return obj


def unwrap(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=0.01)
    bpy.ops.object.mode_set(mode='OBJECT')


# ---------------------------------------------------------------- shape keys
def region_weight(co, center, radius):
    d = (Vector(co) - Vector(center)).length
    if d >= radius:
        return 0.0
    t = 1.0 - d / radius
    return t * t * (3 - 2 * t)  # smoothstep


MOUTH = (0, -0.52, 1.25)
EYE_L = (0.19, -0.40, 1.50)
EYE_R = (-0.19, -0.40, 1.50)
BROW_L = (0.19, -0.40, 1.67)
BROW_R = (-0.19, -0.40, 1.67)


def add_shape_key(obj, name, displace):
    """displace(co) -> Vector offset o None."""
    key = obj.shape_key_add(name=name, from_mix=False)
    basis = obj.data.shape_keys.key_blocks['Basis']
    for i in range(len(obj.data.vertices)):
        off = displace(basis.data[i].co)
        if off is not None:
            key.data[i].co = basis.data[i].co + off
    return key


def mouth_morph(open_z=0.0, wide_x=0.0, pucker_y=0.0, press=0.0, radius=0.17):
    def fn(co):
        w = region_weight(co, MOUTH, radius)
        if w <= 0:
            return None
        sx = 1.0 if co.x >= 0 else -1.0
        lower = max(0.0, (MOUTH[2] + 0.03 - co.z) / 0.12)
        return Vector((
            sx * wide_x * w,
            (-pucker_y * w) + (press * 0.3 * w),
            -open_z * w * min(lower, 1.0) + press * w * 0.01,
        ))
    return fn


def build_shape_keys(obj):
    obj.shape_key_add(name='Basis', from_mix=False)

    # --- parpadeo: colapsa el ojo verticalmente hacia su centro
    for name, center in (('blink_L', EYE_L), ('blink_R', EYE_R)):
        def blink(co, c=center):
            w = region_weight(co, c, 0.17)
            if w <= 0:
                return None
            return Vector((0, 0.025 * w, (c[2] - co.z) * 0.99 * min(w * 1.6, 1.0)))
        add_shape_key(obj, name, blink)

    # --- cejas
    def brows(up=0.0, inner=0.0, outer=0.0):
        def fn(co):
            best = 0.0
            side = 0.0
            for c, sx in ((BROW_L, 1.0), (BROW_R, -1.0)):
                w = region_weight(co, c, 0.14)
                if w > best:
                    best, side = w, sx
            if best <= 0:
                return None
            toward_center = -side * inner * best
            return Vector((toward_center, -0.01 * best, (up + outer * abs(co.x) * 2.5) * best))
        return fn

    add_shape_key(obj, 'browUp', brows(up=0.05))
    add_shape_key(obj, 'browDown', brows(up=-0.035, inner=0.02))
    add_shape_key(obj, 'browHappy', brows(up=0.02, outer=0.03))

    # --- 15 visemas estándar Oculus Lipsync
    visemes = {
        'viseme_sil': mouth_morph(press=0.01),
        'viseme_PP': mouth_morph(press=0.03),
        'viseme_FF': mouth_morph(open_z=0.015, press=0.02),
        'viseme_TH': mouth_morph(open_z=0.025, wide_x=0.005),
        'viseme_DD': mouth_morph(open_z=0.03),
        'viseme_kk': mouth_morph(open_z=0.035, wide_x=-0.005),
        'viseme_CH': mouth_morph(open_z=0.03, pucker_y=0.02),
        'viseme_SS': mouth_morph(wide_x=0.02, press=0.015),
        'viseme_nn': mouth_morph(open_z=0.02, press=0.01),
        'viseme_RR': mouth_morph(open_z=0.025, pucker_y=0.015),
        'viseme_aa': mouth_morph(open_z=0.07, wide_x=0.01),
        'viseme_E': mouth_morph(open_z=0.035, wide_x=0.025),
        'viseme_ih': mouth_morph(open_z=0.02, wide_x=0.03),
        'viseme_oh': mouth_morph(open_z=0.05, pucker_y=0.03, wide_x=-0.015),
        'viseme_ou': mouth_morph(open_z=0.03, pucker_y=0.045, wide_x=-0.02),
    }
    for name, fn in visemes.items():
        add_shape_key(obj, name, fn)


# ---------------------------------------------------------------- rig
BONES = {
    # nombre: (cabeza, cola, padre)
    'root':       ((0, 0, 0.0),   (0, 0, 0.30),  None),
    'spine':      ((0, 0, 0.30),  (0, 0, 0.95),  'root'),
    'chest':      ((0, 0, 0.95),  (0, 0, 1.18),  'spine'),
    'neck':       ((0, 0, 1.18),  (0, 0, 1.32),  'chest'),
    'head':       ((0, 0, 1.32),  (0, 0, 1.95),  'neck'),
    'ear.L':      ((0.30, 0.03, 1.78),  (0.40, 0.02, 2.26), 'head'),
    'ear.R':      ((-0.30, 0.03, 1.78), (-0.40, 0.02, 2.26), 'head'),
    'shoulder.L': ((0.30, 0, 1.08),  (0.52, 0, 1.02),  'chest'),
    'shoulder.R': ((-0.30, 0, 1.08), (-0.52, 0, 1.02), 'chest'),
    'arm.L':      ((0.52, 0, 1.02),  (0.60, -0.02, 0.62), 'shoulder.L'),
    'arm.R':      ((-0.52, 0, 1.02), (-0.60, -0.02, 0.62), 'shoulder.R'),
    'tail.01':    ((0.04, 0.32, 0.52),  (0.16, 0.58, 0.64),  'root'),
    'tail.02':    ((0.16, 0.58, 0.64),  (0.38, 0.74, 0.96),  'tail.01'),
    'tail.03':    ((0.38, 0.74, 0.96),  (0.60, 0.76, 1.42),  'tail.02'),
}


def build_armature():
    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm_obj = bpy.context.active_object
    arm_obj.name = 'SUMI_Rig'
    bpy.ops.object.mode_set(mode='EDIT')
    ebones = arm_obj.data.edit_bones
    ebones.remove(ebones[0])
    created = {}
    for name, (head, tail, parent) in BONES.items():
        b = ebones.new(name)
        b.head, b.tail = head, tail
        if parent:
            b.parent = created[parent]
        created[name] = b
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj


def skin(mesh_obj, arm_obj):
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')


# ---------------------------------------------------------------- animación
def key_bone(pbone, frame, rot=None, loc=None, scale=None):
    if rot is not None:
        pbone.rotation_euler = Euler([math.radians(a) for a in rot], 'XYZ')
        pbone.keyframe_insert('rotation_euler', frame=frame)
    if loc is not None:
        pbone.location = Vector(loc)
        pbone.keyframe_insert('location', frame=frame)
    if scale is not None:
        pbone.scale = Vector(scale)
        pbone.keyframe_insert('scale', frame=frame)


def make_action(arm_obj, name, length, keys):
    """keys: lista (bone, frame, kwargs)."""
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    if arm_obj.animation_data is None:
        arm_obj.animation_data_create()
    arm_obj.animation_data.action = action

    for pbone in arm_obj.pose.bones:
        pbone.rotation_mode = 'XYZ'
        pbone.rotation_euler = Euler((0, 0, 0))
        pbone.location = Vector((0, 0, 0))
        pbone.scale = Vector((1, 1, 1))

    for bone, frame, kwargs in keys:
        key_bone(arm_obj.pose.bones[bone], frame, **kwargs)

    for fcu in action.fcurves:
        for kp in fcu.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.easing = 'EASE_IN_OUT'
    return action, length


def build_animations(arm_obj):
    actions = []

    # idle: respiración + balanceo de cola y orejas (3 s loop)
    idle_keys = []
    for f, s in ((1, 1.0), (36, 1.05), (72, 1.0)):
        idle_keys.append(('chest', f, {'scale': (s, s, s)}))
    for f, r in ((1, 0), (36, 3), (72, 0)):
        idle_keys.append(('head', f, {'rot': (r, 0, 0)}))
    for f, r in ((1, -12), (36, 12), (72, -12)):
        idle_keys.append(('tail.02', f, {'rot': (0, 0, r)}))
        idle_keys.append(('tail.03', f, {'rot': (0, 0, r * 1.4)}))
    for f, r in ((1, 0), (36, -6), (72, 0)):
        idle_keys.append(('ear.L', f, {'rot': (r, 0, 0)}))
        idle_keys.append(('ear.R', f, {'rot': (r, 0, 0)}))
    actions.append(make_action(arm_obj, 'idle', 72, idle_keys))

    # curious: escucha activa, asentir con orejas al frente (2.5 s loop)
    curious_keys = []
    for f, r in ((1, 0), (12, 16), (24, -5), (36, 14), (48, -3), (60, 0)):
        curious_keys.append(('head', f, {'rot': (r, 0, 0)}))
    for f, r in ((1, 0), (12, -22), (48, -22), (60, 0)):
        curious_keys.append(('ear.L', f, {'rot': (r, 0, 0)}))
        curious_keys.append(('ear.R', f, {'rot': (r, 0, 0)}))
    for f, r in ((1, 0), (30, 14), (60, 0)):
        curious_keys.append(('tail.03', f, {'rot': (r, 0, 0)}))
    actions.append(make_action(arm_obj, 'curious', 60, curious_keys))

    # thinking: cabeza ladeada mirando arriba, cola lenta (4 s loop)
    think_keys = []
    for f, rx, rz in ((1, 0, 0), (20, -12, 16), (60, -9, 18), (96, 0, 0)):
        think_keys.append(('head', f, {'rot': (rx, 0, rz)}))
    for f, r in ((1, 0), (20, -16), (60, -13), (96, 0)):
        think_keys.append(('ear.L', f, {'rot': (0, 0, r)}))
        think_keys.append(('ear.R', f, {'rot': (0, 0, -r)}))
    for f, r in ((1, -8), (48, 9), (96, -8)):
        think_keys.append(('tail.02', f, {'rot': (0, 0, r)}))
    for f, r in ((1, 0), (48, 5), (96, 0)):
        think_keys.append(('spine', f, {'rot': (0, 0, r)}))
    actions.append(make_action(arm_obj, 'thinking', 96, think_keys))

    # greeting: saludo con el brazo izquierdo en alto y balanceo (2.5 s loop)
    greet_keys = []
    for f, r in ((1, 0), (8, -70), (52, -70), (60, 0)):
        greet_keys.append(('shoulder.L', f, {'rot': (0, 0, r)}))
    for f, r in ((1, 0), (8, -25), (16, 25), (26, -25), (36, 25), (46, -25), (52, 0), (60, 0)):
        greet_keys.append(('arm.L', f, {'rot': (0, r, 0)}))
    for f, r in ((1, 0), (14, -10), (44, -8), (60, 0)):
        greet_keys.append(('head', f, {'rot': (0, 0, r)}))
    for f, r in ((1, 0), (10, -14), (50, -14), (60, 0)):
        greet_keys.append(('ear.L', f, {'rot': (r, 0, 0)}))
        greet_keys.append(('ear.R', f, {'rot': (r, 0, 0)}))
    for f, r in ((1, -14), (30, 14), (60, -14)):
        greet_keys.append(('tail.02', f, {'rot': (0, 0, r)}))
    actions.append(make_action(arm_obj, 'greeting', 60, greet_keys))

    # success: celebración con rebote y cola enérgica (2 s loop)
    success_keys = []
    for f, h in ((1, 0), (12, 0.07), (24, 0), (36, 0.05), (48, 0)):
        success_keys.append(('root', f, {'loc': (0, h, 0)}))
    for f, r in ((1, 0), (12, -10), (24, 0), (36, -7), (48, 0)):
        success_keys.append(('head', f, {'rot': (r, 0, 0)}))
    for f, r in ((1, -24), (12, 24), (24, -24), (36, 24), (48, -24)):
        success_keys.append(('tail.02', f, {'rot': (0, 0, r)}))
        success_keys.append(('tail.03', f, {'rot': (0, 0, r * 1.2)}))
    for f, r in ((1, 0), (12, -12), (36, -12), (48, 0)):
        success_keys.append(('ear.L', f, {'rot': (r, 0, 0)}))
        success_keys.append(('ear.R', f, {'rot': (r, 0, 0)}))
    actions.append(make_action(arm_obj, 'success', 48, success_keys))

    # warning: alerta, negación con la cabeza y orejas atrás (2.5 s loop)
    warn_keys = []
    for f, r in ((1, 0), (10, 14), (25, -14), (40, 10), (50, -8), (60, 0)):
        warn_keys.append(('head', f, {'rot': (0, r, 0)}))
    for f, r in ((1, 0), (10, 18), (50, 18), (60, 0)):
        warn_keys.append(('ear.L', f, {'rot': (r, 0, 0)}))
        warn_keys.append(('ear.R', f, {'rot': (r, 0, 0)}))
    for f, r in ((1, 0), (10, -6), (50, -6), (60, 0)):
        warn_keys.append(('spine', f, {'rot': (r, 0, 0)}))
    for f, r in ((1, -6), (30, 6), (60, -6)):
        warn_keys.append(('tail.02', f, {'rot': (0, 0, r)}))
    actions.append(make_action(arm_obj, 'warning', 60, warn_keys))

    # sleeping: cabeza caída, respiración profunda y lenta (4 s loop)
    sleep_keys = []
    for f, r in ((1, 16), (48, 21), (96, 16)):
        sleep_keys.append(('head', f, {'rot': (r, 0, 0)}))
    for f, s in ((1, 1.0), (48, 1.07), (96, 1.0)):
        sleep_keys.append(('chest', f, {'scale': (s, s, s)}))
    for f, r in ((1, 10), (48, 13), (96, 10)):
        sleep_keys.append(('ear.L', f, {'rot': (r, 0, -14)}))
        sleep_keys.append(('ear.R', f, {'rot': (r, 0, 14)}))
    for f, r in ((1, -4), (48, 4), (96, -4)):
        sleep_keys.append(('tail.02', f, {'rot': (0, 0, r)}))
    for f, r in ((1, 4), (48, 7), (96, 4)):
        sleep_keys.append(('spine', f, {'rot': (r, 0, 0)}))
    actions.append(make_action(arm_obj, 'sleeping', 96, sleep_keys))

    # happy: alegría con rebote ligero y cola rápida (2.5 s loop)
    happy_keys = []
    for f, h in ((1, 0), (15, 0.05), (30, 0), (45, 0.05), (60, 0)):
        happy_keys.append(('root', f, {'loc': (0, h, 0)}))
    for f, r in ((1, -7), (30, 7), (60, -7)):
        happy_keys.append(('head', f, {'rot': (0, 0, r)}))
    for f, r in ((1, -26), (15, 26), (30, -26), (45, 26), (60, -26)):
        happy_keys.append(('tail.02', f, {'rot': (0, 0, r)}))
        happy_keys.append(('tail.03', f, {'rot': (0, 0, r * 1.2)}))
    for f, r in ((1, -10), (30, -15), (60, -10)):
        happy_keys.append(('ear.L', f, {'rot': (r, 0, 0)}))
        happy_keys.append(('ear.R', f, {'rot': (r, 0, 0)}))
    actions.append(make_action(arm_obj, 'happy', 60, happy_keys))

    # apila cada acción en su propia pista NLA (el exportador usa el nombre de pista)
    arm_obj.animation_data.action = None
    for action, _length in actions:
        track = arm_obj.animation_data.nla_tracks.new()
        track.name = action.name
        strip = track.strips.new(action.name, 1, action)
        # Blender 4.4+: las acciones usan slots; sin esto el strip evalúa pose de reposo
        if action.slots:
            strip.action_slot = action.slots[0]
    return actions


# ---------------------------------------------------------------- exportación
def export_glb(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        export_yup=True,
        export_apply=False,
        export_animations=True,
        export_animation_mode='NLA_TRACKS',
        export_morph=True,
        export_skins=True,
        export_materials='EXPORT',
        export_image_format='AUTO',
    )


def main():
    clean_scene()

    albedo, rough, normal = build_fur_textures(1024)
    materials = {
        'inner': simple_material('sumi_inner_ear', PINK, 0.65),
        'eye': simple_material('sumi_eye', VIOLET, 0.15, emission=DEEP_VIOLET, emission_strength=0.6),
        'nose': simple_material('sumi_nose', NOSE_PINK, 0.4),
        'gem': simple_material('sumi_gem', VIOLET, 0.1, emission=VIOLET, emission_strength=1.0),
        'lilac': simple_material('sumi_tail_tip', LILAC, 0.7),
    }
    fur_mat = fur_material(albedo, rough, normal)

    fur, special = build_body_parts()
    sumi = join_all(fur, special, fur_mat, materials)
    unwrap(sumi)
    build_shape_keys(sumi)

    rig = build_armature()
    skin(sumi, rig)
    build_animations(rig)

    tri_count = sum(len(p.vertices) - 2 for p in sumi.data.polygons)
    print(f'[SUMI] triangulos: {tri_count}')
    print(f'[SUMI] shape keys: {len(sumi.data.shape_keys.key_blocks) - 1}')
    print('[SUMI] clips: idle, curious, thinking, greeting, success, warning, sleeping, happy')

    export_glb(EXPORT_PATH)
    print(f'[SUMI] exportado: {EXPORT_PATH}')

    # archivo fuente editable para trabajo manual en Blender GUI
    blend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sumi_base.blend')
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f'[SUMI] blend editable: {blend_path}')


if __name__ == '__main__':
    main()
