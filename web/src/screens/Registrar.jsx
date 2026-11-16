import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";

const EXEMPLO = "A calçada em frente à padaria da Rua Tobias Barreto está toda quebrada desde o mês passado e minha avó tropeçou lá.";

function destacarCampos(texto) {
  // [endereço], [ponto de referência]: o que o cidadão ainda precisa completar
  return texto.split(/(\[[^\]]+\])/g).map((p, k) => (p.startsWith("[") ? <mark key={k}>{p}</mark> : p));
}

// Plano B: no celular pelo IP da rede a página não é contexto seguro e navigator.clipboard não existe.
function copiarPorSelecao(texto) {
  const ta = document.createElement("textarea");
  ta.value = texto;
  ta.style.cssText = "position:fixed;top:0;left:0;width:1px;height:1px;opacity:0;";
  document.body.appendChild(ta);
  let ok = false;
  try {
    ta.focus();
    ta.select();
    ta.setSelectionRange(0, texto.length);   // iOS ignora select() sozinho
    ok = document.execCommand("copy");
  } catch {
    ok = false;
  }
  document.body.removeChild(ta);
  return ok;
}

export default function Registrar({ regioes, sub, setSub, preenchido, limparPreenchido }) {
  const [distrito, setDistrito] = useState("");
  const [texto, setTexto] = useState("");
  const [res, setRes] = useState(null);
  const [erro, setErro] = useState(null);
  const [enviando, setEnviando] = useState(false);
  const [copiado, setCopiado] = useState(false);
  const topoResultado = useRef(null);

  const distritos = sub ? regioes[sub] || [] : [];
  useEffect(() => { if (!distritos.includes(distrito)) setDistrito(distritos[0] || ""); }, [sub]); // eslint-disable-line

  useEffect(() => {
    if (!preenchido) return;
    if (preenchido.subprefeitura) setSub(preenchido.subprefeitura);
    setTimeout(() => preenchido.distrito && setDistrito(preenchido.distrito), 0);
    setTexto(preenchido.texto || "");
    setRes(null);
    limparPreenchido();
  }, [preenchido]); // eslint-disable-line

  async function preparar(ev) {
    ev.preventDefault();
    setErro(null); setRes(null); setCopiado(false);
    setEnviando(true);
    try {
      const r = await api.assistente(texto, sub, distrito);
      setRes(r);
      setTimeout(() => topoResultado.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  }

  async function copiar() {
    const alvo = res.texto_solicitacao;
    try {
      if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(alvo);
      else if (!copiarPorSelecao(alvo)) throw new Error("sem suporte");
      setCopiado(true);
      setErro(null);
    } catch {
      setCopiado(false);
      setErro("Não foi possível copiar automaticamente. Selecione o texto e copie.");
    }
  }

  const ctx = res?.contexto;
  return (
    <section className="screen" aria-labelledby="t-reg">
      <h1 id="t-reg" className="screen-title">Fazer um pedido no SP156</h1>
      <p className="lede">Conte o problema do seu jeito. A gente identifica o serviço certo, escreve o pedido e mostra onde enviar. Quem registra é você, no canal oficial da Prefeitura.</p>

      <form onSubmit={preparar}>
        <div className="passo">
          <h2 className="passo-titulo"><span className="passo-num">1</span>Onde é o problema?</h2>
          <label className="campo"><span>Subprefeitura</span>
            <select className="input" value={sub || ""} onChange={(e) => setSub(e.target.value)} required>
              {!sub && <option value="">Escolha…</option>}
              {Object.keys(regioes).map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>
          <label className="campo"><span>Distrito</span>
            <select className="input" value={distrito} onChange={(e) => setDistrito(e.target.value)} required>
              {distritos.map((d) => <option key={d}>{d}</option>)}
            </select>
          </label>
        </div>

        <div className="passo">
          <h2 className="passo-titulo"><span className="passo-num">2</span>O que está acontecendo?</h2>
          <label className="campo"><span className="sr-only">Descrição do problema</span>
            <textarea className="input" value={texto} maxLength={500} placeholder={EXEMPLO}
              onChange={(e) => setTexto(e.target.value)} required minLength={10} />
          </label>
          <div className="contador">{texto.length}/500</div>
          <p className="muted small">Não escreva seu nome, CPF ou telefone. O CitizenTech não precisa deles.</p>
        </div>

        <button type="submit" className="btn btn-full" disabled={enviando || !sub || !distrito}>
          {enviando ? "Preparando o pedido…" : "Preparar o pedido"}
        </button>
      </form>

      {erro && <p className="erro" role="alert">{erro}</p>}

      {res && (
        <div className="resultado" ref={topoResultado} aria-live="polite">
          <h2 className="passo-titulo" style={{ marginTop: 28 }}><span className="passo-num">3</span>Seu pedido está pronto</h2>

          {res.emergencia && <p className="emergencia" role="alert">{res.emergencia}</p>}

          <div className="bloco">
            <h3>Serviço no SP156</h3>
            {res.servico === "outro" ? (
              <p>Esse problema não parece ser de ruas e calçadas. Abra o portal do SP156 e procure o serviço pelo nome; o texto abaixo ainda pode ajudar.</p>
            ) : (
              <>
                <span className="placa-mini">{res.servico}</span>
                {res.url_servico
                  ? <a className="link-servico" href={res.url_servico} target="_blank" rel="noopener noreferrer">Abrir a página oficial deste serviço <span aria-hidden="true">›</span></a>
                  : <p className="muted small" style={{ marginTop: 8 }}>Procure exatamente esse nome no portal ou no aplicativo.</p>}
              </>
            )}
          </div>

          <div className="bloco">
            <h3>Texto para colar</h3>
            <p className="texto-pedido">{destacarCampos(res.texto_solicitacao)}</p>
            <button type="button" className="btn btn-sec" onClick={copiar}>{copiado ? "Texto copiado" : "Copiar texto"}</button>
            {res.erro && <p className="muted small">A IA não respondeu agora, então montamos um rascunho simples. Revise antes de enviar.</p>}
          </div>

          {res.informacoes_faltando.length > 0 && (
            <div className="bloco">
              <h3>Antes de enviar, tenha em mãos</h3>
              <ul className="faltando">{res.informacoes_faltando.map((f) => <li key={f}>{f}</li>)}</ul>
            </div>
          )}

          {res.chance_7d_pct !== null && ctx && (
            <div className="bloco">
              <h3>O que esperar</h3>
              <div className="chance">
                <span className="chance-num">{res.chance_7d_pct < 1 ? "<1%" : `${Math.round(res.chance_7d_pct)}%`}</span>
                <span>de chance de ser resolvido em até 7 dias, pelo histórico de pedidos parecidos.</span>
              </div>
              <p className="muted small">
                No {ctx.escopo === "distrito" ? "distrito" : "conjunto da subprefeitura"} {ctx.local}, foram {ctx.pedidos_trimestre.toLocaleString("pt-BR")} pedidos desse serviço de julho a setembro
                {ctx.mediana_dias !== null ? `; metade dos resolvidos levou até ${Math.round(ctx.mediana_dias)} dia${Math.round(ctx.mediana_dias) === 1 ? "" : "s"}` : ""}
                {ctx.abertos ? `; ${ctx.abertos} ainda estavam abertos em 30/09` : ""}. É uma estimativa, não um prazo da Prefeitura.
              </p>
            </div>
          )}

          <div className="bloco">
            <h3>Onde enviar</h3>
            <div className="canais">
              {res.canais.map((c) => {
                // No portal, o link vai direto na página do serviço escolhido; nos outros canais não há como.
                const direto = c.id === "portal" && res.url_servico;
                const url = direto ? res.url_servico : c.url;
                const como = direto ? "abre já na página deste serviço" : c.como;
                const conteudo = <><span><b>{c.nome}</b><span>{como}</span></span>{url && <span className="canal-seta" aria-hidden="true">›</span>}</>;
                return url
                  ? <a key={c.id} className="canal" href={url} target="_blank" rel="noopener noreferrer">{conteudo}</a>
                  : <div key={c.id} className="canal">{conteudo}</div>;
              })}
            </div>
            <p className="aviso-app">Depois de enviar, guarde o número de protocolo que o SP156 informar: é com ele que você acompanha o pedido. O CitizenTech não envia nem guarda o seu pedido.</p>
          </div>
        </div>
      )}
    </section>
  );
}
