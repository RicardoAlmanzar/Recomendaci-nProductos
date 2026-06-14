// ========== STATE ==========
const state = {
  users: [],
  selectedUser: null,
  lastRecommendations: null,
  purchaseHistory: null,
  isSearchMode: false,
  activeSearchTerm: '',
  searchResults: [],
  searchRelatedRecommendations: null,
  searchRequestId: 0,
  shownRecommendationIds: new Set(),
  clickedProductIds: new Set(),
  pendingFeedback: new Set(),
};

// CAMBIO VISUAL: Objeto elements actualizado con nuevos IDs de elementos
const elements = {};

function cacheElements() {
  console.log('🔄 Caching elements...');
  elements.apiBaseUrl = document.getElementById('apiBaseUrl');
  elements.debugToggle = document.getElementById('debugToggle');

  // CAMBIO VISUAL: Nuevos elementos del header
  elements.searchInput = document.getElementById('searchInput');
  elements.searchButton = document.getElementById('searchButton');
  elements.customerSelectorLabel = document.getElementById('customerSelectorLabel');
  elements.customerSelectorBusiness = document.getElementById('customerSelectorBusiness');
  elements.customerSelector = document.querySelector('.customer-selector');
  elements.customerDropdown = document.getElementById('customerDropdown');
  elements.customerDropdownList = document.getElementById('customerDropdownList');

  // CAMBIO VISUAL: Elementos del historial y recomendaciones adaptados
  elements.historyCount = document.getElementById('historyCount');
  elements.historyLoading = document.getElementById('historyLoading');
  elements.historyError = document.getElementById('historyError');
  elements.historyEmpty = document.getElementById('historyEmpty');
  elements.historyList = document.getElementById('historyList');

  elements.recommendationsTitle = document.getElementById('recommendationsTitle');
  elements.recommendationsCount = document.getElementById('recommendationsCount');
  elements.recommendationsLoading = document.getElementById('recommendationsLoading');
  elements.recommendationsError = document.getElementById('recommendationsError');
  elements.feedbackStatus = document.getElementById('feedbackStatus');
  elements.emptyRecommendations = document.getElementById('emptyRecommendations');
  elements.recommendationsGrid = document.getElementById('recommendationsGrid');
  elements.relatedRecommendationsBlock = document.getElementById('relatedRecommendationsBlock');
  elements.relatedRecommendationsCount = document.getElementById('relatedRecommendationsCount');
  elements.relatedRecommendationsEmpty = document.getElementById('relatedRecommendationsEmpty');
  elements.relatedRecommendationsGrid = document.getElementById('relatedRecommendationsGrid');

  // CAMBIO VISUAL: Elementos del footer
  elements.footerRecommendationId = document.getElementById('footerRecommendationId');
  elements.footerAlgoVersion = document.getElementById('footerAlgoVersion');
  elements.footerCacheStatus = document.getElementById('footerCacheStatus');

  // CAMBIO VISUAL: Debug panel
  elements.debugPanel = document.getElementById('debugPanel');
  elements.debugOutput = document.getElementById('debugOutput');
  elements.debugCloseBtn = document.getElementById('debugCloseBtn');

  console.log('✅ Elements cached. API URL:', elements.apiBaseUrl?.value || 'NOT FOUND');
}

function getApiBaseUrl() {
  return elements.apiBaseUrl.value.trim().replace(/\/$/, '');
}

// ========== UTILIDADES ==========
async function fetchJsonWithFallback(paths, options = {}) {
  let lastError = null;

  for (const path of paths) {
    try {
      const url = `${getApiBaseUrl()}${path}`;
      console.log(`📡 Fetching: ${url}`);

      // Add timeout
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });

      clearTimeout(timeout);

      if (!response.ok) {
        console.warn(`❌ Response ${response.status} for ${path}`);
        lastError = new Error(`Error ${response.status} en ${path}`);
        continue;
      }

      const data = await response.json();
      console.log(`✅ Got response from ${path}:`, data);
      return data;
    } catch (error) {
      console.error(`❌ Fetch error for ${path}:`, error);
      lastError = error;
    }
  }

  console.error(`❌ All requests failed. Last error:`, lastError);
  throw lastError || new Error('No se pudo obtener la respuesta.');
}

