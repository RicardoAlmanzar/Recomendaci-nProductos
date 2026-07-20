# GJS Recommendation Engine V11 — Deployment + Real Validation Pack

V11 es el cierre del ciclo técnico principal.
Esta versión se enfoca en **despliegue**, **staging**, **go-live** y **validación real con datos GJS**.

## Qué trae
- pack completo para deployment
- Dockerfile base
- docker-compose para entorno local/staging
- checklist de staging
- checklist de producción
- runbook operativo
- plan de validación real
- matriz de calibración de scoring
- estructura de release notes
- endpoints de readiness y diagnostics
- dashboard administrativo
- scripts de validación

## Objetivo
Que el equipo ya no solo construya:
ahora puede **desplegar, validar y preparar salida real a producción**.

## Flujo recomendado
1. levantar entorno local/staging
2. ejecutar schema SQL
3. cargar data semilla / data controlada
4. correr smoke/security/validation tests
5. validar integraciones
6. calibrar scoring
7. aprobar checklist go-live
8. desplegar producción

## Scripts
```bash
npm install
cp .env.example .env
npm run build
npm run test:smoke
npm run test:security
npm run test:validation
```
