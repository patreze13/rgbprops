import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import os

# 1. Configuração da Página
st.set_page_config(
    page_title="RGBProps - Mesa Analítica",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "fixadas" not in st.session_state:
    st.session_state.fixadas = []

# 2. Design System: Fundo #25262B e Cards de Alta Densidade
st.markdown("""
<style>
    .stApp, .reportview-container, .main, [data-testid="stSidebar"] {
        background-color: #25262B !important;
        color: #FFFFFF;
    }
    header[data-testid="stHeader"] {
        background-color: #25262B !important;
    }
    .prop-row {
        background-color: #1A1B1E;
        border: 1px solid #2C2E33;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        transition: border-color 0.2s;
    }
    .prop-row:hover {
        border-color: #4dabf7;
    }
    .badge-mercado {
        background-color: #202227;
        border: 1px solid #373A40;
        color: #4dabf7;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        padding: 3px 6px;
        border-radius: 4px;
    }
    .linha-tag {
        font-size: 0.95rem;
        font-weight: 800;
        color: #F8F9FA;
    }
    .odd-box {
        background-color: #2b2c31;
        border: 1px solid #495057;
        color: #fab005;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .stat-cell {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 42px;
    }
    .stat-label {
        color: #868e96;
        font-size: 0.62rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .stat-val {
        font-size: 0.82rem;
        font-weight: 700;
    }
    .val-high { color: #40c057; }
    .val-med  { color: #fab005; }
    .val-low  { color: #fa5252; }
    
    .chart-container {
        display: flex;
        align-items: flex-end;
        gap: 2px;
        height: 20px;
    }
    .chart-bar-hit {
        width: 4px;
        height: 18px;
        background-color: #40c057;
        border-radius: 1px;
    }
    .chart-bar-miss {
        width: 4px;
        height: 6px;
        background-color: #fa5252;
        border-radius: 1px;
    }
    .badge-match-a { background-color: #2b8a3e; color: #fff; font-weight: 800; padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; }
    .badge-match-b { background-color: #e67700; color: #fff; font-weight: 800; padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; }
    .badge-match-c { background-color: #c92a2a; color: #fff; font-weight: 800; padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; }
    
    .score-val {
        font-size: 1rem;
        font-weight: 900;
        color: #69db7c;
        min-width: 32px;
        text-align: right;
    }
    .vant-val {
        font-size: 0.95rem;
        font-weight: 800;
        color: #51cf66;
        min-width: 45px;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# 3. Cabeçalho
col_logo, col_titulo, col_data = st.columns([1, 6, 2])
with col_logo:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=85)
    else:
        st.write("🎯")

with col_titulo:
    st.markdown("<h2 style='margin:0; padding:0;'>RGBProps</h2>", unsafe_allow_html=True)
    st.caption("Mesa Analítica • Estatísticas Avançadas (L5, L10, L20, H2H, Score)")

with col_data:
    filtro_dia = st.radio(
        "Calendário",
        options=["Hoje", "Amanhã", "Todos"],
        index=0,
        horizontal=True,
        label_visibility="collapsed"
    )

st.divider()

# 4. Barra Lateral de Filtros
st.sidebar.header("⚙️ Painel de Operações")
busca_termo = st.sidebar.text_input("🔍 Pesquisar Atleta / Confronto", placeholder="Ex: Wilson, Plum, Criciúma...")
ordenar_por = st.sidebar.selectbox("Classificar Por", ["Score Geral", "Vantagem (+EV)", "L5%", "Odd"])
categoria_filtro = st.sidebar.selectbox("Mercados", ["Todos", "Pontos", "Rebotes", "Assistências", "Triplos", "Quartos/Metades", "Totais"])
min_odd = st.sidebar.number_input("Odd Mínima", min_value=1.10, max_value=6.00, value=1.35, step=0.05)
tipo_filtro = st.sidebar.radio("Tipo", ["Todos", "Over", "Under"], horizontal=True)

# 5. Base de Dados do Motor Analítico
def gerar_dados_operacionais():
    tz_br = timezone(timedelta(hours=-3))
    agora_br = datetime.now(tz_br)
    hoje = agora_br.strftime("%Y-%m-%d")
    amanha = (agora_br + timedelta(days=1)).strftime("%Y-%m-%d")

    catalogo = [
        # WNBA - Confronto Hoje
        {"esp": "WNBA", "ev": "Las Vegas Aces x Seattle Storm", "dia": hoje, "hora": "23:00",
         "cat": "Pontos", "tag": "PTS ATLETA", "desc": "A'ja Wilson • Over 26.5", "tipo": "Over", "odd": 1.85, "hit_rate": 0.85},
        {"esp": "WNBA", "ev": "Las Vegas Aces x Seattle Storm", "dia": hoje, "hora": "23:00",
         "cat": "Rebotes", "tag": "REB ATLETA", "desc": "A'ja Wilson • Over 11.5", "tipo": "Over", "odd": 1.78, "hit_rate": 0.80},
        {"esp": "WNBA", "ev": "Las Vegas Aces x Seattle Storm", "dia": hoje, "hora": "23:00",
         "cat": "Triplos", "tag": "3PTS ATLETA", "desc": "Kelsey Plum • Over 2.5", "tipo": "Over", "odd": 1.92, "hit_rate": 0.75},
        {"esp": "WNBA", "ev": "Las Vegas Aces x Seattle Storm", "dia": hoje, "hora": "23:00",
         "cat": "Assistências", "tag": "ASSIST ATLETA", "desc": "Chelsea Gray • Over 5.5", "tipo": "Over", "odd": 1.70, "hit_rate": 0.80},
        {"esp": "WNBA", "ev": "Las Vegas Aces x Seattle Storm", "dia": hoje, "hora": "23:00",
         "cat": "Pontos", "tag": "PTS ATLETA", "desc": "Jewell Loyd • Under 19.5", "tipo": "Under", "odd": 1.88, "hit_rate": 0.70},
        {"esp": "WNBA", "ev": "Las Vegas Aces x Seattle Storm", "dia": hoje, "hora": "23:00",
         "cat": "Quartos/Metades", "tag": "1Q TOTAL", "desc": "Over 41.5 Pontos (1º Quarto)", "tipo": "Over", "odd": 1.80, "hit_rate": 0.75},
        {"esp": "WNBA", "ev": "Las Vegas Aces x Seattle Storm", "dia": hoje, "hora": "23:00",
         "cat": "Quartos/Metades", "tag": "1T TOTAL", "desc": "Over 82.5 Pontos (1º Tempo)", "tipo": "Over", "odd": 1.85, "hit_rate": 0.80},
        {"esp": "WNBA", "ev": "Las Vegas Aces x Seattle Storm", "dia": hoje, "hora": "23:00",
         "cat": "Totais", "tag": "TOTAL JOGO", "desc": "Under 168.5 Pontos", "tipo": "Under", "odd": 1.90, "hit_rate": 0.65},

        # WNBA - Confronto Amanhã
        {"esp": "WNBA", "ev": "New York Liberty x Connecticut Sun", "dia": amanha, "hora": "20:30",
         "cat": "Pontos", "tag": "PTS ATLETA", "desc": "Breanna Stewart • Over 20.5", "tipo": "Over", "odd": 1.82, "hit_rate": 0.80},
        {"esp": "WNBA", "ev": "New York Liberty x Connecticut Sun", "dia": amanha, "hora": "20:30",
         "cat": "Rebotes", "tag": "REB ATLETA", "desc": "Jonquel Jones • Over 8.5", "tipo": "Over", "odd": 1.75, "hit_rate": 0.75},
        {"esp": "WNBA", "ev": "New York Liberty x Connecticut Sun", "dia": amanha, "hora": "20:30",
         "cat": "Assistências", "tag": "ASSIST ATLETA", "desc": "Sabrina Ionescu • Over 6.0", "tipo": "Over", "odd": 1.95, "hit_rate": 0.70},
        {"esp": "WNBA", "ev": "New York Liberty x Connecticut Sun", "dia": amanha, "hora": "20:30",
         "cat": "Quartos/Metades", "tag": "1Q TOTAL", "desc": "Under 39.5 Pontos (1º Quarto)", "tipo": "Under", "odd": 1.85, "hit_rate": 0.75},

        # NBA
        {"esp": "NBA", "ev": "Boston Celtics x Miami Heat", "dia": hoje, "hora": "21:00",
         "cat": "Pontos", "tag": "PTS ATLETA", "desc": "Jayson Tatum • Over 27.5", "tipo": "Over", "odd": 1.88, "hit_rate": 0.80},
        {"esp": "NBA", "ev": "Boston Celtics x Miami Heat", "dia": hoje, "hora": "21:00",
         "cat": "Triplos", "tag": "3PTS ATLETA", "desc": "Jaylen Brown • Over 2.5", "tipo": "Over", "odd": 1.95, "hit_rate": 0.75},
        {"esp": "NBA", "ev": "Boston Celtics x Miami Heat", "dia": hoje, "hora": "21:00",
         "cat": "Quartos/Metades", "tag": "1Q TOTAL", "desc": "Over 54.5 Pontos (1º Quarto)", "tipo": "Over", "odd": 1.82, "hit_rate": 0.85},
        {"esp": "NBA", "ev": "Boston Celtics x Miami Heat", "dia": hoje, "hora": "21:00",
         "cat": "Quartos/Metades", "tag": "1T TOTAL", "desc": "Over 109.5 Pontos (1º Tempo)", "tipo": "Over", "odd": 1.84, "hit_rate": 0.80},

        # FUTEBOL - Brasileirão e Copas
        {"esp": "Futebol", "ev": "Criciúma x Operário-PR", "dia": amanha, "hora": "19:30",
         "cat": "Totais", "tag": "GOLS", "desc": "Under 2.5 Gols", "tipo": "Under", "odd": 1.65, "hit_rate": 0.85},
        {"esp": "Futebol", "ev": "Criciúma x Operário-PR", "dia": amanha, "hora": "19:30",
         "cat": "Quartos/Metades", "tag": "1T GOLS", "desc": "Under 0.5 Gols (1º Tempo)", "tipo": "Under", "odd": 2.20, "hit_rate": 0.65},
        {"esp": "Futebol", "ev": "Independiente Santa Fe x Millonarios", "dia": hoje, "hora": "22:00",
         "cat": "Totais", "tag": "CARTÕES", "desc": "Over 5.5 Cartões", "tipo": "Over", "odd": 1.72, "hit_rate": 0.80},
        {"esp": "Futebol", "ev": "Audax Italiano x Colo-Colo", "dia": amanha, "hora": "20:30",
         "cat": "Totais", "tag": "AMBAS", "desc": "Ambas Marcam: Sim", "tipo": "Over", "odd": 1.80, "hit_rate": 0.75}
    ]

    itens_processados = []
    for idx, c in enumerate(catalogo):
        seed = int(abs(hash(f"{c['desc']}_{c['dia']}"))) % (2**31)
        rng = np.random.default_rng(seed)

        # Geração das amostras históricas L5, L10, L20
        base_rate = c["hit_rate"]
        amostra_20 = (rng.uniform(0, 1, 20) < base_rate).tolist()

        l5 = int(np.mean(amostra_20[:5]) * 100)
        l10 = int(np.mean(amostra_20[:10]) * 100)
        l20 = int(np.mean(amostra_20) * 100)
        chart = amostra_20[:10]

        prob_odd = (1 / c["odd"]) * 100
        prob_modelo = base_rate * 100
        vant = round(prob_modelo - prob_odd, 1)

        score = int(np.clip((l10 * 0.45) + (prob_modelo * 0.3) + (vant * 1.2), 1, 99))
        match = "A" if score >= 80 else ("B" if score >= 65 else "C")

        itens_processados.append({
            "id": f"item_{idx}_{c['esp']}",
            "esporte": c["esp"],
            "evento": c["ev"],
            "dia": c["dia"],
            "hora": c["hora"],
            "categoria": c["cat"],
            "mercado_tag": c["tag"],
            "linha_desc": c["desc"],
            "tipo": c["tipo"],
            "odd": c["odd"],
            "vant": vant,
            "score": score,
            "match": match,
            "l5": l5,
            "l10": l10,
            "l20": l20,
            "chart": chart
        })

    return itens_processados, hoje, amanha

dados, hoje_str, amanha_str = gerar_dados_operacionais()

def cor_pct(val):
    return "val-high" if val >= 75 else ("val-med" if val >= 60 else "val-low")

# 6. Renderizador de Lista
def renderizar(lista, prefix):
    if filtro_dia == "Hoje":
        filtrados = [d for d in lista if d["dia"] == hoje_str]
    elif filtro_dia == "Amanhã":
        filtrados = [d for d in lista if d["dia"] == amanha_str]
    else:
        filtrados = lista

    filtrados = [d for d in filtrados if d["odd"] >= min_odd]

    if categoria_filtro != "Todos":
        filtrados = [d for d in filtrados if d["categoria"] == categoria_filtro]

    if tipo_filtro != "Todos":
        filtrados = [d for d in filtrados if d["tipo"].lower() == tipo_filtro.lower()]

    if busca_termo:
        t = busca_termo.lower()
        filtrados = [d for d in filtrados if t in d["evento"].lower() or t in d["linha_desc"].lower()]

    if ordenar_por == "Score Geral":
        filtrados = sorted(filtrados, key=lambda x: x["score"], reverse=True)
    elif ordenar_por == "Vantagem (+EV)":
        filtrados = sorted(filtrados, key=lambda x: x["vant"], reverse=True)
    elif ordenar_por == "L5%":
        filtrados = sorted(filtrados, key=lambda x: x["l5"], reverse=True)
    elif ordenar_por == "Odd":
        filtrados = sorted(filtrados, key=lambda x: x["odd"], reverse=True)

    st.caption(f"**{len(filtrados)}** linhas analíticas ativas.")

    if not filtrados:
        st.info("Nenhuma oportunidade para os filtros atuais.")
        return

    ids_fixados = [x["id"] for x in st.session_state.fixadas]

    for item in filtrados:
        is_fix = item["id"] in ids_fixados
        badge_match = f"badge-match-{item['match'].lower()}"

        bars_html = "".join([
            f'<div class="chart-bar-hit"></div>' if b else f'<div class="chart-bar-miss"></div>'
            for b in item["chart"]
        ])

        col_card, col_btn = st.columns([11, 1])
        with col_card:
            st.markdown(f"""
            <div class="prop-row">
                <div style="min-width: 200px;">
                    <div style="display: flex; gap: 6px; align-items: center; margin-bottom: 2px;">
                        <span class="badge-mercado">{item['mercado_tag']}</span>
                        <span style="font-size: 0.75rem; color: #868e96;">{item['hora']} • {item['dia'][5:]}</span>
                    </div>
                    <div style="font-weight: 700; font-size: 0.95rem; color: #FFFFFF;">{item['evento']}</div>
                </div>

                <div style="min-width: 200px;">
                    <div class="linha-tag">{item['linha_desc']}</div>
                    <div style="margin-top: 2px;">
                        <span class="odd-box">{item['odd']:.2f}</span>
                        <a href="https://superbet.bet.br" target="_blank" style="color:#fa5252; font-size:0.75rem; text-decoration:none; margin-left:6px; font-weight:700;">Superbet ↗</a>
                    </div>
                </div>

                <div class="stat-cell">
                    <span class="stat-label">CHART</span>
                    <div class="chart-container" style="margin-top: 3px;">{bars_html}</div>
                </div>

                <div class="stat-cell">
                    <span class="stat-label">L5%</span>
                    <span class="stat-val {cor_pct(item['l5'])}">{item['l5']}%</span>
                </div>
                <div class="stat-cell">
                    <span class="stat-label">L10%</span>
                    <span class="stat-val {cor_pct(item['l10'])}">{item['l10']}%</span>
                </div>
                <div class="stat-cell">
                    <span class="stat-label">L20%</span>
                    <span class="stat-val {cor_pct(item['l20'])}">{item['l20']}%</span>
                </div>

                <div style="text-align: right; min-width: 50px;">
                    <div class="stat-label">VANT</div>
                    <div class="vant-val">+{item['vant']}%</div>
                </div>

                <div style="text-align: center; min-width: 35px;">
                    <div class="stat-label" style="margin-bottom: 2px;">MATCH</div>
                    <span class="{badge_match}">{item['match']}</span>
                </div>

                <div style="text-align: right; min-width: 40px;">
                    <div class="stat-label">SCORE</div>
                    <div class="score-val">{item['score']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_btn:
            lbl = "❌" if is_fix else "📌"
            if st.button(lbl, key=f"{prefix}_{item['id']}", use_container_width=True):
                if is_fix:
                    st.session_state.fixadas = [x for x in st.session_state.fixadas if x["id"] != item["id"]]
                else:
                    st.session_state.fixadas.append(item)
                st.rerun()

# 7. Abas de Desportos
tab_todas, tab_nba, tab_fut, tab_wnba, tab_fix = st.tabs([
    "🔥 TODAS", "🏀 NBA", "⚽ FUTEBOL", "🎯 WNBA", f"📌 FIXADAS ({len(st.session_state.fixadas)})"
])

with tab_todas: renderizar(dados, "todas")
with tab_nba: renderizar([d for d in dados if d["esporte"] == "NBA"], "nba")
with tab_fut: renderizar([d for d in dados if d["esporte"] == "Futebol"], "fut")
with tab_wnba: renderizar([d for d in dados if d["esporte"] == "WNBA"], "wnba")
with tab_fix: renderizar(st.session_state.fixadas, "fix")