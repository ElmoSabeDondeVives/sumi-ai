# Integración futura con Alpha ERP

SUMI debe seguir funcionando aunque Alpha ERP no esté disponible.

La integración será mediante API REST autenticada sobre HTTPS. Alpha conserva la autoridad sobre datos operativos y permisos. SUMI solicitará información a través de endpoints/herramientas explícitos y recibirá únicamente los datos permitidos para la sesión.

No conectar el modelo de IA directamente a la base de datos. No permitir que una instrucción conversacional omita autorización, validación, auditoría o confirmación de operaciones sensibles.
