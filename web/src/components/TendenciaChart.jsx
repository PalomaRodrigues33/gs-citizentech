import { useRef, useState } from "react";
import { fmt } from "./TempoChart.jsx";

const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const dataCurta = (iso) => { const [, m, d] = iso.split("-"); return `${+d} ${MESES[+m - 1]}`; };

// "A sua região está melhorando?" — média móvel de 3 semanas, região (azul) x cidade (tracejado cinza).
export default function TendenciaChart({ dados }) {
  const W = 340, H = 180, L = 34, R = 92, T = 12, B = 26;
  const pts = dados.filter((d) => d.cidade_pct !== null);
  const [i, setI] = useState(null);
  const ref = useRef(null);
  if (pts.length < 2) return null;

  const x = (k) => L + (k * (W - L - R)) / (pts.length - 1);
  const y = (v) => T + ((100 - v) * (H - T - B)) / 100;
  const path = (key) => {
    let d = "", pen = false;
    pts.forEach((p, k) => {
      if (p[key] === null) { pen = false; return; }
      d += `${pen ? "L" : "M"}${x(k).toFixed(1)},${y(p[key]).toFixed(1)}`;
      pen = true;
    });
    return d;
  };
  const ultimo = (key) => { for (let k = pts.length - 1; k >= 0; k--) if (pts[k][key] !== null) return k; return null; };
  const kr = ultimo("regiao_pct"), kc = ultimo("cidade_pct");
  // evita que os rótulos do fim das linhas se sobreponham
  let yr = kr !== null ? y(pts[kr].regiao_pct) : null, yc = y(pts[kc].cidade_pct);
  if (yr !== null && Math.abs(yr - yc) < 16) { const mid = (yr + yc) / 2; if (yr < yc) { yr = mid - 8; yc = mid + 8; } else { yr = mid + 8; yc = mid - 8; } }

  const mover = (ev) => {
    const box = ref.current.getBoundingClientRect();
    const px = ((ev.clientX - box.left) / box.width) * W;
    const k = Math.round(((px - L) / (W - L - R)) * (pts.length - 1));
    setI(Math.max(0, Math.min(pts.length - 1, k)));
  };
  const meses = [];
  pts.forEach((p, k) => { const m = p.inicio.slice(5, 7); if (!meses.find((q) => q.m === m)) meses.push({ m, k }); });

  return (
    <div className="viz">
      <div className="legenda" aria-hidden="true">
        <span><i className="sw" /> Sua região</span>
        <span><i className="sw-line" /> Cidade</span>
      </div>
      <svg ref={ref} viewBox={`0 0 ${W} ${H}`} role="img"
        aria-label="Percentual de pedidos resolvidos em até 7 dias por semana, média móvel de 3 semanas, região e cidade"
        onPointerMove={mover} onPointerDown={mover} onPointerLeave={() => setI(null)}>
        {[0, 50, 100].map((v) => (
          <g key={v}>
            <line className="grade" x1={L} x2={W - R} y1={y(v)} y2={y(v)} />
            <text className="eixo" x={L - 6} y={y(v) + 4} textAnchor="end">{v}%</text>
          </g>
        ))}
        {meses.map(({ m, k }) => (
          <text key={m} className="eixo" x={x(k)} y={H - 6} textAnchor="start">{MESES[+m - 1]}</text>
        ))}
        <path className="linha-cidade" d={path("cidade_pct")} />
        <path className="linha-regiao" d={path("regiao_pct")} />
        {kr !== null && <circle className="ponto-regiao" cx={x(kr)} cy={y(pts[kr].regiao_pct)} r="4.5" />}
        {kr !== null && <text className="rotulo-fim" x={x(kr) + 9} y={yr + 4}>Região {fmt(pts[kr].regiao_pct)}</text>}
        <text className="rotulo-fim-2" x={x(kc) + 9} y={yc + 4}>Cidade {fmt(pts[kc].cidade_pct)}</text>
        {i !== null && <line className="cruz" x1={x(i)} x2={x(i)} y1={T} y2={H - B} />}
      </svg>
      {i !== null && (
        <div className="tip" style={{ left: `${(x(i) / W) * 100}%`, top: 34 }}>
          Semana de {dataCurta(pts[i].inicio)}: região {fmt(pts[i].regiao_pct)}, cidade {fmt(pts[i].cidade_pct)}
        </div>
      )}
      <details className="tabela">
        <summary>Ver em tabela</summary>
        <table>
          <thead><tr><th>Semana de</th><th className="n">Região</th><th className="n">Cidade</th><th className="n">Pedidos na região</th></tr></thead>
          <tbody>
            {pts.map((p) => (
              <tr key={p.semana}><td>{dataCurta(p.inicio)}</td><td className="n">{fmt(p.regiao_pct)}</td><td className="n">{fmt(p.cidade_pct)}</td><td className="n">{p.pedidos}</td></tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
