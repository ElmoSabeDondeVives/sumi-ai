# Instructivo del proyecto SUMI AI

Guía práctica para instalar, entender y trabajar en SUMI AI: la mascota virtual 3D independiente para Alpha ERP.

---

## 1. ¿Qué es SUMI AI?

SUMI es un agente de IA con presencia visual 3D (criatura híbrida zorro/gato con gema violeta, ver [character/identity.md](./character/identity.md)). Este repositorio contiene la **fundación visual MVP v0.1**:

- Motor de render Three.js listo para cargar un modelo GLB.
- Máquina de estados de animación.
- Widget embebible.
- Documentación de arquitectura, personaje, animación e integración.
- **Avatar 3D base v0.1** en `public/models/sumi/base/sumi.glb`, generado con el pipeline Blender de [tools/blender/build_sumi.py](../tools/blender/build_sumi.py): ~17.8k triángulos, texturas PBR 1K, rig, 20 blendshapes (parpadeo, cejas y 15 visemas) y clips `idle`, `curious` y `thinking`. Si el archivo falta, el motor dibuja un placeholder geométrico.

## 2. Requisitos

| Herramienta | Versión | Uso |
|---|---|---|
| Laragon | actual | Entorno local Windows |
| PHP | 8.4 | Backend Laravel (futuro) |
| MySQL | 8 | Base de datos |
| Node.js + npm | LTS | Dependencias frontend (`three`) |
| Composer | 2.x | Laravel (cuando se cree el esqueleto) |
| Blender | actual | Modelado, rig y exportación GLB/glTF |

## 3. Instalación rápida (preview frontend)

Para ver la escena 3D sin Laravel:

```bash
cd C:\laragon\www\sumi-ai
npm install
```

Luego abre `http://sumi-ai.test/index.html` desde Laragon (o sirve la carpeta con cualquier servidor estático). El `index.html` incluye un *import map* que resuelve `three` y `three/addons/` desde `node_modules`, por lo que no se requiere bundler para la preview.

Verás el avatar base de SUMI y en la consola el evento `{ type: 'model-loaded', placeholder: false }`. Si el GLB faltara, aparece el placeholder con `{ type: 'placeholder', message: 'Modelo GLB pendiente' }`.

## 4. Instalación completa (con Laravel)

Este repositorio **no** es un proyecto Laravel generado; prepara los módulos frontend y la documentación. Pasos:

1. En Laragon, crea un proyecto Laravel compatible con PHP 8.4.
2. Copia dentro de él las carpetas `resources/`, `public/` y `docs/`, conservando rutas.
3. Ejecuta:

```bash
composer install
npm install
cp .env.example .env
php artisan key:generate
npm run dev
php artisan serve
```

4. Configura MySQL en `.env` (base de datos `sumi_ai`) y ejecuta `php artisan migrate` cuando existan migraciones.

## 5. Estructura del proyecto

```
sumi-ai/
├── index.html                      # Preview standalone de la escena 3D
├── resources/
│   ├── css/sumi/sumi.css           # Estilos del escenario y badge de estado
│   └── js/sumi/
│       ├── index.js                # Punto de entrada (re-exporta API pública)
│       ├── config/sumi.config.js   # Configuración central (modelo, cámara, luces, estados)
│       ├── core/
│       │   ├── SumiEngine.js       # Escena, cámara, renderer, loop y placeholder
│       │   ├── SumiCharacter.js    # Modelo, AnimationMixer y clips
│       │   └── SumiLoader.js       # Carga GLB con GLTFLoader
│       ├── animation/
│       │   └── SumiStateMachine.js # Estados válidos y transiciones
│       └── interface/
│           └── SumiWidget.js       # Widget: engine + máquina de estados
├── public/models/sumi/             # GLB base v0.1, formas, texturas y thumbnails
├── tools/blender/build_sumi.py     # Pipeline Blender headless que genera el GLB
├── docs/                           # Arquitectura, personaje, animación, integración
└── tests/                          # Pruebas (pendiente)
```

## 6. Uso de la API JavaScript

### Motor directo

