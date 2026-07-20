# GJS Recommendation Engine V3

Versión operativa del motor de recomendación GJS, diseñada para conectar con ERP, CRM, Marketplace, eCommerce y WhatsApp.

## Lo que incluye
- API de recomendaciones explicables
- captura de eventos
- feedback loop
- reglas administrables por endpoint
- ranking por ciudad, segmento y canal
- estructura lista para entrenamiento futuro de ML
- conectores stub para ERP / CRM / WhatsApp
- SQL base con data semilla

## Endpoints
- `GET /api/health`
- `POST /api/recommendations`
- `POST /api/events`
- `POST /api/feedback`
- `GET /api/admin/rules`
- `POST /api/admin/rules`

## Ejemplo de recomendación
```json
{
  "customerId": "CUST-001",
  "channel": "marketplace",
  "limit": 5
}
```

## Ejemplo de feedback
```json
{
  "customerId": "CUST-001",
  "recommendedProductId": "PROD-003",
  "feedbackType": "purchased",
  "scoreDelta": 12,
  "metadata": {
    "source": "marketplace"
  }
}
```

## Flujo operativo
1. ERP sincroniza historial del cliente.
2. Se construye contexto de compra.
3. Se cargan reglas activas.
4. Se filtran productos con inventario.
5. Se aplican boosts por ciudad, segmento y canal.
6. Se suman señales de feedback.
7. Se devuelve ranking explicable.
8. El resultado queda listo para CRM o WhatsApp.

## Instalación
```bash
npm install
cp .env.example .env
# configurar DATABASE_URL
npm run dev
```

## Base de datos
Ejecuta el archivo:
- `sql/001_schema_v3.sql`

## Siguiente fase sugerida
- autenticación y permisos por roles
- tabla de campañas y ofertas comerciales
- conector real a SIM ERP / CRM GJS
- dashboard administrativo
- pipeline de entrenamiento real en Python o notebooks
