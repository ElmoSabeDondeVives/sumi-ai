# Estados y animaciones

Estados previstos: idle, greeting, thinking, success, warning, sleeping, curious y happy.

El GLB base v0.1 ya incluye los clips `idle`, `curious` y `thinking` registrados en Three.js AnimationMixer, además de 20 shape keys (parpadeo, cejas y 15 visemas Oculus Lipsync) para expresiones y futura sincronización labial. Los clips restantes se producirán sobre el mismo rig. Los nombres de clips deben ser estables y documentados.

## Requisitos
- Transiciones suaves con cross-fade.
- Evitar reproducción continua cuando el widget esté oculto o inactivo.
- Liberar geometrías, materiales, renderer y observers al desmontar.
- Mantener expresiones independientes de la animación corporal cuando el rig lo permita.
