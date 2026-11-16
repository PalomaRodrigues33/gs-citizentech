import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function Sobre() {
  const [d, setD] = useState(null);
  useEffect(() => { api.sobre().then(setD).catch(() => setD({})); }, []);
  const m = d?.modelo_7_dias, a = d?.assistente;
  return (
    <section className="screen sobre" aria-labelledby="t-sobre">
      <h1 id="t-sobre" className="screen-title">Como funciona</h1>
      <p className="lede">O CitizenTech mostra quanto tempo a Prefeitura leva para resolver problemas de rua e calçada no seu bairro e ajuda você a abrir o pedido certo no SP156. Ele não substitui o SP156: quem recebe e resolve é a Prefeitura.</p>

      <h2>De onde vêm os dados</h2>
      <p>Dos pedidos feitos ao SP156 entre julho e setembro de 2026, publicados pela Prefeitura no <a href="https://dados.prefeitura.sp.gov.br/dataset/dados-do-sp156" target="_blank" rel="noopener noreferrer">Portal de Dados Abertos</a>. São 84.487 pedidos de buraco, calçada e acessibilidade, entulho, varrição e bueiro. O arquivo não tem nome nem contato de quem pediu.</p>

      <h2>O que a inteligência artificial faz</h2>
      <ul>
        <li><b>Entende o seu relato</b> e escolhe, entre 13 serviços do SP156, aquele em que o pedido deve ser aberto. Também escreve o texto e avisa o que falta informar.</li>
        <li><b>Estima a chance de solução em 7 dias</b>, aprendendo com o histórico do tipo de problema e da região.</li>
      </ul>
      {m && (
        <table className="metricas">
          <tbody>
            <tr><th>Previsão testada em</th><td className="n">{m.teste.pedidos.toLocaleString("pt-BR")} pedidos de setembro</td></tr>
            <tr><th>Acerto ao ordenar o risco (AUC) sem IA</th><td className="n">{m.antes_sem_ia.auc.toFixed(2).replace(".", ",")}</td></tr>
            <tr><th>Com IA</th><td className="n">{m.depois_com_ia.auc.toFixed(2).replace(".", ",")}</td></tr>
          </tbody>
        </table>
      )}
      {a?.antes_sem_ia && (
        <p className="muted small">Escolha do serviço, em {a.antes_sem_ia.casos} relatos de teste: {Math.round(100 * a.antes_sem_ia.acuracia_servico)}% com regras simples
          {a.depois_com_ia ? `, ${Math.round(100 * a.depois_com_ia.acuracia_servico)}% com o modelo de linguagem` : ""}.
          {!a.depois_com_ia && " As regras foram escritas olhando esses mesmos relatos, então esse número é otimista."}</p>
      )}

      <h2>O que os números não dizem</h2>
      <ul>
        <li>"Finalizado" no SP156 quer dizer que o pedido foi encerrado, não necessariamente que o problema foi consertado.</li>
        <li>A chance de solução é uma estimativa estatística, não um prazo prometido pela Prefeitura.</li>
        <li>Os dados vão até 30/09/2026. Um problema da lista de atrasos pode ter sido resolvido depois.</li>
        <li>A manutenção da calçada em frente a um imóvel é responsabilidade do dono; a Prefeitura fiscaliza.</li>
        <li>Os números são da subprefeitura que atende o seu bairro, não do bairro sozinho: em muitos distritos os pedidos de um tipo são poucos demais para um número confiável.</li>
      </ul>

      <h2>Privacidade</h2>
      <p>O app não pede nome, e-mail, telefone ou documento e não guarda o seu pedido. O texto que você escreve é usado só para montar o pedido.</p>

      <h2>Em caso de emergência</h2>
      <p>Risco imediato à vida, como fio caído ou desabamento: ligue <a href="tel:193">193</a> (Bombeiros) ou <a href="tel:199">199</a> (Defesa Civil).</p>
    </section>
  );
}
