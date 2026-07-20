# GJS Recommendation Engine V2

Versión conectada a base de datos real, preparada para eventos, inventario y consumo desde ERP / CRM / Marketplace / WhatsApp.

## Qué incluye esta versión
- API `POST /recommendations`
- API `POST /events`
- API `GET /customers/:customerId/recommendation-context`
- conexión PostgreSQL mediante `pg`
- repositorios separados por responsabilidad
- scoring híbrido con filtros por inventario
- `reasonCodes` explicables
- tablas SQL para clientes, productos, inventario, compras, afinidades y eventos
- adaptadores listos para conectar ERP y CRM

## Variables de entorno
```bash
PORT=3000
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gjs_recommendation
MIN_STOCK_AVAILABLE=1
```

## Flujo sugerido
1. Crear base PostgreSQL.
2. Ejecutar `sql/001_schema_v2.sql`.
3. Ejecutar `npm install`.
4. Ejecutar `npm run dev`.
5. Probar `/health`, `/events`, `/recommendations`.

## Endpoints
### 1. Health
`GET /health`

### 2. Registrar evento
`POST /events`
```json
{
  "customerId": "CUST-001",
  "eventType": "product_view",
  "channel": "marketplace",
  "productId": "PROD-004",
  "metadata": {
    "sessionId": "abc-123"
  }
}
```

### 3. Obtener recomendaciones
`POST /recommendations`
```json
{
  "customerId": "CUST-001",
  "limit": 5,
  "channel": "sales_rep"
}
```

### 4. Contexto enriquecido del cliente
`GET /customers/CUST-001/recommendation-context`

## Notas de arquitectura
- Esta versión ya no usa mock data como fuente principal.
- El motor lee compras, inventario, afinidades y eventos desde PostgreSQL.
- ERP y CRM pueden empujar datos a través de adaptadores o integraciones batch/API.
