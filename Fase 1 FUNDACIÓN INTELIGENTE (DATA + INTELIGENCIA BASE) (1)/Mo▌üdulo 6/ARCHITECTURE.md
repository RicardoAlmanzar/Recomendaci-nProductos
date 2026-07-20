# ARCHITECTURE — GJS Recommendation Engine V6

## Principio rector
V6 deja de ser un motor aislado y pasa a ser una plataforma híbrida de recomendación.

## Capas
- API Layer
- Core Recommendation Layer
- Queue Layer
- Worker Layer
- Connector Layer
- Cache Layer
- Observability Layer

## Modelo híbrido
### Paraíso.do
- sellers múltiples
- contexto por tenant
- campañas y catálogos por vendedor
- recomendaciones por marketplace channel

### GJS Core
- clientes B2B
- recomendaciones para ventas directas
- integración con CRM y WhatsApp
- sincronización con ERP / inventario / órdenes

## Flujo principal
1. Entra evento o solicitud
2. Se valida tenant / user / canal
3. Se construye contexto
4. Se consulta cache
5. Si no existe, se calcula recomendación
6. Se aplican reglas, features, campañas, inventario y restricciones
7. Se registra serving log
8. Se retorna y/o se envía a cola para canal correspondiente
