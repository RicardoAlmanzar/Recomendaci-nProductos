# Arquitectura base del módulo MVP

## Qué hace este módulo
Este módulo recibe un `customerId`, busca su historial y devuelve productos recomendados con score y motivos explicables.

## Flujo
1. API recibe solicitud
2. Valida payload
3. Busca cliente
4. Lee historial de compras
5. Aplica reglas de afinidad
6. Aplica boosts por margen y prioridad estratégica
7. Ordena y devuelve recomendaciones
8. En siguiente fase registra feedback y aprende

## Fórmula base de score
Score total =
- afinidad por categoría comprada
- boost por margen
- boost por prioridad estratégica

## Razones explicables
Cada recomendación devuelve `reasonCodes` como:
- `CROSS_SELL_RULE`
- `BASKET_EXPANSION`
- `HIGH_MARGIN`
- `STRATEGIC_PRIORITY`

## Cómo evoluciona a producción
- PostgreSQL real
- Event bus
- Inventario real
- Margen neto por cliente o canal
- Restricciones de crédito
- Reglas por vertical de negocio
- Modelo ML adicional sobre datos históricos
