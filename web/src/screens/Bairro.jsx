import { useEffect, useState } from "react";
import { api } from "../api.js";
import Placa from "../components/Placa.jsx";
import Chips from "../components/Chips.jsx";
import TempoChart, { fmt } from "../components/TempoChart.jsx";
import TendenciaChart from "../components/TendenciaChart.jsx";
import RankingChart from "../components/RankingChart.jsx";

export default function Bairro({ regioes, grupos, sub, setSub, grupo, setGrupo, irPara }) {
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    if (!sub) return;
    let vivo = true;
    setErro(null);
    api.regiao(sub, grupo).then((d) => vivo && setDados(d)).catch((e) => vivo && setErro(e.message));
    return () => { vivo = false; };
  }, [sub, grupo]);

  const r = dados?.resumo;
  const q = Object.fromEntries((dados?.perguntas || []).map((p) => [p.id, p]));
  const tipo = grupo ? grupo.toLowerCase() : "zeladoria";

  return (
    <section className="screen" aria-labelledby="t-bairro">
      <h1 id="t-bairro" className="sr-only">Meu bairro</h1>
      <Placa kicker="Subprefeitura" nome={sub} rotulo="Escolher subprefeitura"
        rodape={r ? `${r.pedidos.toLocaleString("pt-BR")} pedidos de jul a set` : "Dados do SP156"}
        opcoes={Object.keys(regioes)} valor={sub} onChange={setSub} />
      <Chips rotulo="Tipo de problema" opcoes={grupos} valor={grupo} onChange={setGrupo} />

      {erro && <p className="erro">{erro}</p>}
      {!dados && !erro && <p className="carregando">Carregando os dados da região…</p>}

      {dados && (
        <>
          <div className="hero">
            <div className="hero-num">{fmt(r.resolvidos_7d_pct)}</div>
            <p className="hero-txt">
              dos pedidos de {tipo} feitos aqui foram resolvidos em até 7 dias.{" "}
              <span className="hero-cidade">Na cidade, {fmt(r.cidade_resolvidos_7d_pct)}. Ainda há {r.abertos.toLocaleString("pt-BR")} abertos na região.</span>
            </p>
          </div>

          {!grupo && q.tempo && (
            <div className="pergunta">
              <h2>{q.tempo.pergunta}</h2>
              <p className="resposta">{q.tempo.resposta}</p>
              <TempoChart dados={q.tempo.dados} destaque={q.tempo.destaque} />
            </div>
          )}

          {q.tendencia && (
            <div className="pergunta">
              <h2>{q.tendencia.pergunta}</h2>
              <p className="resposta">{q.tendencia.resposta}</p>
              <TendenciaChart dados={q.tendencia.dados} />
              <p className="nota">{q.tendencia.nota}</p>
            </div>
          )}

          {q.comparacao && (
            <div className="pergunta">
              <h2>{q.comparacao.pergunta}</h2>
              <p className="resposta">{q.comparacao.resposta}</p>
              <RankingChart dados={q.comparacao.dados} destaque={sub} />
            </div>
          )}

          <div className="pergunta">
            <h2>Tem um problema na sua rua?</h2>
            <p className="resposta">A gente ajuda a escrever o pedido e mostra onde abrir no SP156, o canal oficial da Prefeitura.</p>
            <button type="button" className="btn btn-full" onClick={() => irPara("registrar")}>Preparar meu pedido</button>
          </div>
        </>
      )}
    </section>
  );
}
