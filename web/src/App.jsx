import { useEffect, useState } from "react";
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
  const [sub, setSubState] = useState(prefs.get("subprefeitura"));
  const [grupo, setGrupo] = useState(null);
  const [preenchido, setPreenchido] = useState(null);

  useEffect(() => {
    api.regioes().then((r) => {
      setRegioes(r.subprefeituras);
      setGrupos(r.grupos);
      if (!sub || !r.subprefeituras[sub]) setSubState(Object.keys(r.subprefeituras)[0]);
    }).catch((e) => setErro(e.message));
  }, []); // eslint-disable-line

  const setSub = (s) => { setSubState(s); if (s) prefs.set("subprefeitura", s); };
  const irPara = (a) => { setAba(a); window.scrollTo({ top: 0 }); };
  const reforcar = (it) => {
    setPreenchido({
      subprefeitura: it.subprefeitura,
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
          <Bairro regioes={regioes} grupos={grupos} sub={sub} setSub={setSub} grupo={grupo} setGrupo={setGrupo} irPara={irPara} />
        )}
        {regioes && aba === "registrar" && (
          <Registrar regioes={regioes} sub={sub} setSub={setSub} preenchido={preenchido} limparPreenchido={() => setPreenchido(null)} />
        )}
        {regioes && aba === "atrasos" && (
          <Atrasos regioes={regioes} grupos={grupos} sub={sub} setSub={setSub} grupo={grupo} setGrupo={setGrupo} reforcar={reforcar} />
        )}
        {aba === "sobre" && <Sobre />}
      </main>
      <TabBar aba={aba} onChange={irPara} />
    </>
  );
}