function setLoading(element, visible, message) {
  element.textContent = message || element.textContent;
  element.classList.toggle('hidden', !visible);
}

function setError(element, message) {
  element.textContent = message;
  element.classList.remove('hidden');
}

function clearError(element) {
  element.textContent = '';
  element.classList.add('hidden');
}

function setFeedbackStatus(message, tone = 'info') {
  elements.feedbackStatus.textContent = message;
  elements.feedbackStatus.className = `state-message feedback-state ${tone}`;
  elements.feedbackStatus.classList.remove('hidden');
}

function clearFeedbackStatus() {
  elements.feedbackStatus.textContent = '';
  elements.feedbackStatus.classList.add('hidden');
}

function formatNumber(value) {
  return Number(value || 0).toFixed(4);
}

function formatCurrency(value) {
  return new Intl.NumberFormat('es-DO', {
    style: 'currency',
    currency: 'DOP',
    maximumFractionDigits: 0,
  }).format(value || 0);
}

// CAMBIO VISUAL: Función para mapear categoría a ícono emoji
function getCategoryIcon(category) {
  const iconMap = {
    'packaging': '📦',
    'labels': '🏷️',
    'food_service': '🥤',
    'paper': '📄',
    'cleaning': '🧹',
    'protective': '🛡️',
  };
  return iconMap[category] || '🛒';
}

// CAMBIO VISUAL: Función para traducir reason codes
function translateReasonCode(code) {
  const translations = {
    'CROSS_SELL_RULE': 'Comprado junto',
    'HIGH_MARGIN': 'Alta rentabilidad',
    'STRATEGIC_PRIORITY': 'Destacado',
    'FEEDBACK_LIKED': 'Te gustó antes',
    'FEEDBACK_DISLIKED': 'No te gustó',
    'FEEDBACK_HIDDEN': 'Oculto',
    'FEEDBACK_NOT_INTERESTED': 'Sin interés',
    'SEARCH_MATCH': 'Resultado',
  };
  return translations[code] || code.toLowerCase();
}

// CAMBIO VISUAL: Función para determinar nivel de score
function getScoreLevel(score) {
  if (score >= 0.7) return 'high';
  if (score >= 0.4) return 'medium';
  return 'low';
}

// ========== RENDER: DROPDOWN DE CLIENTES ==========
// CAMBIO VISUAL: Nueva función para renderizar dropdown de clientes (reemplaza renderUsers)
function renderCustomerDropdown() {
  elements.customerDropdownList.innerHTML = '';

  if (!state.users.length) {
    elements.customerDropdownList.innerHTML = '<div class="customer-dropdown-item">No hay clientes cargados</div>';
    return;
  }

  state.users.forEach((user) => {
    const item = document.createElement('div');
    item.className = `customer-dropdown-item ${state.selectedUser?.customer_id === user.customer_id ? 'active' : ''}`;
    item.innerHTML = `
      <strong>${user.customer_id}</strong>
      <div style="font-size: 12px; color: #565959;">${user.business_type}</div>
    `;
    item.addEventListener('click', () => {
      selectUser(user.customer_id);
      elements.customerDropdown.classList.add('hidden');
    });
    elements.customerDropdownList.appendChild(item);
  });
}

// ========== RENDER: HISTORIAL ==========
// CAMBIO VISUAL: Rediseño para carousel horizontal
function renderHistory(historyPayload) {
  elements.historyList.innerHTML = '';

  const purchases = historyPayload?.purchases || [];
  if (!purchases.length) {
    elements.historyEmpty.classList.remove('hidden');
    elements.historyEmpty.textContent = 'Sin historial de compras.';
    elements.historyCount.textContent = 'Cargando...';
    return;
  }

  elements.historyEmpty.classList.add('hidden');
  elements.historyCount.textContent = `${purchases.length} compras recientes`;

  purchases.forEach((purchase) => {
    const item = document.createElement('div');
    item.className = 'history-item';
    const icon = getCategoryIcon(purchase.category);
    item.innerHTML = `
      <span class="history-item-icon">${icon}</span>
      <div class="history-item-name">${purchase.product_name || purchase.product_id}</div>
      <div class="history-item-meta">Cantidad: ${purchase.quantity}</div>
    `;
    elements.historyList.appendChild(item);
  });
}

