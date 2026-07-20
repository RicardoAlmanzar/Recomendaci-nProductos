# GJS Recommendation Engine V5

Base empresarial avanzada del motor de recomendación GJS.

## Qué agrega sobre la V4
- Panel web administrativo inicial servido por Express (`/admin`)
- Scheduler de campañas y jobs operativos
- Auditoría de acciones administrativas y operativas
- Framework de A/B testing para estrategias de recomendación
- Persistencia para pipeline ML (`feature_snapshots`, `model_registry`, `training_runs`)
- Endpoints para conectores empresariales (ERP / CRM / WhatsApp) listos para implementación real

## Módulos principales
1. **API Core**: recomendaciones, eventos, feedback
2. **Admin UI**: dashboard, campañas, auditoría, experimentos
3. **Scheduler**: ejecución manual y listado de jobs
4. **Audit Layer**: trazabilidad de acciones críticas
5. **Experiment Layer**: experimentos A/B por canal, ciudad o segmento
6. **ML Persistence Layer**: snapshots de features, registro de modelos y corridas de entrenamiento
7. **Enterprise Connectors**: contratos y stubs para ERP / CRM / WhatsApp

## Flujo rápido
1. Ejecutar `sql/001_schema_v5.sql`
2. Crear `.env` con las variables base
3. `npm install`
4. `npm run dev`
5. Login con `POST /api/auth/login` usando `admin@gjs.local`
6. Abrir `http://localhost:3000/admin`

## Endpoints nuevos
### UI
- `GET /admin`
- `GET /admin/app.js`
- `GET /admin/styles.css`

### Enterprise Admin
- `GET /api/admin/audit`
- `GET /api/admin/experiments`
- `POST /api/admin/experiments`
- `GET /api/admin/scheduler/jobs`
- `POST /api/admin/scheduler/run`
- `GET /api/admin/ml/models`
- `POST /api/admin/ml/feature-snapshots`
- `POST /api/admin/ml/training-runs`

### Connectors
- `GET /api/connectors/status`
- `POST /api/connectors/sync/customer/:customerId`
- `POST /api/connectors/whatsapp/recommendations/:customerId`

## Credenciales semilla
```json
{
  "email": "admin@gjs.local"
}
```

## Nota técnica
Esta V5 deja la arquitectura lista para que el equipo conecte servicios reales. Los conectores incluidos son stubs seguros y auditables; el propósito es acelerar la integración con SIM ERP, CRM maestro y WhatsApp Business.
