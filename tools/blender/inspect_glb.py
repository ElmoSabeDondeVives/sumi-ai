# -*- coding: utf-8 -*-
"""
Inspector del GLB exportado: verificación barata sin navegador.

Valida estructura (clips, duraciones, morphs, materiales, texturas no negras,
triángulos) en segundos. Usar SIEMPRE antes de recurrir a capturas de pantalla.

Uso:
  python tools/blender/inspect_glb.py [ruta.glb]
"""

import json
import os
import struct
import sys
import zlib

DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', '..', 'public', 'models', 'sumi', 'base', 'sumi.glb')


def read_glb(path):
    data = open(path, 'rb').read()
    assert data[:4] == b'glTF', 'No es un GLB'
    length = struct.unpack('<I', data[8:12])[0]
    off, chunks = 12, []
    while off < length:
        clen, = struct.unpack('<I', data[off:off + 4])
        ctype = data[off + 4:off + 8]
        chunks.append((ctype, data[off + 8:off + 8 + clen]))
        off += 8 + clen
    gltf = json.loads(chunks[0][1])
    binc = chunks[1][1] if len(chunks) > 1 else b''
    return gltf, binc


def png_first_pixels(blob, n=4):
    assert blob[:8] == b'\x89PNG\r\n\x1a\n'
    pos, idat, meta = 8, b'', None
    while pos < len(blob):
        ln = struct.unpack('>I', blob[pos:pos + 4])[0]
        typ = blob[pos + 4:pos + 8]
        if typ == b'IHDR':
            meta = struct.unpack('>IIBB', blob[pos + 8:pos + 18])
        elif typ == b'IDAT':
            idat += blob[pos + 8:pos + 8 + ln]
        pos += 12 + ln
    raw = zlib.decompress(idat)
    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[meta[3]]
    return meta[0], meta[1], list(raw[1:1 + n * nch])


def main(path):
    gltf, binc = read_glb(path)
    size_mb = os.path.getsize(path) / 1024 / 1024
    print(f'GLB: {path} ({size_mb:.1f} MB)')

    # triángulos
    tris = 0
    for mesh in gltf.get('meshes', []):
        for prim in mesh['primitives']:
            if 'indices' in prim:
                tris += gltf['accessors'][prim['indices']]['count'] // 3
    print(f'triangulos: {tris}')

    # animaciones con duración
    print('clips:')
    for anim in gltf.get('animations', []):
        dur = 0
        for sampler in anim['samplers']:
            acc = gltf['accessors'][sampler['input']]
            dur = max(dur, acc.get('max', [0])[0])
        print(f"  {anim.get('name', '?'):10s} {dur:.2f}s  ({len(anim['channels'])} canales)")

    # morph targets
    mesh0 = gltf['meshes'][0]
    names = mesh0.get('extras', {}).get('targetNames', [])
    print(f'morphs ({len(names)}): {", ".join(names)}')

    # materiales
    print('materiales:', ', '.join(m.get('name', '?') for m in gltf.get('materials', [])))

    # texturas: detecta exportación en negro (bug conocido de imágenes en memoria)
    for img in gltf.get('images', []):
        bv = gltf['bufferViews'][img['bufferView']]
        blob = binc[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']]
        w, h, px = png_first_pixels(blob)
        flag = ' ⚠ POSIBLE NEGRO' if all(p == 0 for p in px) else ''
        print(f"  tex {img.get('name', '?'):20s} {w}x{h} px0={px}{flag}")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(DEFAULT))