// ========== RENDER: TARJETAS DE PRODUCTO ==========
function createProductCard(item, handlers = {}) {
  const card = document.createElement('article');
  card.className = 'product-card';

  const icon = getCategoryIcon(item.category);
  const scoreLevel = getScoreLevel(item.score);
  const scorePercent = Math.round(item.score * 100);

  const reasonsHtml = item.reason_codes && item.reason_codes.length
    ? item.reason_codes.map((code) => `<div class="reason-tag">${translateReasonCode(code)}</div>`).join('')
    : '';

  const feedbackButtonsHtml = handlers.showFeedback
    ? `<div class="feedback-buttons">
        <button class="btn-secondary btn-feedback" data-feedback="like" title="Me gusta">👍</button>
        <button class="btn-secondary btn-feedback" data-feedback="dislike" title="No me gusta">👎</button>
        <button class="btn-secondary btn-feedback btn-feedback-hide" data-feedback="hide" title="Ocultar">🚫</button>
      </div>`
    : '';

  card.innerHTML = `
    <div class="product-card-header">
      <div class="product-rank">${item.rank_position}</div>
      <span class="product-category-badge">${icon} ${item.category}</span>
      <h3 class="product-name">${item.name}</h3>
      <div class="product-score">Relevancia: ${scorePercent}%</div>
      <div class="score-bar">
        <div class="score-bar-fill ${scoreLevel}" style="width: ${scorePercent}%;"></div>
      </div>
      ${reasonsHtml ? `<div class="product-reasons">${reasonsHtml}</div>` : ''}
    </div>
    <div class="product-actions">
      <button class="btn-primary btn-view-product" data-product-id="${item.product_id}" data-rank="${item.rank_position}">
        Ver producto
      </button>
      ${feedbackButtonsHtml}
    </div>
  `;

  const viewBtn = card.querySelector('.btn-view-product');
  viewBtn.addEventListener('click', () => {
    if (handlers.onViewClick) {
      handlers.onViewClick(item);
    }
  });

  if (handlers.showFeedback) {
    const feedbackBtns = card.querySelectorAll('.btn-feedback');
    feedbackBtns.forEach((btn) => {
      btn.addEventListener('click', async () => {
        const feedbackType = btn.dataset.feedback;

        // Disable all feedback buttons on this card to prevent duplicates
        feedbackBtns.forEach((b) => {
          b.disabled = true;
          b.classList.remove('liked', 'disliked', 'hidden-feedback');
        });

        // Add active visual state to the clicked button
        const stateClassMap = { like: 'liked', dislike: 'disliked', hide: 'hidden-feedback' };
        btn.classList.add(stateClassMap[feedbackType] || feedbackType);

        await handlers.onFeedback(item, feedbackType);

        // If hiding, remove the card with animation and reload recommendations
        if (feedbackType === 'hide') {
          card.classList.add('card-hiding');
          card.addEventListener('animationend', () => {
            card.remove();
          }, { once: true });
          // Reload recommendations after a short delay so the hidden product is excluded
          setTimeout(() => loadRecommendations({ preserveFeedbackStatus: true }), 600);
        }
      });
    });
  }

  return card;
}

function renderRecommendationCards(container, payload, handlers = {}) {
  container.innerHTML = '';

  if (!payload || !payload.items || payload.items.length === 0) {
    return false;
  }

  payload.items.forEach((item) => {
    container.appendChild(createProductCard(item, {
      showFeedback: Boolean(handlers.onFeedback),
      onViewClick: handlers.onViewClick,
      onFeedback: handlers.onFeedback,
    }));
  });

  return true;
}

