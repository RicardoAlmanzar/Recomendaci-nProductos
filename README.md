Principios que guían este plan
Antes de los módulos, tres principios no negociables. Si los rompes, el plan se cae:
1. El schema de eventos es sagrado. Es lo único que vas a lamentar si lo haces mal, porque cambiarlo después implica perder o migrar datos históricos. Todo lo demás se puede refactorizar.
2. Separación candidatos → ranking desde el día uno. Aunque hoy ambos pasos sean reglas tontas, la interfaz entre ellos tiene que existir. Esto te permite cambiar el ranking a ML sin tocar nada más.
3. Logguea ahora, modela después. No necesitas ML en mes 1. Necesitas datos limpios para entrenarlo en mes 6. La trampa más común es pasarse meses con un modelo malo en lugar de acumular datos buenos.
Los 11 módulos, priorizados realmente
Te los agrupo en tres tiers según qué hacer con cada uno en los próximos 6-12 meses:
TIER 1 — Construir bien desde ya (meses 1-3)
Estos son los que si los haces mal o los pospones, todo lo demás se rompe.

Módulo 1: Catálogo ✅

Modelo de datos con: producto, variantes, categoría jerárquica (no plana), atributos en JSONB para flexibilidad, multi-vendor desde el inicio (aunque arranques con uno solo).
Por qué ahora: cambiar el modelo del catálogo después es brutal. Si arrancas con tabla plana de productos, en mes 8 vas a estar reescribiendo medio sistema.
Tu estado actual: tienes 15 productos planos. Necesitas rediseñar.

Módulo 2: Identidad y sesiones ✅

user_id (logueado) + session_id (anónimo persistente vía cookie/localStorage). Lógica de merge cuando un anónimo se loguea.
Por qué ahora: el 60-80% del tracking de un marketplace es de usuarios anónimos. Si solo trackeas logueados, perdiste la mayoría de la señal.
Tu estado actual: probablemente solo tienes usuario logueado. Hay trabajo aquí.

Módulo 3: Event tracking

Tabla de eventos con schema versionado: event_id, event_type, user_id, session_id, entity_type, entity_id, properties (JSONB), timestamp, schema_version.
Eventos mínimos a capturar: product_view, product_click, search, add_to_cart, purchase, recommendation_shown, recommendation_clicked.
Por qué ahora: literalmente el activo más valioso. Sin esto no hay ML, no hay métricas, no hay A/B test.
Tu estado actual: parcial/faltante. Esto es lo más urgente.

Módulo 11: Servicio y entrega (API)

Endpoint /recommendations con contratos claros: contexto de entrada (user, session, page_type, slot), respuesta estructurada (lista de items + metadata para tracking).
Caching desde el inicio (Redis o el cache de Supabase).
Por qué ahora: define cómo el frontend consume recomendaciones. Cambiar el contrato después rompe a todos los consumidores.

TIER 2 — Interfaz mínima ahora, profundizar después (meses 3-6)
Estos los construyes "feos pero funcionales" con la interfaz correcta. Los vas a reemplazar internamente sin que nadie afuera se entere.
Módulo 4: Generación de candidatos

Hoy: reglas + popularidad + co-compra básica (productos comprados juntos).
Interfaz: función get_candidates(context) → List[product_id].
Después: agregas similitud por embeddings, candidatos por categoría, etc. Sin tocar el ranker.

Módulo 5: Ranking

Hoy: tu motor actual de score con boosts por margen y prioridad.
Interfaz: función rank(candidates, context) → ordered_list.
Después: lo reemplazas por un modelo learning-to-rank cuando tengas datos suficientes (típicamente 50k-100k eventos de interacción).

Módulo 7: Cold-start

Hoy: para usuario nuevo → top productos populares por categoría. Para producto nuevo → recomendarlo en su categoría con boost temporal.
Es simple pero explícito. La trampa es no pensarlo y que tu sistema no recomiende nada a usuarios nuevos.

Módulo 8: Feedback loop

Hoy: solo capturas implícito (clicks en recomendaciones, gracias al módulo 3).
Después: agregas explícito (like/hide/no me interesa) cuando el producto lo justifique.
La clave: que cada recomendación servida tenga un recommendation_id que puedas correlacionar con el evento de click. Sin esto no puedes medir CTR.

TIER 3 — Stub o postergar (meses 6-12+)
Estos los mencionas en la documentación pero no los construyes ahora. Construirlos prematuro es desperdicio.
Módulo 6: Contexto y personalización avanzada

Hora del día, dispositivo, ubicación geográfica, historial reciente vs largo plazo.
Por qué postergar: requiere volumen de datos que no vas a tener en los primeros meses. Implementarlo sin datos es teatro.

Módulo 9: Evaluación y métricas

Stub mínimo ahora: dashboard simple con CTR de recomendaciones, conversión, productos más recomendados.
Postergar: NDCG, recall@k, diversidad, cobertura. Esas métricas tienen sentido cuando tienes un modelo real que evaluar.

Módulo 10: A/B testing

Stub: capacidad de servir dos versiones del ranker basado en hash del user_id. Eso es todo.
Postergar: framework completo de experimentación con significancia estadística, guardrails, etc. Eso es trabajo de meses 9-12 cuando ya tengas tráfico.
