# Arquitectura V2

## Capas

### 1. HTTP Layer
Recibe requests, valida payloads y responde.

### 2. Service Layer
Orquesta el flujo de recomendación y de captura de eventos.

### 3. Repository Layer
Lee y escribe en PostgreSQL.

### 4. Engine Layer
Aplica scoring híbrido:
- afinidad entre categorías
- prioridad estratégica
- margen
- inventario disponible
- señales recientes por eventos

### 5. Integration Layer
Adaptadores listos para:
- ERP
- CRM
- Marketplace
- WhatsApp Commerce

## Entrada mínima al motor
- historial de compras
- catálogo activo
- stock disponible
- reglas de afinidad
- eventos recientes

## Salida
- productos recomendados
- score total
- reason codes
- contexto resumido del cliente

## Siguiente versión recomendada
- feature store
- entrenamiento ML
- ranking por segmento/ciudad/canal
- feedback loop de aceptación/rechazo
- colas de eventos (Kafka / SQS / PubSub)
