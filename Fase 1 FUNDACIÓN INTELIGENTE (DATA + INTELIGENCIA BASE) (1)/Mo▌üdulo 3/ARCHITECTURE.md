# Arquitectura V3

## Capas

### 1. API Layer
Recibe solicitudes de recomendaciones, eventos, feedback y administración de reglas.

### 2. Recommendation Service
Coordina el flujo completo:
- sincronización ERP
- armado de contexto del cliente
- consulta de reglas
- consulta de inventario
- cálculo de features
- ranking final
- salida a CRM / WhatsApp

### 3. Feature Engine
Calcula:
- afinidad por categoría
- prioridad estratégica
- margen
- stock
- boost territorial
- boost por segmento
- boost por canal
- aprendizaje por feedback

### 4. Data Layer
Tablas principales:
- customers
- products
- inventory_snapshot
- sales_order_lines
- recommendation_rules
- ranking_boosts
- recommendation_events
- recommendation_feedback

### 5. Connectors
- ERPConnector
- CRMConnector
- WhatsAppConnector

## Diseño funcional
El motor todavía es híbrido:
- reglas explícitas
- scoring controlado
- señales operativas
- preparación para aprendizaje automático

## Resultado
Entrega recomendaciones explicables y operables, listas para integrarse con el ecosistema GJS.
