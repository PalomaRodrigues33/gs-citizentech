const ICONES = {
  bairro: <><path d="M12 21s-7-6.1-7-11.5A7 7 0 0 1 19 9.5C19 14.9 12 21 12 21Z" /><circle cx="12" cy="9.5" r="2.5" /></>,
  registrar: <><path d="M4 20h4L19 9l-4-4L4 16v4Z" /><path d="M13.5 6.5l4 4" /></>,
  atrasos: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></>,
  sobre: <><circle cx="12" cy="12" r="8.5" /><path d="M12 11v5.5M12 7.8v.2" /></>,
};
const ABAS = [
  ["bairro", "Meu bairro"],
  ["registrar", "Fazer pedido"],
  ["atrasos", "Atrasos"],
  ["sobre", "Como funciona"],
];

export default function TabBar({ aba, onChange }) {
  return (
    <nav className="tabbar" aria-label="Seções">
      <div className="tabbar-inner">
        {ABAS.map(([id, nome]) => (
          <button key={id} type="button" className="tab" aria-current={aba === id ? "page" : undefined} onClick={() => onChange(id)}>
            <svg viewBox="0 0 24 24" aria-hidden="true">{ICONES[id]}</svg>
            {nome}
          </button>
        ))}
      </div>
    </nav>
  );
}
