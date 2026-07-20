# DEPLOYMENT NOTES — V11

## Artefactos
- Dockerfile
- docker-compose.yml
- .env.example
- SQL base
- runbooks
- validation plan

## Orden sugerido
1. crear infraestructura
2. inyectar secretos
3. levantar PostgreSQL / Redis
4. desplegar API
5. desplegar workers
6. validar readiness
7. validar dashboard
8. validar integraciones
9. ejecutar plan de scoring
10. habilitar producción

## Recomendación
Usar staging como entorno obligatorio antes de producción.
Nunca probar integración crítica directamente primero en producción.
