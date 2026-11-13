---
name: blender-pipeline-optimizado
description: Optimización de cuota y reutilización en tareas 3D/Blender de SUMI. Usar SIEMPRE antes de cualquier tarea de modelado, texturas, rig, shape keys, animación o exportación GLB, para reutilizar helpers existentes, elegir la verificación más barata y evitar errores ya resueltos.
---

# Pipeline Blender optimizado (SUMI)

Objetivo: máxima calidad con mínimo gasto. Reutilizar siempre lo que existe, verificar con la herramienta más barata posible y agrupar cambios en un solo ciclo.

## Activos ya instalados — NUNCA reinstalar ni recrear

- Blender 4.5 LTS: `C:\Program Files\Blender Foundation\Blender 4.5\blender.exe`
- Pipeline completo: `tools/blender/build_sumi.py` (regenera GLB + .blend con un comando)
- `tools/blender/sumi_base.blend`: fuente editable para GUI/artista
- Preview web con API viva: `window.sumi` en `index.html` (servidor estático simple)

## Helpers reutilizables en build_sumi.py — extender, no duplicar

| Necesidad | Helper existente |
|---|---|
| Parte del cuerpo esférica | `sphere(name, loc, radius, scale, rotation, …)` |
| Forma orgánica puntiaguda (orejas, hojas) | `ear_petal(name, loc, size, rotation, taper)` |
| Gema/cristal | `octahedron(name, loc, size)` |
| Textura procedural | `value_noise()` + `make_image()` (escribe PNG a disco vía `write_png`) |
| Material simple/emisivo | `simple_material(name, color, roughness, emission…)` |
| Shape key regional | `add_shape_key(obj, name, fn)` + `region_weight(co, centro, radio)` |
| Visema/boca | `mouth_morph(open_z, wide_x, pucker_y, press)` |
| Clip de animación | `make_action(arm, nombre, frames, keys)` + `key_bone()` |
| Paleta oficial | constantes `CREAM/PINK/VIOLET/…` al inicio del archivo |

Regla: una tarea nueva = editar `build_sumi.py` reutilizando estos helpers + 1 rebuild. No crear scripts paralelos para variantes del mismo avatar.

## Escalera de verificación (usar el peldaño más bajo que baste)

1. **Log del build** (gratis): `blender -b -P tools/blender/build_sumi.py` imprime triángulos, shape keys y clips. Suficiente para cambios de parámetros.
2. **`python tools/blender/inspect_glb.py`** (barato, sin navegador): valida clips+duraciones, canales, morphs, materiales y detecta texturas negras. Suficiente para animación/estructura.
3. **`blender -b -P tools/blender/diag_parts.py`** (barato): límites por pieza; usar ante geometría sospechosa (explosiones, piezas desplazadas).
4. **Captura de navegador** (caro): SOLO para cambios de silueta/estética que exijan juicio visual, y máximo 1–2 capturas por ciclo. Para poses deterministas: `s.stop(); s.playAnimation(clip,{fade:0}); for(...) s.character.update(1/30); s.renderer.render(s.scene,s.camera)` — el rAF se pausa en pestañas ocultas, nunca confiar en esperas de tiempo real.

## Agrupar trabajo (ahorro principal)

- Acumular TODOS los cambios solicitados y hacer UN solo ciclo editar→rebuild→verificar.
- Un rebuild tarda ~30 s y regenera todo (malla, texturas, rig, morphs, 8 clips, GLB y .blend): no hay rebuilds parciales, así que no dividir cambios en varios builds.
- Documentación y commit al final del lote, no por cambio.

## Errores ya resueltos — no volver a tropezar

1. **`transform_apply()` aplica también location por defecto** → los vértices quedan en coordenadas de mundo. Deformar SIEMPRE en local antes de aplicar transformaciones (ver `ear_petal`).
2. **Imágenes creadas en memoria (`bpy.data.images.new` + `pixels`) exportan NEGRAS** → escribir PNG a disco y cargar con `bpy.data.images.load` (ver `make_image`); `inspect_glb.py` detecta la regresión.
3. **Blender 4.4+ (acciones con slots): strips NLA creados por Python evalúan pose de reposo** → asignar `strip.action_slot = action.slots[0]` (ya hecho en `build_animations`).
4. **Nombres estables**: clips (`idle`,`curious`,`thinking`,`greeting`,`success`,`warning`,`sleeping`,`happy`) y shape keys (`blink_*`,`brow*`,`viseme_*`) son contrato con el motor web — jamás renombrar.
5. Loops perfectos: primer y último keyframe idénticos; 24 fps.

## Comandos canónicos

```bash
# regenerar todo (GLB + .blend)
blender -b -P tools/blender/build_sumi.py

# verificación estructural barata
python tools/blender/inspect_glb.py

# QA de límites de geometría
blender -b -P tools/blender/diag_parts.py
```

(En esta máquina `blender` no está en PATH: usar la ruta completa del ejecutable.)