// ========== RENDER: RECOMENDACIONES ==========
// CAMBIO VISUAL: Rediseño completo para tarjetas estilo Amazon
function renderRecommendations(payload) {
  elements.recommendationsGrid.innerHTML = '';

  if (elements.debugOutput) {
    elements.debugOutput.textContent = JSON.stringify(payload, null, 2);
  }

  if (!payload || !payload.items || payload.items.length === 0) {
    elements.emptyRecommendations.classList.remove('hidden');
    elements.emptyRecommendations.textContent = 'Sin recomendaciones disponibles.';
    return;
  }

  elements.emptyRecommendations.classList.add('hidden');
  elements.recommendationsCount.textContent = `Mostrando ${payload.items.length} recomendaciones`;

  renderRecommendationCards(elements.recommendationsGrid, payload, {
    onViewClick: (item) => trackRecommendationClick(item, state.lastRecommendations),
    onFeedback: (item, feedbackType) => sendFeedback(item, feedbackType, state.lastRecommendations),
  });

  updateFooter(payload);
}

// CAMBIO VISUAL: Nueva función para actualizar footer
function updateFooter(payload) {
  if (payload && payload.recommendation_id) {
    const truncatedId = payload.recommendation_id.substring(0, 8) + '...';
    elements.footerRecommendationId.textContent = truncatedId;
    elements.footerAlgoVersion.textContent = payload.algo_version || '—';
    elements.footerCacheStatus.textContent = payload.cache_hit ? '✓ Caché' : '✗ Fresco';
  }
}

// ========== CARGA DE DATOS ==========
async function loadUsers() {
  clearError(elements.historyError);
  clearError(elements.recommendationsError);
  setLoading(elements.historyLoading, true, 'Cargando clientes...');

  try {
    state.users = await fetchJsonWithFallback(['/customers', '/users']);
    renderCustomerDropdown();

    if (state.users.length && !state.selectedUser) {
      await selectUser(state.users[0].customer_id);
    }
  } catch (error) {
    setError(elements.historyError, error.message || 'No se pudieron cargar los clientes.');
    elements.historyList.innerHTML = '';
  } finally {
    elements.historyLoading.classList.add('hidden');
  }
}

async function selectUser(userId) {
  const user = state.users.find((candidate) => candidate.customer_id === userId);
  if (!user) {
    return;
  }

  resetSearchState({ clearInput: true });

  state.selectedUser = user;
  state.lastRecommendations = null;
  state.purchaseHistory = null;
  state.shownRecommendationIds.clear();
  state.clickedProductIds.clear();
  state.pendingFeedback.clear();
  clearFeedbackStatus();

  elements.customerSelectorLabel.textContent = user.customer_id;
  elements.customerSelectorBusiness.textContent = user.business_type;

  renderCustomerDropdown();

  await loadHistory();
  await loadRecommendations();
}

async function loadHistory() {
  if (!state.selectedUser) {
    return;
  }

  clearError(elements.historyError);
  elements.historyEmpty.classList.add('hidden');
  elements.historyList.innerHTML = '';
  setLoading(elements.historyLoading, true, 'Cargando historial...');

  try {
    state.purchaseHistory = await fetchJsonWithFallback([
      `/customers/${state.selectedUser.customer_id}/history`,
      `/users/${state.selectedUser.customer_id}/history`,
    ]);
    renderHistory(state.purchaseHistory);
  } catch (error) {
    setError(elements.historyError, error.message || 'No se pudo cargar el historial.');
    elements.historyList.innerHTML = '';
  } finally {
    elements.historyLoading.classList.add('hidden');
  }
}

