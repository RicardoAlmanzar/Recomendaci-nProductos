const state = {
  users: [],
  selectedUser: null,
  lastRecommendations: null,
  purchaseHistory: null,
  shownRecommendationIds: new Set(),
  clickedProductIds: new Set(),
  pendingFeedback: new Set(),
};

const elements = {};

function cacheElements() {
  elements.apiBaseUrl = document.getElementById('apiBaseUrl');
  elements.debugToggle = document.getElementById('debugToggle');
  elements.reloadUsersBtn = document.getElementById('reloadUsersBtn');
  elements.reloadRecommendationsBtn = document.getElementById('reloadRecommendationsBtn');
  elements.reloadHistoryBtn = document.getElementById('reloadHistoryBtn');
  elements.usersList = document.getElementById('usersList');
  elements.usersLoading = document.getElementById('usersLoading');
  elements.usersError = document.getElementById('usersError');
  elements.usersMeta = document.getElementById('usersMeta');
  elements.selectedUserMeta = document.getElementById('selectedUserMeta');
  elements.historyMeta = document.getElementById('historyMeta');
  elements.historyLoading = document.getElementById('historyLoading');
  elements.historyError = document.getElementById('historyError');
  elements.historyEmpty = document.getElementById('historyEmpty');
  elements.historyList = document.getElementById('historyList');
  elements.recommendationsLoading = document.getElementById('recommendationsLoading');
  elements.recommendationsError = document.getElementById('recommendationsError');
  elements.feedbackStatus = document.getElementById('feedbackStatus');
  elements.emptyRecommendations = document.getElementById('emptyRecommendations');
  elements.recommendationsGrid = document.getElementById('recommendationsGrid');
  elements.debugSection = document.getElementById('debugSection');
  elements.debugOutput = document.getElementById('debugOutput');
}

function getApiBaseUrl() {
  return elements.apiBaseUrl.value.trim().replace(/\/$/, '');
}

async function fetchJsonWithFallback(paths, options = {}) {
  let lastError = null;

  for (const path of paths) {
    try {
      const response = await fetch(`${getApiBaseUrl()}${path}`, options);
      if (!response.ok) {
        lastError = new Error(`Error ${response.status} en ${path}`);
        continue;
      }

      return await response.json();
    } catch (error) {
      lastError = error;
    }
  }

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
  elements.feedbackStatus.className = `state feedback-state ${tone}`;
  elements.feedbackStatus.classList.remove('hidden');
}

function clearFeedbackStatus() {
  elements.feedbackStatus.textContent = '';
  elements.feedbackStatus.classList.add('hidden');
}

function renderUsers() {
  elements.usersList.innerHTML = '';

  if (!state.users.length) {
    elements.usersMeta.textContent = 'No se encontraron usuarios.';
    elements.usersList.innerHTML = '<li class="state">No hay usuarios cargados.</li>';
    return;
  }

  elements.usersMeta.textContent = `${state.users.length} usuarios cargados`;

  state.users.forEach((user) => {
    const item = document.createElement('li');
    item.className = `user-item ${state.selectedUser?.customer_id === user.customer_id ? 'active' : ''}`;
    item.dataset.userId = user.customer_id;
    item.innerHTML = `
      <strong>${user.customer_id}</strong>
      <p class="user-meta">${user.business_type} · ${user.city}</p>
      <p class="user-meta">Ticket promedio: ${formatCurrency(user.average_order_value)}</p>
    `;
    item.addEventListener('click', () => selectUser(user.customer_id));
    elements.usersList.appendChild(item);
  });
}

