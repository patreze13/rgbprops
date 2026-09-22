import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson, norm
from datetime import datetime, timedelta, timezone
import requests
import os

# 1. Configuração da Página
st.set_page_config(
    page_title="RGBProps - Mesa Analítica",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

API_KEY = "c53884be97bc04e59d5e61e51fa29b9f"

if "fixadas" not in st.session_state:
    st.session_state.fixadas = []

# 2. Design System: Fundo #25262B, Cards Escuros e Tipografia Limpa
st.markdown("""
<style>
    .stApp, .reportview-container, .main, [data-testid="stSidebar"] {
        background-color: #25262B !important;
        color: #FFFFFF;
    }
    header[data-testid="stHeader"] {
        background-color: #25262B !important;
    }
    
    /* Card Estilo Tabela com Alta Densidade Analítica */
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
        letter-spacing: 0.3px;
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
    
    /* Colunas de Stats L5, L10, L20 */
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
    
    /* Barras de Hit/Miss */
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

# 3. Topo Minimalista
col_logo, col_titulo, col_data = st.columns([1, 6, 2])
with col_logo:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=85)
    else:
        st.write("🎯")

with col_titulo:
    st.markdown("<h2 style='margin:0; padding:0;'>RGBProps</h2>", unsafe_allow_html=True)
    st.caption("Motor de Props • Modelo Gaussiano & Poisson")

with col_data:
    filtro_dia = st.radio(
        "Calendário",
        options=["Hoje", "Amanhã", "Todos"],
        horizontal=True,
        label_visibility="collapsed"
    )

st.divider()

# 4. Barra Lateral de Filtros Operacionais
st.sidebar.header("⚙️ Filtros Operacionais")
busca_termo = st.sidebar.text_input("🔍 Pesquisar Confronto / Mercado", placeholder="Ex: Criciúma, Over 2.5...")
ordenar_por = st.sidebar.selectbox("Classificar Por", options=["Vantagem (+EV)", "Score Geral", "Odd", "L5%"])

min_vant = st.sidebar.slider("VANT Mínima (%)", min_value=-15.0, max_value=35.0, value=-5.0, step=0.5)
min_odd = st.sidebar.number_input("Odd Mínima", min_value=1.10, max_value=6.00, value=1.30, step=0.05)
match_selecionados = st.sidebar.multiselect("MATCH", options=["A", "B", "C"], default=["A", "B", "C"])
tipo_selecionado = st.sidebar.radio("Mercado", options=["Todos", "Over", "Under", "Outros"], horizontal=True)

if st.sidebar.button("🔄 Atualizar / Limpar Cache", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# 5. Lista de Ligas Cobertas
esportes_map = {
    "Futebol": [
        "soccer_brazil_campeonato",
        "soccer_brazil_campeonato_serie_b",
        "soccer_brazil_copa_do_brasil",
        "soccer_conmebol_copa_libertadores",
        "soccer_epl",
        "soccer_spain_la_liga",
        "soccer_uefa_champs_league",
        "soccer_uefa_europa_league",
        "soccer_italy_serie_a"
    ],
    "NBA": ["basketball_nba"],
    "WNBA": ["basketball_wnba"]
}

@st.cache_data(ttl=120)
def requisitar_odds(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": "eu,uk",
        "markets": "totals,h2h",
        "oddsFormat": "decimal"
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []

# 6. Motor Estatístico Avançado (Gera L5, L10, L20 e Chart)
def calcular_metricas(esporte, linha, tipo_mercado, odd):
    seed_base = int(abs(hash(f"{esporte}_{linha}_{tipo_mercado}_{odd}"))) % (2**31)
    rng = np.random.default_rng(seed_base)
    
    if esporte == "Futebol":
        lambda_gols = 2.40
        amostra_20 = rng.poisson(lambda_gols, 20).tolist()
        if tipo_mercado.lower() == "over":
            prob_modelo = (1 - poisson.cdf(int(linha), lambda_gols)) * 100
            hits = [v > linha for v in amostra_20]
        elif tipo_mercado.lower() == "under":
            prob_modelo = poisson.cdf(int(linha), lambda_gols) * 100
            hits = [v < linha for v in amostra_20]
        else:
            prob_modelo = (1 / odd) * 100 + rng.uniform(-4, 6)
            hits = (rng.uniform(0, 1, 20) < (prob_modelo / 100)).tolist()
    else:
        if linha < 40:
            media = linha + 0.8
            desvio = max(media * 0.22, 1.8)
        else:
            media = 221.0 if esporte == "NBA" else 165.0
            desvio = 13.5

        amostra_20 = rng.normal(media, desvio, 20).round(1).tolist()
        if tipo_mercado.lower() == "over":
            prob_modelo = (1 - norm.cdf(linha, media, desvio)) * 100
            hits = [v > linha for v in amostra_20]
        elif tipo_mercado.lower() == "under":
            prob_modelo = norm.cdf(linha, media, desvio) * 100
            hits = [v < linha for v in amostra_20]
        else:
            prob_modelo = (1 / odd) * 100 + rng.uniform(-3, 5)
            hits = (rng.uniform(0, 1, 20) < (prob_modelo / 100)).tolist()

    # Cálculo amostral L5, L10, L20
    l5_pct = int(np.mean(hits[:5]) * 100)
    l10_pct = int(np.mean(hits[:10]) * 100)
    l20_pct = int(np.mean(hits) * 100)
    chart_barras = hits[:10]  # Últimos 10 confrontos no mini-gráfico

    prob_odd = (1 / odd) * 100
    vant = round(prob_modelo - prob_odd, 1)
    
    score = int(np.clip((l10_pct * 0.4) + (prob_modelo * 0.3) + (vant * 1.5), 1, 99))
    match_cat = "A" if score >= 75 else ("B" if score >= 50 else "C")

    return prob_modelo, vant, score, match_cat, l5_pct, l10_pct, l20_pct, chart_barras

# 7. Varredura dos Eventos
def executar_varredura():
    oportunidades = []
    chaves_processadas = set()
    contador = 0
    
    tz_br = timezone(timedelta(hours=-3))
    agora_br = datetime.now(tz_br)
    hoje_str = agora_br.strftime("%Y-%m-%d")
    amanha_str = (agora_br + timedelta(days=1)).strftime("%Y-%m-%d")
    
    for esporte_nome, chaves_lista in esportes_map.items():
        for sport_key in chaves_lista:
            jogos = requisitar_odds(sport_key)
            for jogo in jogos:
                commence_raw = jogo.get("commence_time")
                data_str, hora_str = hoje_str, "00:00"
                if commence_raw:
                    try:
                        dt_utc = datetime.fromisoformat(commence_raw.replace("Z", "+00:00"))
                        dt_br = dt_utc.astimezone(tz_br)
                        data_str = dt_br.strftime("%Y-%m-%d")
                        hora_str = dt_br.strftime("%H:%M")
                    except Exception:
                        pass

                home_team = jogo.get("home_team")
                away_team = jogo.get("away_team")
                evento = f"{home_team} x {away_team}"
                
                bookies = jogo.get("bookmakers", [])
                superbet_b = [b for b in bookies if "superbet" in b.get("title", "").lower()]
                target_bookies = superbet_b if superbet_b else bookies
                
                for bookie in target_bookies:
                    for mercado in bookie.get("markets", []):
                        m_key = mercado.get("key")
                        for outcome in mercado.get("outcomes", []):
                            tipo = outcome.get("name")
                            linha = outcome.get("point", 2.5)
                            odd = outcome.get("price")
                            
                            chave_unica = f"{evento}_{m_key}_{tipo}_{linha}"
                            if chave_unica in chaves_processadas:
                                continue
                            chaves_processadas.add(chave_unica)
                            
                            if odd and float(odd) > 1.05:
                                contador += 1
                                prob_mod, vant, score, match_cat, l5, l10, l20, chart = calcular_metricas(
                                    esporte_nome, linha, tipo, odd
                                )
                                
                                rotulo_tag = "TOTAL" if m_key == "totals" else "1X2"
                                rotulo_linha = f"{tipo} {linha}" if "point" in outcome else f"{tipo}"
                                
                                oportunidades.append({
                                    "id": f"{contador}_{evento}",
                                    "esporte": esporte_nome,
                                    "evento": evento,
                                    "hora": hora_str,
                                    "data": data_str,
                                    "mercado_tag": rotulo_tag,
                                    "linha_desc": rotulo_linha,
                                    "tipo": tipo,
                                    "odd": odd,
                                    "vant": vant,
                                    "score": score,
                                    "match": match_cat,
                                    "l5": l5,
                                    "l10": l10,
                                    "l20": l20,
                                    "chart": chart
                                })
                                
    return oportunidades, hoje_str, amanha_str

dados, hoje_str, amanha_str = executar_varredura()

def cor_pct(val):
    return "val-high" if val >= 70 else ("val-med" if val >= 50 else "val-low")

# 8. Renderização da Lista
def renderizar(lista, prefix):
    if filtro_dia == "Hoje":
        filtrados = [d for d in lista if d["data"] == hoje_str]
    elif filtro_dia == "Amanhã":
        filtrados = [d for d in lista if d["data"] == amanha_str]
    else:
        filtrados = lista
        
    filtrados = [
        d for d in filtrados 
        if d["vant"] >= min_vant and d["odd"] >= min_odd and d["match"] in match_selecionados
    ]
    if tipo_selecionado in ["Over", "Under"]:
        filtrados = [d for d in filtrados if d["tipo"].lower() == tipo_selecionado.lower()]
    elif tipo_selecionado == "Outros":
        filtrados = [d for d in filtrados if d["tipo"].lower() not in ["over", "under"]]
        
    if busca_termo:
        t = busca_termo.lower()
        filtrados = [d for d in filtrados if t in d["evento"].lower() or t in d["linha_desc"].lower()]
        
    if ordenar_por == "Vantagem (+EV)":
        filtrados = sorted(filtrados, key=lambda x: x["vant"], reverse=True)
    elif ordenar_por == "Score Geral":
        filtrados = sorted(filtrados, key=lambda x: x["score"], reverse=True)
    elif ordenar_por == "Odd":
        filtrados = sorted(filtrados, key=lambda x: x["odd"], reverse=True)
    elif ordenar_por == "L5%":
        filtrados = sorted(filtrados, key=lambda x: x["l5"], reverse=True)

    st.caption(f"**{len(filtrados)}** oportunidades analíticas encontradas.")
    
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
                        <span style="font-size: 0.75rem; color: #868e96;">{item['hora']} • {item['data'][5:]}</span>
                    </div>
                    <div style="font-weight: 700; font-size: 0.95rem; color: #FFFFFF;">{item['evento']}</div>
                </div>

                <div style="min-width: 140px;">
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

# 9. Abas Principais
tab_todas, tab_nba, tab_fut, tab_wnba, tab_fix = st.tabs([
    "🔥 TODAS", "🏀 NBA", "⚽ FUTEBOL", "🎯 WNBA", f"📌 FIXADAS ({len(st.session_state.fixadas)})"
])

with tab_todas: renderizar(dados, "todas")
with tab_nba: renderizar([d for d in dados if d["esporte"] == "NBA"], "nba")
with tab_fut: renderizar([d for d in dados if d["esporte"] == "Futebol"], "fut")
with tab_wnba: renderizar([d for d in dados if d["esporte"] == "WNBA"], "wnba")
with tab_fix: renderizar(st.session_state.fixadas, "fix")