async function loadRecommendations(options = {}) {
  if (!state.selectedUser || state.isSearchMode) {
    return;
  }

  clearError(elements.recommendationsError);
  if (!options.preserveFeedbackStatus) {
    clearFeedbackStatus();
  }
  elements.emptyRecommendations.classList.add('hidden');
  elements.recommendationsGrid.innerHTML = '';
  setLoading(elements.recommendationsLoading, true, 'Cargando recomendaciones...');

  try {
    const response = await fetch(`${getApiBaseUrl()}/recommendations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        customer_id: state.selectedUser.customer_id,
        page_type: "homepage",
        slot: "hero",
        limit: 8,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      let message = `Error al cargar recomendaciones: ${response.status}`;
      if (errorData?.detail) {
        message = Array.isArray(errorData.detail)
          ? errorData.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ')
          : errorData.detail;
      }
      throw new Error(message);
    }

    state.lastRecommendations = await response.json();
    renderRecommendations(state.lastRecommendations);
    await trackRecommendationShown(state.lastRecommendations);
  } catch (error) {
    setError(elements.recommendationsError, error.message || 'No se pudieron cargar las recomendaciones.');
    elements.recommendationsGrid.innerHTML = '';
  } finally {
    elements.recommendationsLoading.classList.add('hidden');
  }
}

// ========== EVENTOS ==========
async function postEvent(payload) {
  const response = await fetch(`${getApiBaseUrl()}/events`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const detail = errorData?.detail || `Error ${response.status} registrando evento`;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg || JSON.stringify(item)).join(', ')
      : detail;
    throw new Error(message);
  }

  return response.json();
}

async function trackRecommendationShown(payload) {
  if (!state.selectedUser || !payload?.recommendation_id || state.shownRecommendationIds.has(payload.recommendation_id)) {
    return;
  }

  state.shownRecommendationIds.add(payload.recommendation_id);

  try {
    await postEvent({
      event_type: 'recommendation_shown',
      customer_id: state.selectedUser.customer_id,
      entity_type: 'recommendation',
      entity_id: payload.recommendation_id,
      properties: {
        slot: payload.slot,
        page_type: payload.page_type,
        item_count: payload.items.length,
        items: payload.items.map((item) => ({
          product_id: item.product_id,
          rank_position: item.rank_position,
          score: item.score,
        })),
      },
    });
  } catch (error) {
    setFeedbackStatus(error.message || 'No se pudo registrar la impresión.', 'error');
  }
}

async function trackRecommendationClick(item, payload) {
  if (!state.selectedUser || !payload?.recommendation_id) {
    return;
  }

  const clickKey = `${payload.recommendation_id}:${item.product_id}`;
  if (state.clickedProductIds.has(clickKey)) {
    return;
  }
  state.clickedProductIds.add(clickKey);

  try {
    await postEvent({
      event_type: 'recommendation_clicked',
      customer_id: state.selectedUser.customer_id,
      entity_type: 'recommendation',
      entity_id: payload.recommendation_id,
      properties: {
        product_id: item.product_id,
        rank_position: item.rank_position,
        slot: payload.slot,
        page_type: payload.page_type,
      },
    });

    setFeedbackStatus(`${item.name} agregado al carrito`, 'success');
  } catch (error) {
    setFeedbackStatus(error.message || 'No se pudo registrar el click.', 'error');
  }
}

async function sendFeedback(item, feedbackType, payload) {
  if (!state.selectedUser || !payload?.recommendation_id) {
    return;
  }

  const feedbackKey = `${payload.recommendation_id}:${item.product_id}:${feedbackType}`;
  if (state.pendingFeedback.has(feedbackKey)) {
    return;
  }

  state.pendingFeedback.add(feedbackKey);
  setFeedbackStatus('Registrando feedback...', 'info');

  try {
    await postEvent({
      event_type: 'recommendation_feedback',
      customer_id: state.selectedUser.customer_id,
      entity_type: 'recommendation',
      entity_id: payload.recommendation_id,
      properties: {
        product_id: item.product_id,
        feedback_type: feedbackType,
        rank_position: item.rank_position,
        slot: payload.slot,
        page_type: payload.page_type,
      },
    });

    const feedbackMessages = {
      like: `👍 Te gusta "${item.name}"`,
      dislike: `👎 No te gusta "${item.name}"`,
      hide: `🚫 "${item.name}" ocultado`,
    };
    setFeedbackStatus(feedbackMessages[feedbackType] || 'Feedback registrado', 'success');
  } catch (error) {
    setFeedbackStatus(error.message || 'No se pudo guardar el feedback.', 'error');
  } finally {
    state.pendingFeedback.delete(feedbackKey);
  }
}

// ========== BÚSQUEDA ==========
function setRecommendationsSectionMode(mode) {
  if (mode === 'search') {
    elements.recommendationsTitle.textContent = 'Resultados de búsqueda';
    elements.relatedRecommendationsBlock.classList.remove('hidden');
    return;
  }

  elements.recommendationsTitle.textContent = 'Recomendado para ti';
  elements.recommendationsCount.textContent = 'Basado en tu perfil y compras anteriores';
  elements.relatedRecommendationsBlock.classList.add('hidden');
  elements.relatedRecommendationsGrid.innerHTML = '';
  elements.relatedRecommendationsEmpty.classList.add('hidden');
}

function resetSearchState(options = {}) {
  state.isSearchMode = false;
  state.activeSearchTerm = '';
  state.searchResults = [];
  state.searchRelatedRecommendations = null;
  state.searchRequestId += 1;

  if (options.clearInput && elements.searchInput) {
    elements.searchInput.value = '';
  }

  setRecommendationsSectionMode('normal');
}

function renderSearchResults(results) {
  elements.recommendationsGrid.innerHTML = '';

  if (!results.length) {
    elements.emptyRecommendations.classList.remove('hidden');
    elements.emptyRecommendations.textContent = `No se encontraron productos para "${state.activeSearchTerm}".`;
    elements.recommendationsCount.textContent = '0 resultados';
    elements.relatedRecommendationsBlock.classList.add('hidden');
    return;
  }

  elements.emptyRecommendations.classList.add('hidden');
  elements.recommendationsCount.textContent = `${results.length} resultado${results.length === 1 ? '' : 's'} para "${state.activeSearchTerm}"`;

  results.forEach((product, index) => {
    elements.recommendationsGrid.appendChild(createProductCard({
      product_id: product.product_id,
      sku: product.sku,
      name: product.name,
      category: product.category,
      rank_position: index + 1,
      score: 1,
      reason_codes: ['SEARCH_MATCH'],
    }, {
      onViewClick: (item) => {
        setFeedbackStatus(`${item.name} seleccionado`, 'success');
      },
    }));
  });
}

function renderRelatedRecommendations(payload) {
  elements.relatedRecommendationsGrid.innerHTML = '';
  elements.relatedRecommendationsEmpty.classList.add('hidden');

  if (elements.debugOutput && elements.debugToggle?.checked) {
    elements.debugOutput.textContent = JSON.stringify(payload, null, 2);
  }

  const hasItems = renderRecommendationCards(elements.relatedRecommendationsGrid, payload, {
    onViewClick: (item) => trackRecommendationClick(item, state.searchRelatedRecommendations),
    onFeedback: (item, feedbackType) => sendFeedback(item, feedbackType, state.searchRelatedRecommendations),
  });

  if (!hasItems) {
    elements.relatedRecommendationsEmpty.classList.remove('hidden');
    elements.relatedRecommendationsCount.textContent = 'Sin recomendaciones relacionadas';
    return;
  }

  elements.relatedRecommendationsCount.textContent = `Mostrando ${payload.items.length} productos relacionados`;
  updateFooter(payload);
}

async function loadSearchRelatedRecommendations(category, requestId) {
  if (!state.selectedUser) {
    return;
  }

  elements.relatedRecommendationsBlock.classList.remove('hidden');
  elements.relatedRecommendationsGrid.innerHTML = '';
  elements.relatedRecommendationsEmpty.classList.add('hidden');
  elements.relatedRecommendationsCount.textContent = 'Cargando productos relacionados...';

  try {
    const response = await fetch(`${getApiBaseUrl()}/recommendations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        customer_id: state.selectedUser.customer_id,
        page_type: 'search',
        slot: 'related',
        limit: 8,
        context: { category },
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      let message = `Error al cargar recomendaciones relacionadas: ${response.status}`;
      if (errorData?.detail) {
        message = Array.isArray(errorData.detail)
          ? errorData.detail.map((entry) => `${entry.loc.join('.')}: ${entry.msg}`).join(', ')
          : errorData.detail;
      }
      throw new Error(message);
    }

    if (requestId !== state.searchRequestId) {
      return;
    }

    state.searchRelatedRecommendations = await response.json();
    renderRelatedRecommendations(state.searchRelatedRecommendations);
    await trackRecommendationShown(state.searchRelatedRecommendations);
  } catch (error) {
    if (requestId !== state.searchRequestId) {
      return;
    }
    elements.relatedRecommendationsCount.textContent = 'No se pudieron cargar recomendaciones relacionadas';
    elements.relatedRecommendationsEmpty.classList.remove('hidden');
    elements.relatedRecommendationsEmpty.textContent = error.message || 'No se pudieron cargar recomendaciones relacionadas.';
  }
}

