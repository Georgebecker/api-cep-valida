const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";
const HISTORY_KEY = "cepvalida.history.v1";
const MAX_HISTORY = 8;

const TYPES = {
  cpf: {
    label: "CPF",
    placeholder: "529.982.247-25",
    hint: "11 dígitos, com ou sem pontuação.",
    inputmode: "numeric",
    examples: ["529.982.247-25", "111.444.777-35", "123.456.789-09"],
  },
  cnpj: {
    label: "CNPJ",
    placeholder: "11.222.333/0001-81",
    hint: "14 dígitos, com ou sem pontuação.",
    inputmode: "numeric",
    examples: ["11.222.333/0001-81", "04.252.011/0001-10"],
  },
  cep: {
    label: "CEP",
    placeholder: "01001-000",
    hint: "8 dígitos. O endereço é consultado no ViaCEP quando disponível.",
    inputmode: "numeric",
    examples: ["01001-000", "20040-020", "30130-010"],
  },
  uf: {
    label: "UF",
    placeholder: "SP",
    hint: "Uma das 27 siglas oficiais, sem diferenciar maiúsculas de minúsculas.",
    inputmode: "text",
    examples: ["SP", "rj", "DF"],
  },
  pis: {
    label: "PIS/PASEP",
    placeholder: "120.425.445-09",
    hint: "11 dígitos, com ou sem pontuação.",
    inputmode: "numeric",
    examples: ["120.425.445-09", "170.332.558-94"],
  },
};

const state = {
  type: "cpf",
  lastResult: null,
  history: loadHistory(),
};

const elements = {
  tabs: Array.from(document.querySelectorAll(".tab")),
  form: document.querySelector("#validate-form"),
  input: document.querySelector("#document-value"),
  inputLabel: document.querySelector("#input-label"),
  fieldHint: document.querySelector("#field-hint"),
  examples: document.querySelector("#example-list"),
  submit: document.querySelector("#submit-button"),
  result: document.querySelector("#result"),
  copy: document.querySelector("#copy-result"),
  status: document.querySelector("#api-status"),
  statusLabel: document.querySelector("#api-status .status-label"),
  historyList: document.querySelector("#history-list"),
  clearHistory: document.querySelector("#clear-history"),
};

function loadHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.slice(0, MAX_HISTORY) : [];
  } catch {
    return [];
  }
}

function saveHistory() {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(state.history));
  } catch {
    /* armazenamento indisponível: o histórico vale só para esta página */
  }
}

function setApiStatus(mode, label) {
  elements.status.classList.remove("status-online", "status-offline", "status-checking");
  elements.status.classList.add(`status-${mode}`);
  elements.statusLabel.textContent = label;
}

async function checkHealth() {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 4000);
    const response = await fetch(`${API_BASE}/health`, {
      cache: "no-store",
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    await response.json();
    setApiStatus("online", "API online");
  } catch {
    setApiStatus("offline", "API offline");
  }
}

function selectType(type, { clear = true } = {}) {
  if (!TYPES[type]) return;
  state.type = type;
  const meta = TYPES[type];

  for (const tab of elements.tabs) {
    const active = tab.dataset.type === type;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
  }

  elements.inputLabel.textContent = meta.label;
  elements.input.placeholder = meta.placeholder;
  elements.input.inputMode = meta.inputmode;
  elements.fieldHint.textContent = meta.hint;
  if (clear) elements.input.value = "";

  renderExamples();
  elements.input.focus();
}

function renderExamples() {
  elements.examples.replaceChildren();
  for (const example of TYPES[state.type].examples) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.textContent = example;
    chip.addEventListener("click", () => {
      elements.input.value = example;
      elements.input.focus();
    });
    elements.examples.append(chip);
  }
}

function setLoading(loading) {
  elements.submit.disabled = loading;
  elements.submit.textContent = loading ? "Validando…" : "Validar";
}

function renderEmpty(message = "Escolha o tipo, informe o documento e clique em Validar.") {
  state.lastResult = null;
  elements.copy.hidden = true;
  elements.result.className = "result-empty";
  elements.result.replaceChildren();

  const icon = document.createElement("div");
  icon.className = "empty-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = "⌁";

  const text = document.createElement("p");
  text.textContent = message;

  elements.result.append(icon, text);
}

function addDetail(list, term, value) {
  const dt = document.createElement("dt");
  dt.textContent = term;
  const dd = document.createElement("dd");
  dd.textContent = value;
  list.append(dt, dd);
}

function formatAddress(address) {
  const lines = [];
  const lineOne = [address.street, address.complement].filter(Boolean).join(", ");
  if (lineOne) lines.push(lineOne);
  if (address.neighborhood) lines.push(address.neighborhood);
  const cityState = [address.city, address.state].filter(Boolean).join(" — ");
  if (cityState) lines.push(cityState);
  if (address.cep) lines.push(`CEP ${address.cep}`);
  return lines.join("\n");
}

