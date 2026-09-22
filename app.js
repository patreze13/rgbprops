// Dados iniciais de demonstração (serão alimentados pelo script Python oficial)
const DADOS_AMOSTRA = [
    {
        id: "1",
        esporte: "WNBA",
        evento: "Las Vegas Aces x Seattle Storm",
        dia: "hoje",
        hora: "23:00",
        mercado_tag: "PTS ATLETA",
        linha_desc: "A'ja Wilson • Over 26.5",
        l5: 100,
        l10: 90,
        l20: 85,
        match: "A",
        score: 96,
        chart: [true, true, true, true, true, true, true, false, true, true]
    },
    {
        id: "2",
        esporte: "WNBA",
        evento: "Las Vegas Aces x Seattle Storm",
        dia: "hoje",
        hora: "23:00",
        mercado_tag: "3PTS ATLETA",
        linha_desc: "Kelsey Plum • Over 2.5",
        l5: 80,
        l10: 70,
        l20: 75,
        match: "A",
        score: 88,
        chart: [true, true, false, true, true, true, false, true, true, false]
    },
    {
        id: "3",
        esporte: "Futebol",
        evento: "Criciúma x Operário-PR",
        dia: "amanha",
        hora: "19:30",
        mercado_tag: "GOLS",
        linha_desc: "Under 2.5 Gols",
        l5: 80,
        l10: 80,
        l20: 75,
        match: "A",
        score: 84,
        chart: [true, true, true, false, true, true, false, true, true, true]
    }
];

let esporteAtivo = "todos";
let diaAtivo = "hoje";

function corPct(val) {
    if (val >= 75) return "val-green";
    if (val >= 60) return "val-yellow";
    return "val-red";
}

function renderizarCards(lista) {
    const container = document.getElementById("listaCards");
    const contador = document.getElementById("contagemLinhas");
    
    contador.innerText = `${lista.length} linhas analíticas ativas encontradas.`;
    container.innerHTML = "";

    if (lista.length === 0) {
        container.innerHTML = `<div style="padding: 20px; color: #868e96; text-align: center;">Nenhuma oportunidade encontrada para esses filtros.</div>`;
        return;
    }

    lista.forEach(item => {
        const barrasHtml = item.chart.map(hit => 
            `<div class="${hit ? 'bar-hit' : 'bar-miss'}"></div>`
        ).join("");

        const card = document.createElement("div");
        card.className = "prop-card";
        card.innerHTML = `
            <div class="card-info">
                <div>
                    <span class="badge-tag">${item.mercado_tag}</span>
                    <span class="game-time">${item.hora} • ${item.esporte}</span>
                </div>
                <div class="game-title">${item.evento}</div>
            </div>

            <div class="line-desc">${item.linha_desc}</div>

            <div class="stats-group">
                <div class="stat-item">
                    <span class="stat-label">CHART</span>
                    <div class="chart-bars">${barrasHtml}</div>
                </div>
                <div class="stat-item">
                    <span class="stat-label">L5%</span>
                    <span class="stat-value ${corPct(item.l5)}">${item.l5}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">L10%</span>
                    <span class="stat-value ${corPct(item.l10)}">${item.l10}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">L20%</span>
                    <span class="stat-value ${corPct(item.l20)}">${item.l20}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">MATCH</span>
                    <span class="badge-match">${item.match}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">SCORE</span>
                    <span class="score-text">${item.score}</span>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

function executarFiltroGeral() {
    const termo = document.getElementById("campoBusca").value.toLowerCase();
    
    let filtrados = DADOS_AMOSTRA.filter(item => {
        const bateEsporte = (esporteAtivo === "todos" || item.esporte === esporteAtivo);
        const bateDia = (diaAtivo === "todos" || item.dia === diaAtivo);
        const bateBusca = !termo || item.evento.toLowerCase().includes(termo) || item.linha_desc.toLowerCase().includes(termo);
        return bateEsporte && bateDia && bateBusca;
    });

    renderizarCards(filtrados);
}

function filtrarEsporte(esp, btn) {
    esporteAtivo = esp;
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    executarFiltroGeral();
}

function filtrarDia(dia, btn) {
    diaAtivo = dia;
    document.querySelectorAll(".filter-pill").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    executarFiltroGeral();
}

// Inicializar na carga
document.addEventListener("DOMContentLoaded", () => {
    executarFiltroGeral();
});