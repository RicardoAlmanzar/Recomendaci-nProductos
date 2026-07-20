# ARCHITECTURE — GJS Recommendation Engine V7

## Objetivo
Convertir la fundación híbrida V6 en una base productiva más robusta.

## Nuevos bloques
- Request tracing básico
- Error middleware
- Retry policy
- Dead-letter queue conceptual
- Health checks ampliados
- Configuración para conectores reales

## Flujo
1. entra request
2. se genera requestId
3. se valida auth / payload
4. se procesa o se encola job
5. si falla, se reintenta
6. si excede reintentos, va a dead-letter queue
7. se registran logs y serving logs
