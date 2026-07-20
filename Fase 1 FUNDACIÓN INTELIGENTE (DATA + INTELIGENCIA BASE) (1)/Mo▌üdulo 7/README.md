# GJS Recommendation Engine V7 — Production-Oriented Foundation

V7 lleva la base híbrida a una estructura más cercana a operación productiva.

## Qué agrega sobre V6
- conectores reales por configuración (`ERP_BASE_URL`, `CRM_BASE_URL`, `WHATSAPP_BASE_URL`)
- política de reintentos para jobs
- dead-letter queue lógica
- middleware de request id
- manejo centralizado de errores
- health checks ampliados
- smoke test base
- estructura preparada para endurecimiento de seguridad y observabilidad

## Instalación
```bash
npm install
cp .env.example .env
# ejecutar sql/001_schema_v7.sql
npm run dev
```

## Scripts
```bash
npm run worker:queue
npm run worker:sync
npm run worker:ml
npm run test:smoke
```

## Siguiente foco
Después de V7, el trabajo pendiente ya no es “inventar” arquitectura.
El trabajo pendiente es:
1. conexión real con tus sistemas
2. hardening de producción
3. frontend operativo definitivo
4. despliegue
5. validación real con datos GJS
