# Estados y animaciones

Estados: idle, greeting, thinking, success, warning, sleeping, curious y happy.

El GLB base incluye **los 8 clips** registrados en Three.js AnimationMixer, además de 20 shape keys (parpadeo, cejas y 15 visemas Oculus Lipsync) para expresiones y futura sincronización labial. Los nombres de clips deben ser estables y documentados.

## Requisitos
- Transiciones suaves con cross-fade.
- Evitar reproducción continua cuando el widget esté oculto o inactivo.
- Liberar geometrías, materiales, renderer y observers al desmontar.
- Mantener expresiones independientes de la animación corporal cuando el rig lo permita.