function renderRecommendations(payload) {
  elements.recommendationsGrid.innerHTML = '';
  elements.debugOutput.textContent = JSON.stringify(payload, null, 2);

  if (!payload || !payload.items || payload.items.length === 0) {
    elements.emptyRecommendations.classList.remove('hidden');
    elements.emptyRecommendations.textContent = 'Este usuario no tiene recomendaciones.';
    return;
  }

  elements.emptyRecommendations.classList.add('hidden');

  payload.items.forEach((item) => {
    const card = document.createElement('article');
    card.className = 'card recommendation-card';

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'recommendation-main';
    button.innerHTML = `
      <div class="score">Score ${formatNumber(item.score)}</div>
      <h3>${item.name}</h3>
      <p class="user-meta">SKU: ${item.sku}</p>
      <p class="user-meta">Producto: ${item.product_id}</p>
      <p class="user-meta">Haz clic para ver el porqué</p>
    `;

    const details = document.createElement('div');
    details.className = 'recommendation-details hidden';
    details.innerHTML = buildRecommendationExplanation(item);

    button.addEventListener('click', () => {
      details.classList.toggle('hidden');
      trackRecommendationClick(item);
    });

    card.appendChild(button);
    card.appendChild(details);
    card.appendChild(buildFeedbackActions(item));
    elements.recommendationsGrid.appendChild(card);
  });
}

function buildFeedbackActions(item) {
  const actions = document.createElement('div');
  actions.className = 'feedback-actions';

  [
    ['like', 'Me gusta'],
    ['not_interested', 'No me interesa'],
    ['hide', 'Ocultar'],
    ['dislike', 'No encaja'],
  ].forEach(([feedbackType, label]) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `feedback-button ${feedbackType}`;
    button.textContent = label;
    button.addEventListener('click', (event) => {
      event.stopPropagation();
      sendFeedback(item, feedbackType);
    });
    actions.appendChild(button);
  });

  return actions;
}

function buildRecommendationExplanation(item) {
  const reasons = item.reason_codes || [];
  const rulesHtml = reasons.length
    ? `<ul class="reason-list">${reasons.map((r) => `<li>${r}</li>`).join('')}</ul>`
    : '<p class="user-meta">Sin razones específicas.</p>';

  return `
    <p><strong>Score final:</strong> ${formatNumber(item.score)}</p>
    <p class="user-meta"><strong>Razones (Reason Codes):</strong></p>
    ${rulesHtml}
  `;
}

function formatNumber(value) {
  return Number(value || 0).toFixed(4);
}

function renderHistory(historyPayload) {
  elements.historyList.innerHTML = '';

  const purchases = historyPayload?.purchases || [];
  if (!purchases.length) {
    elements.historyEmpty.classList.remove('hidden');
    elements.historyEmpty.textContent = 'Este usuario no tiene compras registradas.';
    elements.historyMeta.textContent = 'Sin historial.';
    return;
  }

  elements.historyEmpty.classList.add('hidden');
  elements.historyMeta.textContent = `${purchases.length} compras registradas`;

  purchases.forEach((purchase) => {
    const item = document.createElement('article');
    item.className = 'history-item';
    item.innerHTML = `
      <strong>${purchase.product_name || purchase.product_id}</strong>
      <p class="user-meta">Cantidad: ${purchase.quantity}</p>
      <p class="user-meta">Categoría: ${purchase.category || 'N/A'}</p>
      <p class="user-meta">Canal: ${purchase.channel || 'N/A'}</p>
      <p class="user-meta">Ciudad: ${purchase.city || 'N/A'}</p>
    `;
    elements.historyList.appendChild(item);
  });
}

function formatCurrency(value) {
  return new Intl.NumberFormat('es-DO', {
    style: 'currency',
    currency: 'DOP',
    maximumFractionDigits: 0,
  }).format(value || 0);
}

async function loadUsers() {
  clearError(elements.usersError);
  setLoading(elements.usersLoading, true, 'Cargando usuarios...');

  try {
    state.users = await fetchJsonWithFallback(['/customers', '/users']);
    renderUsers();

    if (state.users.length && !state.selectedUser) {
      await selectUser(state.users[0].customer_id);
    }
  } catch (error) {
    setError(elements.usersError, error.message || 'No se pudieron cargar los usuarios.');
    elements.usersMeta.textContent = 'Error al cargar usuarios.';
    elements.usersList.innerHTML = '';
  } finally {
    elements.usersLoading.classList.add('hidden');
  }
}

