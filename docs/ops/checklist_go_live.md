# Go-Live Checklist

## 1. Staging
- [ ] Variables de entorno (db, jwt, cors) configuradas para entorno staging.
- [ ] Base de datos migrada (tablas SQLModel creadas automáticamente).
- [ ] Datos semilla y de control cargados (`python seed.py` o similar).
- [ ] Ejecución exitosa de `GET /health` y `GET /readiness`.
- [ ] Webhooks de prueba disparados con respuesta `200 OK`.
- [ ] Endpoint de diagnóstico (`GET /admin/diagnostics`) muestra `connected` en todo.

## 2. Producción
- [ ] Repetir pasos de staging en el entorno productivo.
- [ ] Configurar CORS (`ALLOWED_ORIGINS`) exclusivamente a los dominios productivos.
- [ ] Rotación de `JWT_SECRET` (No usar el de staging).
- [ ] Monitoreo (p.ej. Datadog / Prometheus) apuntando a `/health`.
- [ ] Habilitar SSL (Terminación TLS en Load Balancer / Nginx).
- [ ] Revisión del `GET /admin/audit` post-despliegue tras ejecutar primeras acciones.
