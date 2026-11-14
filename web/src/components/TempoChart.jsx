import { useState } from "react";

// "Quanto tempo cada tipo leva aqui?" — barra = sua região; traço = média da cidade.
export default function TempoChart({ dados, destaque }) {
  const [ativo, setAtivo] = useState(null);
  return (
    <div>
      <div className="legenda" aria-hidden="true">
        <span><i className="sw" /> Sua região</span>
        <span><i className="sw-tick" /> Média da cidade</span>
      </div>
      <div className="barras">
        {dados.map((d) => {
          const sem = d.regiao_pct === null || d.pedidos_regiao < 20;
          const desc = sem
            ? `${d.grupo}: poucos pedidos na região. Cidade: ${fmt(d.cidade_pct)} resolvidos em até 7 dias.`
            : `${d.grupo}: ${fmt(d.regiao_pct)} resolvidos em até 7 dias na região, contra ${fmt(d.cidade_pct)} na cidade.`;
          return (
            <button
              type="button" key={d.grupo} className="barra-linha" aria-label={desc}
              onMouseEnter={() => setAtivo(d.grupo)} onMouseLeave={() => setAtivo(null)}
              onFocus={() => setAtivo(d.grupo)} onBlur={() => setAtivo(null)}
              onClick={() => setAtivo(ativo === d.grupo ? null : d.grupo)}
            >
              <span className="barra-rotulo">
                {d.grupo === destaque ? <b>{d.grupo}</b> : <span>{d.grupo}</span>}
                {sem ? <span className="barra-sem">poucos pedidos</span> : <span className="barra-valor">{fmt(d.regiao_pct)}</span>}
              </span>
              <span className="barra-trilho">
                {!sem && <span className="barra-fill" style={{ width: `${d.regiao_pct}%` }} />}
                <span className="barra-tick" style={{ left: `${d.cidade_pct}%` }} />
              </span>
              {ativo === d.grupo && (
                <span className="tip" style={{ left: "50%", top: 0 }}>
                  Cidade: {fmt(d.cidade_pct)}
                  {!sem && d.regiao_mediana_dias !== null && <>; metade leva até {dias(d.regiao_mediana_dias)}</>}
                </span>
              )}
            </button>
          );
        })}
      </div>
      <details className="tabela">
        <summary>Ver em tabela</summary>
        <table>
          <thead><tr><th>Tipo</th><th className="n">Região</th><th className="n">Cidade</th><th className="n">Mediana</th></tr></thead>
          <tbody>
            {dados.map((d) => (
              <tr key={d.grupo}>
                <td>{d.grupo}</td><td className="n">{fmt(d.regiao_pct)}</td><td className="n">{fmt(d.cidade_pct)}</td>
                <td className="n">{d.regiao_mediana_dias === null ? "—" : dias(d.regiao_mediana_dias)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}

export const fmt = (v) => (v === null || v === undefined ? "—" : `${Math.round(v)}%`);
export const dias = (v) => `${Math.round(v)} dia${Math.round(v) === 1 ? "" : "s"}`;
