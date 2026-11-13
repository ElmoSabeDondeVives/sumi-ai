# Arquitectura general

## Principio
SUMI se construye como aplicación independiente. La mascota 3D es una capa de presentación; la inteligencia y las integraciones viven en servicios separados.

## Capas
1. **Experiencia:** widget, chat, escena Three.js, estados y expresiones.
2. **Aplicación:** Laravel, autenticación, sesiones, preferencias y API.
3. **Inteligencia:** orquestador, contexto, especialidades y selección de herramientas.
4. **Integraciones:** conectores autorizados con Alpha ERP y otros servicios.

## Seguridad de integración
- Autenticar cada solicitud entre SUMI y Alpha.
- Autorizar por usuario, empresa, sede y almacén.
- Exponer herramientas de negocio explícitas, no consultas SQL arbitrarias.
- Registrar operaciones y exigir confirmación para acciones sensibles.
- Mantener secretos exclusivamente en el backend.