function renderResult(body, elapsedMs) {
  state.lastResult = body;
  elements.result.className = `result result-${body.valid ? "valid" : "invalid"}`;
  elements.result.replaceChildren();

  const status = document.createElement("div");
  status.className = "result-status";

  const icon = document.createElement("span");
  icon.className = "result-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = body.valid ? "✓" : "✕";

  const label = document.createElement("span");
  label.textContent = body.valid ? "Documento válido" : "Documento inválido";
  status.append(icon, label);

  const message = document.createElement("p");
  message.className = "result-message";
  message.textContent = body.message;

  const details = document.createElement("dl");
  addDetail(details, "Tipo", TYPES[body.document]?.label ?? body.document.toUpperCase());
  if (body.normalized) addDetail(details, "Normalizado", body.normalized);
  if (body.source) addDetail(details, "Fonte", body.source === "viacep" ? "ViaCEP" : "validação local");
  if (body.address) {
    const address = formatAddress(body.address);
    if (address) addDetail(details, "Endereço", address);
  }
  if (typeof elapsedMs === "number") addDetail(details, "Tempo", `${elapsedMs} ms`);

  elements.result.append(status, message, details);
  elements.copy.hidden = false;
}

function renderError(message) {
  state.lastResult = null;
  elements.copy.hidden = true;
  elements.result.className = "result result-invalid";
  elements.result.replaceChildren();

  const status = document.createElement("div");
  status.className = "result-status";
  const icon = document.createElement("span");
  icon.className = "result-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = "!";
  const label = document.createElement("span");
  label.textContent = "Não foi possível validar";
  status.append(icon, label);

  const detail = document.createElement("p");
  detail.className = "result-message";
  detail.textContent = message;

  elements.result.append(status, detail);
}

function relativeTime(timestamp) {
  const diff = Date.now() - timestamp;
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "agora";
  if (minutes < 60) return `há ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `há ${hours} h`;
  return new Date(timestamp).toLocaleDateString("pt-BR");
}

function addHistory(body) {
  state.history.unshift({
    type: body.document,
    value: body.normalized || elements.input.value,
    valid: body.valid,
    at: Date.now(),
  });
  state.history = state.history.slice(0, MAX_HISTORY);
  saveHistory();
  renderHistory();
}

function renderHistory() {
  elements.historyList.replaceChildren();

  if (state.history.length === 0) {
    const empty = document.createElement("li");
    empty.className = "history-empty";
    empty.textContent = "Nenhuma validação nesta sessão.";
    elements.historyList.append(empty);
    return;
  }

  for (const entry of state.history) {
    const item = document.createElement("li");
    item.className = "history-item";

    const type = document.createElement("span");
    type.className = "history-type";
    type.textContent = entry.type.toUpperCase();

    const value = document.createElement("span");
    value.className = "history-value";
    value.textContent = entry.value;

    const meta = document.createElement("span");
    meta.className = "history-meta";

    const badge = document.createElement("span");
    badge.className = `history-badge ${entry.valid ? "valid" : "invalid"}`;
    badge.textContent = entry.valid ? "válido" : "inválido";

    const time = document.createElement("span");
    time.textContent = relativeTime(entry.at);

    const reuse = document.createElement("button");
    reuse.type = "button";
    reuse.className = "history-reuse";
    reuse.textContent = "usar";
    reuse.addEventListener("click", () => {
      selectType(entry.type);
      elements.input.value = entry.value;
      elements.input.focus();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    meta.append(badge, time, reuse);
    item.append(type, value, meta);
    elements.historyList.append(item);
  }
}

async function copyLastResult() {
  if (!state.lastResult) return;
  const text = JSON.stringify(state.lastResult, null, 2);

  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.append(area);
    area.select();
    document.execCommand("copy");
    area.remove();
  }

  const original = elements.copy.textContent;
  elements.copy.textContent = "Copiado!";
  setTimeout(() => {
    elements.copy.textContent = original;
  }, 1400);
}

async function validate(event) {
  event.preventDefault();
  const value = elements.input.value;

  if (!value.trim()) {
    renderError("Informe um valor para validar. Exemplos estão disponíveis ao lado do campo.");
    elements.input.focus();
    return;
  }

  setLoading(true);
  const started = performance.now();

  try {
    const response = await fetch(`${API_BASE}/validate/${state.type}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    });

    if (response.status === 422) {
      renderError("Entrada malformada: informe um valor de 1 a 32 caracteres, sem campos extras.");
      return;
    }
    if (response.status === 429) {
      const retryAfter = response.headers.get("Retry-After");
      renderError(
        retryAfter
          ? `Limite de requisições atingido. Tente novamente em ${retryAfter} s.`
          : "Limite de requisições atingido. Aguarde e tente novamente.",
      );
      return;
    }
    if (!response.ok) {
      renderError(`A API respondeu HTTP ${response.status}. Tente novamente.`);
      return;
    }

    const body = await response.json();
    const elapsed = Math.round(performance.now() - started);
    renderResult(body, elapsed);
    addHistory(body);
    checkHealth();
  } catch (error) {
    renderError(
      `Falha de conexão com a API (${error.message}). Verifique se o servidor está em execução.`,
    );
    setApiStatus("offline", "API offline");
  } finally {
    setLoading(false);
  }
}

for (const tab of elements.tabs) {
  tab.addEventListener("click", () => selectType(tab.dataset.type));
}

elements.form.addEventListener("submit", validate);
elements.copy.addEventListener("click", copyLastResult);
elements.clearHistory.addEventListener("click", () => {
  state.history = [];
  saveHistory();
  renderHistory();
});

window.addEventListener("focus", checkHealth);
window.addEventListener("online", checkHealth);
window.addEventListener("offline", () => setApiStatus("offline", "API offline"));

selectType("cpf", { clear: false });
renderHistory();
checkHealth();
setInterval(checkHealth, 20000);