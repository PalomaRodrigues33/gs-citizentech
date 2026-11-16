import { useEffect, useMemo, useState } from "react";
import { api, prefs } from "./api.js";
import TabBar from "./components/TabBar.jsx";
import Bairro from "./screens/Bairro.jsx";
import Registrar from "./screens/Registrar.jsx";
import Atrasos from "./screens/Atrasos.jsx";
import Sobre from "./screens/Sobre.jsx";

export default function App() {
  const [aba, setAba] = useState("bairro");
  const [regioes, setRegioes] = useState(null);
  const [grupos, setGrupos] = useState([]);
  const [erro, setErro] = useState(null);
  const [distrito, setDistritoState] = useState(prefs.get("distrito"));
  const [grupo, setGrupo] = useState(null);
  const [preenchido, setPreenchido] = useState(null);

  // O cidadão escolhe o bairro; a subprefeitura sai daqui, porque ninguém sabe a sua de cor.
  const regiaoDe = useMemo(
    () => Object.fromEntries(Object.entries(regioes || {}).flatMap(([s, ds]) => ds.map((d) => [d, s]))),
    [regioes]);
  const sub = regiaoDe[distrito] || null;

  useEffect(() => {
    api.regioes().then((r) => {
      setRegioes(r.subprefeituras);
      setGrupos(r.grupos);
      const todos = Object.values(r.subprefeituras).flat();
      if (!distrito || !todos.includes(distrito)) setDistritoState(todos.sort()[0]);
    }).catch((e) => setErro(e.message));
  }, []); // eslint-disable-line

  const setDistrito = (d) => { setDistritoState(d); if (d) prefs.set("distrito", d); };
  const irPara = (a) => { setAba(a); window.scrollTo({ top: 0 }); };
  const reforcar = (it) => {
    setPreenchido({
      distrito: it.distrito,
      texto: `Problema de ${it.grupo.toLowerCase()} na ${it.logradouro || "[endereço]"}, com pedido aberto no SP156 há ${it.dias_em_aberto} dias e ainda sem solução. Também me afeta. `,
    });
    irPara("registrar");
  };

  return (
    <>
      <main className="app">
        {erro && <p className="erro" style={{ marginTop: 24 }}>{erro}</p>}
        {!regioes && !erro && <p className="carregando">Carregando…</p>}
        {regioes && aba === "bairro" && (
          <Bairro regioes={regioes} grupos={grupos} sub={sub} distrito={distrito} setDistrito={setDistrito}
            grupo={grupo} setGrupo={setGrupo} irPara={irPara} />
        )}
        {regioes && aba === "registrar" && (
          <Registrar regioes={regioes} sub={sub} distrito={distrito} setDistrito={setDistrito}
            preenchido={preenchido} limparPreenchido={() => setPreenchido(null)} />
        )}
        {regioes && aba === "atrasos" && (
          <Atrasos regioes={regioes} grupos={grupos} subPadrao={sub}
            grupo={grupo} setGrupo={setGrupo} reforcar={reforcar} />
        )}
        {aba === "sobre" && <Sobre />}
      </main>
      <TabBar aba={aba} onChange={irPara} />
    </>
  );
}
