// Cliente da API Python. Toda resposta de erro traz { erro: "mensagem" }.
async function call(path, options) {
  let resp;
  try {
    resp = await fetch(path, options);
  } catch {
    throw new Error("Sem conexão com o servidor. Confira se a API está rodando.");
  }
  const body = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const msg = typeof body.erro === "string" ? body.erro
      : Array.isArray(body.detail) ? body.detail.map((d) => d.msg.replace(/^Value error, /, "")).join(" ")
      : "Algo deu errado. Tente de novo.";
    throw new Error(msg);
  }
  return body;
}

const qs = (params) =>
  new URLSearchParams(Object.entries(params).filter(([, v]) => v !== null && v !== undefined && v !== "")).toString();

export const api = {
  regioes: () => call("/api/regioes"),
  regiao: (subprefeitura, grupo) => call(`/api/regiao?${qs({ subprefeitura, grupo })}`),
  atrasos: (subprefeitura, grupo, limite = 20) => call(`/api/atrasos?${qs({ subprefeitura, grupo, limite })}`),
  sobre: () => call("/api/sobre"),
  assistente: (texto, subprefeitura, distrito) =>
    call("/api/assistente", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ texto, subprefeitura, distrito }),
    }),
};

// Preferências do aparelho (só conveniência: o app funciona sem elas).
export const prefs = {
  get(key) {
    try { return localStorage.getItem(`zeladoriasp.${key}`); } catch { return null; }
  },
  set(key, value) {
    try { localStorage.setItem(`zeladoriasp.${key}`, value); } catch { /* modo privado */ }
  },
};