async function selectUser(userId) {
  const user = state.users.find((candidate) => candidate.customer_id === userId);
  if (!user) {
    return;
  }

  state.selectedUser = user;
  state.lastRecommendations = null;
  state.purchaseHistory = null;
  state.shownRecommendationIds.clear();
  state.clickedProductIds.clear();
  state.pendingFeedback.clear();
  clearFeedbackStatus();
  renderUsers();

  elements.selectedUserMeta.textContent = `Usuario seleccionado: ${user.customer_id} · ${user.business_type} · ${user.city}`;
  elements.reloadRecommendationsBtn.disabled = false;
  elements.reloadHistoryBtn.disabled = false;

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
  if (!state.selectedUser) {
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
        limit: 5,
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
    setFeedbackStatus(error.message || 'No se pudo registrar la impresion.', 'error');
  }
}

async function trackRecommendationClick(item) {
  if (!state.selectedUser || !state.lastRecommendations?.recommendation_id) {
    return;
  }

  const clickKey = `${state.lastRecommendations.recommendation_id}:${item.product_id}`;
  if (state.clickedProductIds.has(clickKey)) {
    return;
  }
  state.clickedProductIds.add(clickKey);

  try {
    await postEvent({
      event_type: 'recommendation_clicked',
      customer_id: state.selectedUser.customer_id,
      entity_type: 'recommendation',
      entity_id: state.lastRecommendations.recommendation_id,
      properties: {
        product_id: item.product_id,
        rank_position: item.rank_position,
        slot: state.lastRecommendations.slot,
        page_type: state.lastRecommendations.page_type,
      },
    });
  } catch (error) {
    setFeedbackStatus(error.message || 'No se pudo registrar el click.', 'error');
  }
}

async function sendFeedback(item, feedbackType) {
  if (!state.selectedUser || !state.lastRecommendations?.recommendation_id) {
    return;
  }

  const feedbackKey = `${state.lastRecommendations.recommendation_id}:${item.product_id}:${feedbackType}`;
  if (state.pendingFeedback.has(feedbackKey)) {
    return;
  }

  state.pendingFeedback.add(feedbackKey);
  setFeedbackStatus(`Guardando feedback para ${item.product_id}...`, 'info');

  try {
    await postEvent({
      event_type: 'recommendation_feedback',
      customer_id: state.selectedUser.customer_id,
      entity_type: 'recommendation',
      entity_id: state.lastRecommendations.recommendation_id,
      properties: {
        product_id: item.product_id,
        feedback_type: feedbackType,
        rank_position: item.rank_position,
        slot: state.lastRecommendations.slot,
        page_type: state.lastRecommendations.page_type,
      },
    });

    const message = feedbackType === 'hide'
      ? 'Producto ocultado. Recalculando recomendaciones...'
      : 'Feedback guardado. Recalculando recomendaciones...';
    setFeedbackStatus(message, 'success');
    await loadRecommendations({ preserveFeedbackStatus: true });
  } catch (error) {
    setFeedbackStatus(error.message || 'No se pudo guardar el feedback.', 'error');
  } finally {
    state.pendingFeedback.delete(feedbackKey);
  }
}

function bindEvents() {
  elements.reloadUsersBtn.addEventListener('click', loadUsers);
  elements.reloadRecommendationsBtn.addEventListener('click', loadRecommendations);
  elements.reloadHistoryBtn.addEventListener('click', loadHistory);
  elements.debugToggle.addEventListener('change', () => {
    elements.debugSection.classList.toggle('hidden', !elements.debugToggle.checked);
    if (elements.debugToggle.checked && state.lastRecommendations) {
      elements.debugOutput.textContent = JSON.stringify(state.lastRecommendations, null, 2);
    }
  });

  elements.apiBaseUrl.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      loadUsers();
    }
  });
}

function init() {
  cacheElements();
  bindEvents();
  loadUsers();
}

document.addEventListener('DOMContentLoaded', init);
