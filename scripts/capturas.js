// Capturas das 4 telas para o PDF (iPhone 13 simulado, claro e escuro).
// Uso (com a API rodando em http://localhost:8000):  node scripts/capturas.js
// Requer o Playwright: npm i -D playwright && npx playwright install chromium
const { chromium, devices } = require("playwright");
const path = require("path");

(async () => {
  const out = path.join(__dirname, "..", "capturas", "telas");
  const browser = await chromium.launch();
  for (const scheme of ["light", "dark"]) {
    const ctx = await browser.newContext({ ...devices["iPhone 13"], deviceScaleFactor: 2, colorScheme: scheme });
    const p = await ctx.newPage();
    await p.goto("http://localhost:8000/");
    // na captura de página inteira, a barra de abas vai para o fim da página (no uso real ela fica fixa)
    await p.addStyleTag({ content: "html{position:relative} .tabbar{position:absolute !important}" });
    await p.waitForSelector(".hero-num");
    await p.selectOption(".placa select", "MOOCA");
    await p.waitForTimeout(700);
    await p.screenshot({ path: `${out}/1-meu-bairro-${scheme}.png`, fullPage: true });
    await p.click(".tab >> text=Fazer pedido");
    await p.fill("textarea", "A calçada em frente à padaria da Rua Tobias Barreto está toda quebrada desde o mês passado e minha avó tropeçou lá.");
    await p.click("button[type=submit]");
    await p.waitForSelector(".texto-pedido");
    await p.screenshot({ path: `${out}/2-fazer-pedido-${scheme}.png`, fullPage: true });
    await p.click(".tab >> text=Atrasos");
    await p.waitForSelector(".item");
    await p.screenshot({ path: `${out}/3-atrasos-${scheme}.png`, fullPage: true });
    await p.click(".tab >> text=Como funciona");
    await p.waitForSelector(".metricas");
    await p.screenshot({ path: `${out}/4-como-funciona-${scheme}.png`, fullPage: true });
    await ctx.close();
  }
  await browser.close();
  console.log("Capturas em", out);
})();
