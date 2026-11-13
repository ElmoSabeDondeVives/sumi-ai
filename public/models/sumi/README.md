# Modelos SUMI

Ubicación:
- base/sumi.glb: personaje base v0.1 (generado proceduralmente con `tools/blender/build_sumi.py`).
- forms/: variantes o recursos específicos de formas.
- textures/: texturas externas si fueran necesarias.
- thumbnails/: vistas previas.

El GLB base incluye: malla multi-material (~17.8k tris), texturas PBR 1K (albedo, roughness, normal), rig (tronco, cuello, cabeza, orejas, hombros, brazos y cola), 20 shape keys (parpadeo, cejas y 15 visemas Oculus) y clips en loop `idle`, `curious` y `thinking`.

Para regenerarlo: `blender -b -P tools/blender/build_sumi.py`. El modelo esculpido a mano en Blender podrá reemplazar este base conservando los nombres de clips y shape keys. No colocar aquí una imagen 2D renombrada como si fuera un modelo 3D.
