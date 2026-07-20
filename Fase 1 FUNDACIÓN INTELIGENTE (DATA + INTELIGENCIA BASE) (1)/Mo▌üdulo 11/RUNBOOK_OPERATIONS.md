# RUNBOOK — OPERACIONES

## Si health falla
1. revisar proceso API
2. revisar logs
3. revisar variables
4. revisar acceso DB

## Si readiness falla
1. validar PostgreSQL
2. validar Redis
3. validar conectividad de red
4. revisar pool de conexiones

## Si aparecen dead letters
1. revisar queue_name
2. inspeccionar failure_reason
3. corregir causa
4. reprocesar manualmente si aplica

## Si scoring da resultados pobres
1. revisar reglas activas
2. revisar categorías base
3. revisar data de eventos
4. recalibrar weights
5. validar con equipo comercial
