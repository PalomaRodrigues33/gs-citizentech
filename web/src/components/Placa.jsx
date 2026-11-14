// A placa azul das ruas de São Paulo: mostra a região escolhida e é, ela mesma, o seletor.
export default function Placa({ kicker, nome, rodape, opcoes, valor, onChange, rotulo }) {
  return (
    <div className="placa">
      <div className="placa-kicker">{kicker}</div>
      <div className="placa-nome">{nome || "Escolha"}</div>
      <div className="placa-rodape">
        <span>{rodape}</span>
        {opcoes && <span aria-hidden="true">trocar ▾</span>}
      </div>
      {opcoes && (
        <select aria-label={rotulo} value={valor || ""} onChange={(e) => onChange(e.target.value)}>
          {!valor && <option value="">Escolha…</option>}
          {opcoes.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      )}
    </div>
  );
}
