# Estados y animaciones

Estados previstos: idle, greeting, thinking, success, warning, sleeping, curious y happy.

Cada clip se entregará en el modelo GLB oficial y se registrará en Three.js AnimationMixer. Los nombres de clips deben ser estables y documentados. La máquina de estados actual valida transiciones de estado; las animaciones reales se conectarán cuando exista el rig.

## Requisitos
- Transiciones suaves con cross-fade.
- Evitar reproducción continua cuando el widget esté oculto o inactivo.
- Liberar geometrías, materiales, renderer y observers al desmontar.
- Mantener expresiones independientes de la animación corporal cuando el rig lo permita.
