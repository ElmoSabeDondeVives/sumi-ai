# SUMI AI

Proyecto independiente de la mascota virtual 3D SUMI para Alpha ERP.

> 📘 Guía completa de instalación y uso: [docs/INSTRUCTIVO.md](docs/INSTRUCTIVO.md)

## Estado del proyecto
MVP v0.1 con avatar 3D base integrado. El motor Three.js carga `public/models/sumi/base/sumi.glb`, generado proceduralmente con Blender (`tools/blender/build_sumi.py`): malla multi-material, texturas PBR 1K, rig, 20 blendshapes (parpadeo, cejas y 15 visemas) y clips `idle`, `curious` y `thinking`. El modelo esculpido a mano podrá reemplazar este base conservando nombres de clips y shape keys. Dirección de arte y especificación: `docs/character/produccion-avatar.md`.

## Stack objetivo
- Laravel (backend; fijar versión compatible con PHP 8.4 al crear el proyecto local)
- PHP 8.4 · MySQL 8
- Vite · JavaScript · Three.js
- Blender · GLB/glTF

## Inicio en Laragon
Este commit prepara los módulos frontend y documentación, no es un Laravel generado por Composer. En Laragon crea el proyecto Laravel compatible con PHP 8.4 y coloca estos archivos dentro de él, conservando `resources/`, `public/` y `docs/`. Después:
```bash
composer install
npm install
cp .env.example .env
php artisan key:generate
npm run dev
php artisan serve
```
Configura MySQL en `.env` y ejecuta `php artisan migrate` cuando existan migraciones.

## Arquitectura
- `resources/js/sumi/core`: motor Three.js, personaje y carga GLB.
- `resources/js/sumi/animation`: estados y expresiones.
- `resources/js/sumi/interface`: widget flotante y controles.
- `resources/js/sumi/config`: configuración central.
- `public/models/sumi`: modelos y texturas.
- `docs`: decisiones de arquitectura, personaje, animación e integración.

## Principios
1. SUMI funciona de forma independiente de Alpha ERP.
2. UI 3D y núcleo de inteligencia desacoplados.
3. Integración futura por API autenticada HTTPS.
4. El backend autoriza cada herramienta según usuario, empresa, sede y almacén.
5. La IA no tiene acceso SQL directo e ilimitado.
6. Acciones sensibles requieren confirmación y validación del backend.

## Próximos hitos
1. Crear el esqueleto Laravel local.
2. Esculpir el modelo artístico final en Blender (reemplazo del base procedural, mismos nombres de clips y shape keys).
3. Producir los clips restantes: greeting, success, warning, sleeping y happy.
4. Construir widget flotante y chat.
5. Preparar API para el núcleo de IA y Alpha ERP.
