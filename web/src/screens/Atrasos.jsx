import { useEffect, useState } from "react";
import { api } from "../api.js";
import Chips from "../components/Chips.jsx";

const fmtVezes = (v) => (v >= 10 ? Math.round(v) : v.toFixed(1).replace(".", ","));
const mapa = (lat, lon) => `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=18/${lat}/${lon}`;

export default function Atrasos({ regioes, grupos, sub, setSub, grupo, setGrupo, reforcar }) {
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    let vivo = true;
    setErro(null); setDados(null);
    api.atrasos(sub || null, grupo, 20).then((d) => vivo && setDados(d)).catch((e) => vivo && setErro(e.message));
    return () => { vivo = false; };
  }, [sub, grupo]);

  return (
    <section className="screen" aria-labelledby="t-atr">
      <h1 id="t-atr" className="screen-title">Onde a Prefeitura está mais atrasada</h1>
      <p className="lede">Pedidos que seguiam abertos no SP156 em 30/09. No topo, onde mais gente espera há mais tempo.</p>

      <div className="filtros">
        <label className="campo" style={{ marginBottom: 0 }}><span>Subprefeitura</span>
          <select className="input" value={sub || ""} onChange={(e) => setSub(e.target.value || null)}>
            <option value="">Cidade inteira</option>
            {Object.keys(regioes).map((s) => <option key={s}>{s}</option>)}
          </select>
        </label>
      </div>
      <Chips rotulo="Tipo de problema" opcoes={grupos} valor={grupo} onChange={setGrupo} />

      {erro && <p className="erro">{erro}</p>}
      {!dados && !erro && <p className="carregando">Carregando…</p>}
      {dados && (
        <>
          <p className="resumo-atrasos">
            <b>{dados.problemas_abertos.toLocaleString("pt-BR")}</b> problemas com pedidos abertos, somando {dados.pedidos_abertos.toLocaleString("pt-BR")} pedidos.
          </p>
          {dados.itens.length === 0 && <p className="muted">Nenhum problema aberto com esse filtro. Escolha outro tipo ou a cidade inteira.</p>}
          <ol className="lista">
            {dados.itens.map((it) => (
              <li key={it.problema_id} className="item">
                <div className="item-topo">
                  <div>
                    <p className="item-rua">{it.logradouro || "Endereço não informado"}</p>
                    <p className="item-tipo">{it.servico}, em {it.distrito}</p>
                  </div>
                  {it.vezes_acima_do_tipico >= 2 && <span className="vezes">{fmtVezes(it.vezes_acima_do_tipico)}× o normal</span>}
                </div>
                <p className="item-dias"><b>{it.dias_em_aberto} dias</b><span>desde o primeiro pedido</span></p>
                <p className="item-fatos">
                  {it.pedidos_abertos === 1 ? "1 pedido aberto" : `${it.pedidos_abertos} pedidos abertos`}
                  {it.pontos > 1 ? ` em ${it.pontos} pontos da rua` : ""}.
                  {it.mediana_tipica_dias !== null && ` Aqui, esse tipo de problema costuma ser resolvido em ${Math.max(1, Math.round(it.mediana_tipica_dias))} dia${Math.max(1, Math.round(it.mediana_tipica_dias)) === 1 ? "" : "s"}.`}
                </p>
                <div className="item-acoes">
                  <button type="button" className="btn-link" onClick={() => reforcar(it)}>Também me afeta: fazer pedido</button>
                  <a href={mapa(it.lat, it.lon)} target="_blank" rel="noopener noreferrer">Ver no mapa</a>
                </div>
              </li>
            ))}
          </ol>
          <p className="nota">Um problema é uma rua com o mesmo tipo de pedido aberto na mesma subprefeitura. "O normal" é o tempo que metade dos pedidos desse tipo levou para ser resolvida na região. Os dados vão até 30/09/2026; o problema pode ter sido resolvido depois.</p>
        </>
      )}
    </section>
  );
}
