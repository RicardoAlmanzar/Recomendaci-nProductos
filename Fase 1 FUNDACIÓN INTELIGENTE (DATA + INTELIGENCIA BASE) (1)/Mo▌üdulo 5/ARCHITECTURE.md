# GJS Recommendation Engine V5 - Architecture

## Capas

### 1. Experience Layer
- Admin UI estática servida por Express
- API REST protegida por JWT y RBAC

### 2. Decision Layer
- RecommendationService
- FeatureEngine
- Campaign scoring
- Experiment allocation

### 3. Governance Layer
- AuditService
- SchedulerService
- AuthService
- DashboardService

### 4. Intelligence Persistence Layer
- Feature snapshots
- Training runs
- Model registry
- Feedback events

### 5. Integration Layer
- ERPConnector
- CRMConnector
- WhatsAppConnector
- ConnectorService central

## Flujo de recomendación V5
1. Cliente llega por canal
2. Se cargan contexto y features
3. Se evalúan reglas activas y campañas
4. Se asigna variante de experimento si existe
5. Se rankean productos
6. Se registra recomendación servida
7. Se envía a canal o UI
8. Se registra feedback y audit trail

## Flujo de gobierno operativo
1. Admin crea campaña / regla / experimento
2. Acción queda registrada en auditoría
3. Scheduler puede ejecutar jobs de sincronización o refresh
4. Pipeline ML persiste snapshots y corridas
5. Dashboard consume métricas agregadas

## Lista de artefactos V5
- API REST enterprise
- Admin UI base
- SQL v5
- contratos de integración
- repositorios de auditoría, experimentos y ML
- scheduler operativo
