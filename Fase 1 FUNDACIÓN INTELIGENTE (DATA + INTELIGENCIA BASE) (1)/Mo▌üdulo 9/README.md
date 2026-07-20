# GJS Recommendation Engine V9 — Dashboard + Real Operations

V9 mueve el proyecto desde integración técnica hacia **operación humana real**.

## Qué trae
- dashboard administrativo base en HTML server-rendered
- vista de métricas operativas
- vista de tenants
- vista de logs de integración
- vista de recomendaciones servidas
- vista de reglas activas
- vista de campañas
- vista de jobs y dead letters
- acciones operativas desde API admin
- estructura lista para evolucionar a frontend React/Vue más adelante

## Objetivo
Que el equipo pueda:
- ver qué está pasando
- operar el sistema
- monitorear integraciones
- revisar recomendaciones
- detectar errores
- lanzar syncs y jobs

## Instalación
```bash
npm install
cp .env.example .env
# ejecutar sql/001_schema_v9.sql
npm run dev
```

## Endpoints clave
- `GET /admin`
- `GET /admin/metrics`
- `GET /admin/tenants`
- `GET /admin/integrations/logs`
- `GET /admin/recommendations/logs`
- `GET /admin/rules`
- `GET /admin/campaigns`
- `GET /admin/jobs`
- `GET /admin/dead-letters`
- `POST /api/admin/integrations/sync/catalog`
- `POST /api/admin/integrations/sync/customers`
- `POST /api/admin/integrations/sync/inventory`

## Nota
Esta V9 trae un dashboard base funcional desde backend.
No es todavía el frontend definitivo de producción, pero sí una capa real de operación.
