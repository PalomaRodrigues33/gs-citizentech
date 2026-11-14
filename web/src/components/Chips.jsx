export default function Chips({ opcoes, valor, onChange, rotulo }) {
  return (
    <div className="chips" role="group" aria-label={rotulo}>
      <button type="button" className="chip" aria-pressed={!valor} onClick={() => onChange(null)}>Todos</button>
      {opcoes.map((o) => (
        <button type="button" key={o} className="chip" aria-pressed={valor === o} onClick={() => onChange(o)}>{o}</button>
      ))}
    </div>
  );
}
