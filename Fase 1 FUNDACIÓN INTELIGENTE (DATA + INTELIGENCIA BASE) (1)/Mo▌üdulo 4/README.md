# GJS Recommendation Engine V4

Versión empresarial del motor de recomendación GJS.

## Qué agrega sobre la V3
- Autenticación JWT
- Roles y permisos (RBAC)
- Dashboard administrativo
- Campañas y ofertas comerciales
- Registro automático de recomendaciones servidas
- Base lista para conectar UI administrativa y analítica

## Roles
- `super_admin`
- `admin`
- `analyst`
- `operator`
- `viewer`

## Flujo rápido
1. Ejecutar SQL `sql/001_schema_v4.sql`
2. Configurar `.env`
3. `npm install`
4. `npm run dev`
5. Hacer login con `POST /api/auth/login` usando `admin@gjs.local`
6. Usar el token en `Authorization: Bearer <token>`

## Endpoints
### Públicos
- `GET /api/health`
- `POST /api/auth/login`

### Protegidos
- `POST /api/recommendations`
- `POST /api/events`
- `POST /api/feedback`
- `GET /api/admin/dashboard`
- `GET /api/admin/rules`
- `POST /api/admin/rules`
- `GET /api/admin/campaigns`
- `POST /api/admin/campaigns`
- `GET /api/admin/offers`
- `POST /api/admin/offers`

## Ejemplo login
```json
POST /api/auth/login
{
  "email": "admin@gjs.local"
}
```

## Ejemplo recommendations
```json
POST /api/recommendations
Authorization: Bearer <token>
{
  "customerId": "CUST-001",
  "channel": "whatsapp",
  "limit": 5
}
```

## Siguiente paso recomendado
- Conectar identity provider real
- Crear panel web admin
- Conectar campañas a CRM y WhatsApp reales
- Crear pipeline de features persistentes y entrenamiento ML