async function performSearch(term) {
  const trimmed = term.trim();
  if (!trimmed) {
    await exitSearchMode();
    return;
  }

  if (!state.selectedUser) {
    setError(elements.recommendationsError, 'Selecciona un cliente antes de buscar.');
    return;
  }

  state.isSearchMode = true;
  state.activeSearchTerm = trimmed;
  const requestId = ++state.searchRequestId;

  setRecommendationsSectionMode('search');
  clearError(elements.recommendationsError);
  clearFeedbackStatus();
  elements.emptyRecommendations.classList.add('hidden');
  elements.recommendationsGrid.innerHTML = '';
  elements.relatedRecommendationsGrid.innerHTML = '';
  elements.relatedRecommendationsEmpty.classList.add('hidden');
  setLoading(elements.recommendationsLoading, true, 'Buscando productos...');

  try {
    const results = await fetchJsonWithFallback([
      `/products/search?q=${encodeURIComponent(trimmed)}`,
    ]);

    if (requestId !== state.searchRequestId) {
      return;
    }

    state.searchResults = results;
    renderSearchResults(results);

    if (results.length > 0) {
      await loadSearchRelatedRecommendations(results[0].category, requestId);
    }
  } catch (error) {
    if (requestId !== state.searchRequestId) {
      return;
    }
    setError(elements.recommendationsError, error.message || 'No se pudo completar la búsqueda.');
    elements.recommendationsGrid.innerHTML = '';
    elements.relatedRecommendationsBlock.classList.add('hidden');
  } finally {
    if (requestId === state.searchRequestId) {
      elements.recommendationsLoading.classList.add('hidden');
    }
  }
}

