# VALIDATION PLAN — REAL DATA GJS

## Objetivo
Validar que el motor produzca recomendaciones útiles, explicables y comercialmente relevantes.

## Capas de validación
1. técnica
2. funcional
3. integración
4. comercial

## Casos mínimos
- cliente que compra fundas → recomendar cajas / etiquetas
- cliente sin historial → priorizar productos estratégicos
- cliente por canal WhatsApp → recomendaciones rápidas
- inventario cero → no recomendar
- reglas inactivas → no impactan score

## Éxitos esperados
- recomendaciones coherentes
- reason codes consistentes
- response times aceptables
- sin errores críticos de integración
