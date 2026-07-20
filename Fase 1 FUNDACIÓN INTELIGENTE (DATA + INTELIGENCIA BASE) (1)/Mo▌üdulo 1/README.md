# GJS Recommendation Engine - MVP

Módulo base del motor de recomendación para el ecosistema GJS.

## Objetivo del MVP
Generar recomendaciones explicables para clientes B2B a partir de:
- historial de compras
- reglas de negocio
- afinidad entre productos
- margen
- prioridad estratégica

## Caso inicial GJS
Ejemplo:
- cliente compra **fundas plásticas**
- el motor recomienda **cajas**, **etiquetas** y **papelería**

## Stack sugerido
- **Node.js + TypeScript**
- **Fastify** para API
- **PostgreSQL** para datos persistentes
- **Redis** opcional para cache futura

## Cómo correrlo
```bash
npm install
npm run dev
```

## Endpoint principal
`POST /recommendations`

### Payload ejemplo
```json
{
  "customerId": "CUST-001",
  "limit": 5,
  "context": {
    "channel": "sales_rep",
    "businessType": "pharmacy",
    "city": "Santiago"
  }
}
```

## Respuesta ejemplo
```json
{
  "customerId": "CUST-001",
  "generatedAt": "2026-04-14T00:00:00.000Z",
  "recommendations": [
    {
      "productId": "BOX-001",
      "sku": "BOX-PIZZA-12",
      "name": "Caja 12 pulgadas",
      "score": 0.91,
      "reasonCodes": ["CROSS_SELL_RULE", "HIGH_MARGIN", "STRATEGIC_PRIORITY"]
    }
  ]
}
```

## Qué incluye este MVP
1. Modelo de dominio base
2. Reglas de recomendación explicables
3. Scoring híbrido
4. API lista para conectar con frontend/admin
5. SQL inicial de tablas maestras
6. Pruebas unitarias del motor

## Próxima expansión sugerida
- eventos en tiempo real
- retroalimentación de vendedores
- recomendaciones por vertical
- modelo ML complementario
- restricción por inventario real
- conexión con ERP / CRM / Paraíso.do / WhatsApp