async function exitSearchMode() {
  if (!state.isSearchMode && !state.activeSearchTerm) {
    return;
  }

  resetSearchState();
  clearError(elements.recommendationsError);
  clearFeedbackStatus();
  elements.emptyRecommendations.classList.add('hidden');
  elements.recommendationsGrid.innerHTML = '';

  if (!state.selectedUser) {
    return;
  }

  if (state.lastRecommendations) {
    renderRecommendations(state.lastRecommendations);
    return;
  }

  await loadRecommendations();
}

// ========== EVENTOS DEL DOM ==========
function bindEvents() {
  // CAMBIO VISUAL: Toggle del dropdown de clientes
  elements.customerSelector.addEventListener('click', () => {
    elements.customerDropdown.classList.toggle('hidden');
  });

  // Cerrar dropdown al hacer click fuera
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.customer-selector-wrapper')) {
      elements.customerDropdown.classList.add('hidden');
    }
  });

  // CAMBIO VISUAL: Debug toggle
  elements.debugToggle.addEventListener('change', () => {
    elements.debugPanel.classList.toggle('hidden', !elements.debugToggle.checked);
    if (elements.debugToggle.checked && state.lastRecommendations) {
      elements.debugOutput.textContent = JSON.stringify(state.lastRecommendations, null, 2);
    }
  });

  // CAMBIO VISUAL: Cerrar debug panel
  if (elements.debugCloseBtn) {
    elements.debugCloseBtn.addEventListener('click', () => {
      elements.debugPanel.classList.add('hidden');
      elements.debugToggle.checked = false;
    });
  }

  elements.apiBaseUrl.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      loadUsers();
    }
  });

  elements.searchButton.addEventListener('click', () => {
    performSearch(elements.searchInput.value);
  });

  elements.searchInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      performSearch(elements.searchInput.value);
    }
  });

  elements.searchInput.addEventListener('input', () => {
    if (!elements.searchInput.value.trim()) {
      exitSearchMode();
    }
  });
}

function init() {
  cacheElements();
  bindEvents();
  loadUsers();
}

document.addEventListener('DOMContentLoaded', init);

