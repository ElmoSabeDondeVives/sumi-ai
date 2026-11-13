---
name: experto-agente-ia-3d
description: Experto en desarrollo e instalación de agentes de IA con avatar 3D (Three.js, GLB/glTF, Blender, Laravel). Usar cuando se trabaje en SUMI o tareas similares: instalación del proyecto, escena 3D, carga de modelos GLB, animaciones y estados, widget embebible, o integración del núcleo de IA con el avatar.
---

# Experto en desarrollo de agentes de IA en 3D

Eres un experto en construir agentes de IA con presencia visual 3D en la web: motor de render, pipeline de modelos, animación por estados e integración con el núcleo de inteligencia. Aplica este skill al trabajar en SUMI AI o proyectos equivalentes.

## Instalación del proyecto

1. **Preview frontend (sin Laravel):**
   - `npm install` en la raíz (dependencia única: `three`).
   - Servir la carpeta y abrir `index.html`. El import map resuelve `three` y `three/addons/` desde `node_modules`; no se requiere bundler.
   - Confirmar en consola el evento de estado: `model-loaded` (GLB real) o `placeholder` (modelo pendiente).
2. **Instalación completa:** crear proyecto Laravel compatible con PHP 8.4 en Laragon, copiar `resources/`, `public/` y `docs/` conservando rutas, luego `composer install`, `npm install`, `cp .env.example .env`, `php artisan key:generate`, `npm run dev`, `php artisan serve`. Configurar MySQL 8 en `.env`.
3. Guía completa: `docs/INSTRUCTIVO.md`. Especificación del avatar: `docs/character/produccion-avatar.md`.
4. **Regenerar el avatar base:** `blender -b -P tools/blender/build_sumi.py` exporta `public/models/sumi/base/sumi.glb` (malla, PBR, rig, blendshapes y clips). Conservar siempre los nombres de clips y shape keys.

## Arquitectura del avatar 3D

Separa siempre estas responsabilidades (patrón usado en `resources/js/sumi/`):

- **Engine** (`core/SumiEngine.js`): escena, cámara, luces, renderer, loop con `Clock` (delta limitado a 0.05s), `ResizeObserver` para adaptarse al contenedor, y fallback a placeholder si el GLB falla.
- **Character** (`core/SumiCharacter.js`): grupo raíz, `AnimationMixer`, mapa de clips indexado por nombre en minúsculas, cross-fade entre acciones.
- **Loader** (`core/SumiLoader.js`): `GLTFLoader` envuelto en Promise.
- **State machine** (`animation/SumiStateMachine.js`): valida estados permitidos y notifica cambios; los estados disparan animaciones, nunca al revés.
- **Widget** (`interface/SumiWidget.js`): compone engine + estados; es la API de alto nivel para embeber el agente.
- **Config** (`config/sumi.config.js`): única fuente de verdad para URL del modelo, cámara, luces, estados y expresiones. No hardcodear estos valores en otros módulos.

## Reglas del pipeline 3D (Blender → GLB → Three.js)

- Exportar GLB binario con animaciones incluidas a `public/models/sumi/base/sumi.glb`.
- Los nombres de clips deben coincidir con los estados (`idle`, `greeting`, `thinking`, `success`, `warning`, `sleeping`, `curious`, `happy`) y mantenerse estables.
- Respetar la identidad oficial del personaje (`docs/character/identity.md`): no rediseñar silueta ni rasgos; las formas (Original, Sage, Tech, Noble, Scout, Nova) conservan el núcleo visual.
- Nunca colocar imágenes 2D renombradas como modelos 3D.
- Usar `outputColorSpace = SRGBColorSpace` y limitar `pixelRatio` (máx. 2) para rendimiento.

## Reglas de rendimiento y ciclo de vida

- Pausar el render loop cuando el widget esté oculto o inactivo (`stop()`/`start()`).
- Al desmontar, liberar todo: geometrías, materiales, renderer, canvas y observers (`destroy()`/`dispose()`).
- Transiciones de animación siempre con cross-fade (`fadeIn`/`fadeOut`), nunca cortes secos.
- Validar estados antes de aplicarlos; estados inválidos deben lanzar error, no fallar en silencio.

## Reglas de integración con el núcleo de IA

- El avatar 3D es solo capa de presentación; la inteligencia vive en servicios separados.
- Integración con sistemas externos (Alpha ERP) solo por API REST autenticada sobre HTTPS.
- La IA nunca accede a SQL directamente: solo herramientas de negocio explícitas autorizadas por usuario, empresa, sede y almacén.
- Acciones sensibles requieren confirmación, validación y auditoría en el backend.
- Los secretos viven exclusivamente en el backend; nunca en el frontend ni en el repositorio.

## Convenciones de código

- JavaScript ES Modules, clases con prefijo `Sumi`, un archivo por clase.
- Mensajes de error y comentarios de cara al usuario en español.
- Exportar la API pública únicamente desde `resources/js/sumi/index.js`.
- Documentar decisiones nuevas en `docs/` (arquitectura, personaje, animación o integración según corresponda).
