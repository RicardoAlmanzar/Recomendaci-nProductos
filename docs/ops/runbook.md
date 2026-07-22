# Runbook Operativo - Recommendation Engine

## Despliegue Local / Staging
Para levantar la plataforma en modo desarrollo o staging de manera aislada:
```bash
docker-compose up --build -d
```

## Validación de Salud
Verificar que el motor está levantado:
```bash
curl http://localhost:8000/health
```
Verificar que la base de datos está conectada:
```bash
curl http://localhost:8000/readiness
```

## Variables de Entorno Clave
* `SUPABASE_DATABASE_URL`: URL de conexión a la base de datos Postgres (o Supabase).
* `JWT_SECRET`: Secreto para firma y validación de tokens JWT.
* `ALLOWED_ORIGINS`: Lista separada por comas de orígenes permitidos para CORS (ej: `https://app.com,http://localhost:3000`).

## Operaciones Comunes
* **Sincronización de Catálogo**: `POST /admin/integrations/sync/catalog`
* **Ver logs de integración**: `GET /admin/integrations/status` o revisando la tabla `integration_logs`.
* **Revisión de Auditoría**: `GET /admin/audit` para revisar las acciones de administradores.
