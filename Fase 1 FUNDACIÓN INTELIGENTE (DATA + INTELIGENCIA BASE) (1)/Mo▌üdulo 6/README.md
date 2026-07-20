# GJS Recommendation Engine V6 — Hybrid Enterprise Foundation

V6 está diseñada con enfoque híbrido:
- Marketplace first para Paraíso.do
- ERP / CRM / WhatsApp first para GJS Core y operaciones comerciales

## Qué incluye
- Arquitectura multi-tenant
- Cola de trabajos y productores/consumidores
- Workers separados por responsabilidad
- Scheduler para campañas, re-entrenamiento y sincronizaciones
- Observabilidad base con logs estructurados y métricas simples
- Cache layer Redis-ready
- Conectores listos para ERP / CRM / WhatsApp
- Endpoints admin + operativos
- SQL base de producción inicial

## Instalación
```bash
npm install
cp .env.example .env
# ejecutar sql/001_schema_v6.sql
npm run dev
```

## Endpoints principales
- GET /api/health
- GET /api/connectors/status
- POST /api/events
- POST /api/recommendations
- POST /api/admin/jobs/run
- GET /api/admin/metrics
- GET /api/admin/tenants
- POST /api/connectors/sync/customer/:customerId
- POST /api/connectors/whatsapp/recommendations/:customerId

## Workers
```bash
npm run worker:events
npm run worker:recommendations
npm run worker:ml
npm run worker:sync
npm run scheduler
```

## Diseño híbrido
### Bloque Marketplace
- tenant por seller / negocio
- ranking por ciudad, canal, vertical y vendedor
- campañas y ofertas por tenant

### Bloque GJS Core
- cliente 360
- recomendaciones para CRM
- sincronización ERP
- envío a WhatsApp comercial
- trazabilidad operativa y comercial
