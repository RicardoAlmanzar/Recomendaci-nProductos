# ARCHITECTURE — GJS Recommendation Engine V8

## Enfoque
V8 convierte la plataforma en un hub de integración.

## Bloques nuevos
- Integration Clients
- External ID Mapping
- Sync Logs
- Webhook Ingestion
- Integration Status Layer

## Flujo de integración
1. sistema externo envía evento o se programa sync
2. se valida firma / credenciales
3. se transforma payload externo
4. se mapea external_id → internal_id
5. se registra sync log
6. se actualiza catálogo, inventario, clientes o eventos
7. se publica job si aplica
8. el motor queda listo para recomendar con datos reales

## Sistemas objetivo
### ERP
- clientes
- productos
- inventario
- órdenes
- precios

### CRM
- leads
- clientes
- actividades comerciales
- oportunidades

### WhatsApp
- mensajes entrantes
- clics / respuestas
- envío de recomendaciones
