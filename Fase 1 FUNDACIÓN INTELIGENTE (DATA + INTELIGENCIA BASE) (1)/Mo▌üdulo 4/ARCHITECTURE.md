# GJS Recommendation Engine V4 - Arquitectura

## Capas
1. API protegida con JWT
2. Middleware de autorización por roles
3. Servicio de recomendaciones
4. Repositorios de datos (clientes, productos, reglas, campañas, dashboard)
5. Conectores externos (ERP, CRM, WhatsApp)
6. Base PostgreSQL con tablas operativas y administrativas

## Novedades V4
### Seguridad
- Login por email para entorno inicial
- JWT firmado con `JWT_SECRET`
- RBAC para rutas administrativas

### Operación comercial
- Campañas por canal
- Ofertas por producto con `extra_score`
- Oferta activa impacta el ranking final

### Gobierno y supervisión
- Dashboard con KPIs básicos
- Registro de eventos `recommendation_served`
- Preparado para auditoría y trazabilidad

## Modelo de decisión
`score final = afinidad + estrategia + margen + inventario + ranking territorial/canal + feedback + offerScore`

## Integración futura
- Identity Provider corporativo
- Dashboard React/Next.js
- Scheduler para campañas
- Experimentación A/B
- Model serving de ML
