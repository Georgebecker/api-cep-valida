const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

const EXAMPLES = {
  cpf: ["529.982.247-25", "111.444.777-35", "123.456.789-09"],
  cnpj: ["11.222.333/0001-81", "04.252.011/0001-10"],
  cep: ["01001-000", "20040-020", "30130-010"],
  uf: ["SP", "rj", "DF"],
  pis: ["120.425.445-09", "170.332.558-94"],
};

const PLACEHOLDERS = {
  cpf: "529.982.247-25",
  cnpj: "11.222.333/0001-81",
  cep: "01001-000",
  uf: "SP",
  pis: "120.425.445-09",
};

const form = document.querySelector("#validate-form");
const typeSelect = document.querySelector("#document-type");
const valueInput = document.querySelector("#document-value");
const resultBox = document.querySelector("#result");
const exampleList = document.querySelector("#example-list");

function renderExamples() {
  const type = typeSelect.value;
  exampleList.replaceChildren();
  for (const example of EXAMPLES[type]) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = example;
    button.addEventListener("click", () => {
      valueInput.value = example;
      valueInput.focus();
    });
    item.append(button);
    exampleList.append(item);
  }
  valueInput.placeholder = PLACEHOLDERS[type];
}

function row(term, description) {
  const dt = document.createElement("dt");
  dt.textContent = term;
  const dd = document.createElement("dd");
  dd.textContent = description;
  return [dt, dd];
}

function renderResult(body) {
  resultBox.replaceChildren();
  resultBox.hidden = false;
  resultBox.classList.toggle("valid", body.valid);
  resultBox.classList.toggle("invalid", !body.valid);

  const status = document.createElement("span");
  status.className = `status-${body.valid ? "valid" : "invalid"}`;
  status.textContent = body.valid ? "Documento válido" : "Documento inválido";
  resultBox.append(status);

  const details = document.createElement("dl");
  details.append(...row("Mensagem", body.message));
  if (body.normalized) {
    details.append(...row("Normalizado", body.normalized));
  }
  if (body.source) {
    details.append(...row("Fonte", body.source));
  }
  if (body.address) {
    const location = [body.address.street, body.address.neighborhood, body.address.city, body.address.state]
      .filter(Boolean)
      .join(" — ");
    if (location) {
      details.append(...row("Endereço", location));
    }
  }
  resultBox.append(details);
}

function renderError(message) {
  resultBox.replaceChildren();
  resultBox.hidden = false;
  resultBox.classList.add("invalid");
  resultBox.classList.remove("valid");
  const status = document.createElement("span");
  status.className = "status-invalid";
  status.textContent = "Não foi possível validar";
  resultBox.append(status);
  const details = document.createElement("dl");
  details.append(...row("Mensagem", message));
  resultBox.append(details);
}

async function submitValidation(event) {
  event.preventDefault();
  const type = typeSelect.value;
  const value = valueInput.value;

  try {
    const response = await fetch(`${API_BASE}/validate/${type}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    });
    if (response.status === 422) {
      renderError("Entrada inválida: informe um valor entre 1 e 32 caracteres.");
      return;
    }
    if (!response.ok) {
      renderError(`A API respondeu com status ${response.status}.`);
      return;
    }
    renderResult(await response.json());
  } catch (error) {
    renderError(`Falha de conexão com a API (${error.message}).`);
  }
}

typeSelect.addEventListener("change", renderExamples);
form.addEventListener("submit", submitValidation);
renderExamples();
