# GJS Recommendation Engine V8 — Integration Ready

V8 se enfoca en el paso 8 real: **integración**.

## Qué trae
- clientes HTTP listos para ERP / CRM / WhatsApp
- servicios de sincronización de catálogo, clientes e inventario
- endpoints webhook para entrada de eventos desde sistemas externos
- firma simple para proteger webhooks
- cola dedicada a webhooks e integraciones
- tablas SQL para integraciones, sync logs y mapeos externos
- estructura para convertir IDs externos en IDs internos

## Objetivo
Que el motor deje de vivir aislado y empiece a conversar con:
- SIM ERP
- CRM maestro GJS
- WhatsApp Business API
- catálogos e inventarios reales

## Instalación
```bash
npm install
cp .env.example .env
# ejecutar sql/001_schema_v8.sql
npm run dev
```

## Scripts
```bash
npm run worker:queue
npm run worker:sync
npm run worker:ml
npm run worker:webhooks
npm run test:smoke
```

## Endpoints nuevos
- `POST /api/webhooks/erp/events`
- `POST /api/webhooks/crm/events`
- `POST /api/webhooks/whatsapp/events`
- `POST /api/admin/integrations/sync/catalog`
- `POST /api/admin/integrations/sync/customers`
- `POST /api/admin/integrations/sync/inventory`
- `GET /api/admin/integrations/status`
- `GET /api/admin/integrations/logs`

## Nota
Esta versión deja lista la estructura, pero no consume tus credenciales reales ni tus contratos API reales.
El equipo técnico debe mapear los endpoints exactos de SIM ERP, CRM y WhatsApp Business.
