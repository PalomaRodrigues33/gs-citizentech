// A placa azul das ruas de São Paulo: mostra a região escolhida e é, ela mesma, o seletor.
// O cidadão escolhe pelo bairro, que é o que ele sabe; as opções vêm agrupadas pela subprefeitura.
export default function Placa({ kicker, nome, rodape, agrupadas, valor, onChange, rotulo }) {
  return (
    <div className="placa">
      <div className="placa-kicker">{kicker}</div>
      <div className="placa-nome">{nome || "Escolha"}</div>
      <div className="placa-rodape">
        <span>{rodape}</span>
        {agrupadas && <span aria-hidden="true">trocar ▾</span>}
      </div>
      {agrupadas && (
        <select aria-label={rotulo} value={valor || ""} onChange={(e) => onChange(e.target.value)}>
          {!valor && <option value="">Escolha…</option>}
          {Object.entries(agrupadas).map(([regiao, distritos]) => (
            <optgroup key={regiao} label={regiao}>
              {distritos.map((d) => <option key={d} value={d}>{d}</option>)}
            </optgroup>
          ))}
        </select>
      )}
    </div>
  );
}