```js
import { SumiEngine } from './resources/js/sumi/core/SumiEngine.js';

const sumi = new SumiEngine({
    container: '#sumi-container',          // selector o elemento DOM
    model: '/models/sumi/base/sumi.glb',   // opcional, usa sumiConfig.modelUrl por defecto
    onStatus: (event) => console.log(event),
});

await sumi.load();          // monta escena y carga GLB (o placeholder si falla)
sumi.playAnimation('idle'); // reproduce un clip por nombre (case-insensitive)
sumi.stop();                // pausa el render loop
sumi.start();               // lo reanuda
sumi.destroy();             // libera geometrías, materiales, renderer y observers
```

### Widget con estados

```js
import { SumiWidget } from './resources/js/sumi/interface/SumiWidget.js';

const widget = new SumiWidget({ container: '#sumi-container' });
await widget.mount();
widget.setState('thinking'); // dispara la animación asociada al estado
```

### Estados válidos

`idle`, `greeting`, `thinking`, `success`, `warning`, `sleeping`, `curious`, `happy`.
Cualquier otro valor lanza `Error: Estado SUMI no válido`. Ver [animation/states.md](./animation/states.md).

### Eventos de `onStatus`

| Evento | Significado |
|---|---|
| `{ type: 'model-loaded', placeholder: false }` | El GLB oficial cargó correctamente |
| `{ type: 'placeholder', message, error }` | No se encontró el GLB; se muestra el placeholder |

## 7. Pipeline del modelo 3D

El avatar base v0.1 se genera de forma reproducible con Blender headless:

```bash
blender -b -P tools/blender/build_sumi.py
```

El script construye malla, materiales PBR, UVs, rig, shape keys y clips, y exporta a `public/models/sumi/base/sumi.glb`. Especificación completa en [character/produccion-avatar.md](./character/produccion-avatar.md).

Para reemplazarlo por el modelo esculpido a mano:

1. Modelar y riggear SUMI en Blender respetando la identidad oficial ([character/identity.md](./character/identity.md)) y la lámina de concepto ([character/concept/sumi-model-sheet.png](./character/concept/sumi-model-sheet.png)).
2. Conservar los **nombres estables** de clips (`idle`, `curious`, `thinking`, …) y de shape keys (`blink_L`, `viseme_aa`, …).
3. Exportar como GLB (glTF binario) con animaciones incluidas y sustituir el archivo.
4. Recargar la preview: el motor registra los clips en `AnimationMixer` automáticamente.

**No** colocar imágenes 2D renombradas como modelos. Ver [public/models/sumi/README.md](../public/models/sumi/README.md).

## 8. Principios de arquitectura (resumen)

Ver [architecture/overview.md](./architecture/overview.md) e [integration/alpha-erp.md](./integration/alpha-erp.md):

1. SUMI funciona de forma independiente de Alpha ERP.
2. UI 3D y núcleo de inteligencia desacoplados.
3. Integración futura por API REST autenticada sobre HTTPS.
4. El backend autoriza cada herramienta por usuario, empresa, sede y almacén.
5. La IA **no** tiene acceso SQL directo; solo herramientas de negocio explícitas.
6. Acciones sensibles requieren confirmación, validación y auditoría en el backend.
7. Los secretos viven exclusivamente en el backend.

## 9. Solución de problemas

| Problema | Causa probable | Solución |
|---|---|---|
| Pantalla negra y error `Failed to resolve module specifier "three"` | Falta el import map o `node_modules` | Ejecutar `npm install`; verificar el bloque `importmap` de `index.html` |
| Siempre aparece el placeholder | Falta `public/models/sumi/base/sumi.glb` | Regenerarlo con `blender -b -P tools/blender/build_sumi.py` |
| `playAnimation` devuelve `false` | El clip no existe con ese nombre en el GLB | Revisar nombres de clips en Blender (deben coincidir con los estados) |
| `Error: No se encontró el contenedor de SUMI` | El selector no coincide con ningún elemento | Verificar que el contenedor exista antes de instanciar el motor |
| Canvas no se adapta al redimensionar | Contenedor sin dimensiones | Dar `width`/`height` al contenedor; el motor usa `ResizeObserver` |

## 10. Próximos hitos

1. Crear el esqueleto Laravel local.
2. Integrar el modelo oficial `sumi.glb` con rig y clips.
3. Conectar la máquina de estados a las animaciones reales.
4. Construir el widget flotante y el chat.
5. Preparar la API para el núcleo de IA y la integración con Alpha ERP.
