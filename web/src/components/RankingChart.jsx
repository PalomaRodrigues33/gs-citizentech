import { useState } from "react";
import { fmt } from "./TempoChart.jsx";

// "Como a sua região se compara?" — as subprefeituras da mais rápida à mais lenta; a sua em azul.
export default function RankingChart({ dados, destaque }) {
  const [i, setI] = useState(null);
  const W = 340, H = 120, T = 8, B = 22, n = dados.length;
  if (!n) return null;
  const gap = 2, bw = (W - gap * (n - 1)) / n;
  const y = (v) => T + ((100 - v) * (H - T - B)) / 100;
  const sua = dados.findIndex((d) => d.subprefeitura === destaque);
  return (
    <div className="viz">
      <svg viewBox={`0 0 ${W} ${H}`} role="img"
        aria-label={`Subprefeituras ordenadas pelo percentual resolvido em até 7 dias${sua >= 0 ? `; ${destaque} é a ${sua + 1}ª de ${n}` : ""}`}>
        {dados.map((d, k) => {
          const x = k * (bw + gap), top = y(d.resolvidos_7d_pct);
          return (
            <g key={d.subprefeitura}>
              <path className={k === sua ? "rank-sua" : "rank-outra"}
                d={`M${x},${H - B} V${top + 2} q0,-2 2,-2 h${bw - 4} q2,0 2,2 V${H - B} Z`} />
              <rect className="rank-hit" x={x - gap / 2} y={T} width={bw + gap} height={H - T - B}
                onPointerEnter={() => setI(k)} onPointerDown={() => setI(k)} onPointerLeave={() => setI(null)} />
            </g>
          );
        })}
        <text className="eixo" x="0" y={H - 6}>mais rápida</text>
        <text className="eixo" x={W} y={H - 6} textAnchor="end">mais lenta</text>
      </svg>
      {i !== null && (
        <div className="tip" style={{ left: `${Math.min(80, Math.max(20, ((i + 0.5) / n) * 100))}%`, top: 24 }}>
          {dados[i].posicao}ª {dados[i].subprefeitura}: {fmt(dados[i].resolvidos_7d_pct)}
        </div>
      )}
      <details className="tabela">
        <summary>Ver em tabela</summary>
        <table>
          <thead><tr><th>Posição</th><th>Subprefeitura</th><th className="n">Em até 7 dias</th></tr></thead>
          <tbody>
            {dados.map((d) => (
              <tr key={d.subprefeitura}>
                <td>{d.posicao}ª</td>
                <td>{d.subprefeitura === destaque ? <b>{d.subprefeitura}</b> : d.subprefeitura}</td>
                <td className="n">{fmt(d.resolvidos_7d_pct)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
