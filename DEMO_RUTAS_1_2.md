# Demo de Routes 1 y 2

Esta demo reproduce el flujo básico de la API actual:

- Route 1: `GET /customers` y `GET /customers/{customer_id}`
- Route 2: `POST /recommendations`

## Ejecución

1. Activa el entorno virtual.
2. Ejecuta:

```powershell
py -3 demo_routes.py
```

## Qué muestra

- La lista de clientes cargados por semilla.
- El detalle de un cliente específico.
- Las recomendaciones generadas para ese cliente.

## Nota

La demo usa los datos cargados por `seed.py`. Si la base de datos ya tiene registros, la salida puede variar ligeramente porque el contenido es persistente.
