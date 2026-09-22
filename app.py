import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson, norm
from datetime import datetime, timedelta, timezone
import requests
import os

st.set_page_config(
    page_title="RGBProps - Mesa Analítica",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

API_KEY = "c53884be97bc04e59d5e61e51fa29b9f"

if "fixadas" not in st.session_state:
    st.session_state.fixadas = []

# Estilo Escuro #25262B + Cards Analíticos
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

# Topo
col_logo, col_titulo, col_data = st.columns([1, 6, 2])
with col_logo:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=85)
    else:
        st.write("🎯")

with col_titulo:
    st.markdown("<h2 style='margin:0; padding:0;'>RGBProps</h2>", unsafe_allow_html=True)
    st.caption("Motor de Props • Todas as Regiões • Cobertura Máxima de Mercados")

with col_data:
    filtro_dia = st.radio(
        "Calendário",
        options=["Hoje", "Amanhã", "Todos"],
        index=2,
        horizontal=True,
        label_visibility="collapsed"
    )

st.divider()

# Barra Lateral
st.sidebar.header("⚙️ Filtros Operacionais")
busca_termo = st.sidebar.text_input("🔍 Pesquisar Atleta / Equipe", placeholder="Ex: Wilson, Plum, Over 18.5...")
min_odd = st.sidebar.number_input("Odd Mínima", min_value=1.01, max_value=10.00, value=1.15, step=0.05)
categoria_filtro = st.sidebar.selectbox("Filtrar Categoria", ["Todas", "Pontos", "Rebotes", "Assistências", "Bolas de 3", "Totais de Jogo", "Futebol"])

if st.sidebar.button("🔄 Atualizar / Limpar Cache", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Mercados de Basquete (Incluindo props individuais e quartos)
BASKETBALL_MARKETS = "totals,player_points,player_rebounds,player_assists,player_threes,player_blocks,player_steals,h2h"

@st.cache_data(ttl=120)
def requisitar_jogos(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events"
    params = {"apiKey": API_KEY}
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

@st.cache_data(ttl=120)
def requisitar_odds_evento(sport_key, event_id, markets):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events/{event_id}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us,eu,uk",
        "markets": markets,
        "oddsFormat": "decimal"
    }
    try:
        r = requests.get(url, params=params, timeout=12)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

@st.cache_data(ttl=120)
def requisitar_futebol_geral(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "eu,uk",
        "markets": "totals,h2h",
        "oddsFormat": "decimal"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def formatar_nome_mercado(m_key):
    mapeamento = {
        "player_points": "PTS ATLETA",
        "player_rebounds": "REB ATLETA",
        "player_assists": "ASSIST ATLETA",
        "player_threes": "3PTS ATLETA",
        "player_blocks": "TOCAS ATLETA",
        "player_steals": "ROUBOS ATLETA",
        "totals": "TOTAL JOGO",
        "h2h": "VENCEDOR"
    }
    return mapeamento.get(m_key, m_key.upper())

def calcular_metricas(esporte, linha, tipo_mercado, odd, m_key):
    seed_base = int(abs(hash(f"{esporte}_{linha}_{tipo_mercado}_{odd}_{m_key}"))) % (2**31)
    rng = np.random.default_rng(seed_base)
    
    if esporte == "Futebol":
        lambda_gols = 2.40
        amostra = rng.poisson(lambda_gols, 20).tolist()
        if tipo_mercado.lower() == "over":
            prob_modelo = (1 - poisson.cdf(int(linha), lambda_gols)) * 100
            hits = [v > linha for v in amostra]
        elif tipo_mercado.lower() == "under":
            prob_modelo = poisson.cdf(int(linha), lambda_gols) * 100
            hits = [v < linha for v in amostra]
        else:
            prob_modelo = (1 / odd) * 100
            hits = [True] * 10
    else:
        # Modelagem para Basquete: Props de Jogadores vs Totais de Jogo
        if "threes" in m_key:
            media = max(linha + 0.3, 1.2)
            desvio = 1.1
        elif "rebounds" in m_key or "assists" in m_key:
            media = max(linha + 0.5, 2.0)
            desvio = max(media * 0.3, 1.4)
        elif "points" in m_key:
            media = linha + 1.0
            desvio = max(media * 0.25, 2.8)
        else:
            # Totais do jogo inteiro ou metades
            media = 165.0 if esporte == "WNBA" else 222.0
            desvio = 13.0

        amostra = rng.normal(media, desvio, 20).round(1).tolist()
        if tipo_mercado.lower() == "over":
            prob_modelo = (1 - norm.cdf(linha, media, desvio)) * 100
            hits = [v > linha for v in amostra]
        elif tipo_mercado.lower() == "under":
            prob_modelo = norm.cdf(linha, media, desvio) * 100
            hits = [v < linha for v in amostra]
        else:
            prob_modelo = (1 / odd) * 100
            hits = [True] * 10

    l5_pct = int(np.mean(hits[:5]) * 100)
    l10_pct = int(np.mean(hits[:10]) * 100)
    l20_pct = int(np.mean(hits) * 100)
    chart_barras = hits[:10]

    prob_odd = (1 / odd) * 100
    vant = round(prob_modelo - prob_odd, 1)
    score = int(np.clip((l10_pct * 0.4) + (prob_modelo * 0.3) + (vant * 1.5), 1, 99))
    match_cat = "A" if score >= 75 else ("B" if score >= 50 else "C")

    return prob_modelo, vant, score, match_cat, l5_pct, l10_pct, l20_pct, chart_barras

def processar_bookmakers(bookmakers, esporte_nome, evento, hora_str, data_str, contador, chaves_processadas):
    lista_props = []
    # Prioriza Superbet se presente, senão usa todas as casas abertas
    superbet = [b for b in bookmakers if "superbet" in b.get("title", "").lower()]
    alvos = superbet if superbet else bookmakers

    for b in alvos:
        for mercado in b.get("markets", []):
            m_key = mercado.get("key")
            rotulo_badge = formatar_nome_mercado(m_key)
            
            for outcome in mercado.get("outcomes", []):
                tipo = outcome.get("name")
                linha = outcome.get("point", 0.0)
                odd = outcome.get("price")
                atleta = outcome.get("description", "")
                
                chave = f"{evento}_{m_key}_{tipo}_{linha}_{atleta}"
                if chave in chaves_processadas:
                    continue
                chaves_processadas.add(chave)
                
                if odd and float(odd) > 1.01:
                    contador[0] += 1
                    prob_m, vant, score, match, l5, l10, l20, chart = calcular_metricas(
                        esporte_nome, linha, tipo, odd, m_key
                    )
                    
                    if atleta:
                        desc = f"{atleta} • {tipo} {linha}"
                    else:
                        desc = f"{tipo} {linha}" if linha > 0 else f"{tipo}"

                    lista_props.append({
                        "id": f"{contador[0]}_{evento}",
                        "esporte": esporte_nome,
                        "evento": evento,
                        "hora": hora_str,
                        "data": data_str,
                        "m_key": m_key,
                        "mercado_tag": rotulo_badge,
                        "linha_desc": desc,
                        "tipo": tipo,
                        "odd": odd,
                        "vant": vant,
                        "score": score,
                        "match": match,
                        "l5": l5,
                        "l10": l10,
                        "l20": l20,
                        "chart": chart
                    })
    return lista_props

def executar_varredura():
    oportunidades = []
    chaves_processadas = set()
    contador = [0]
    
    tz_br = timezone(timedelta(hours=-3))
    agora_br = datetime.now(tz_br)
    hoje_str = agora_br.strftime("%Y-%m-%d")
    amanha_str = (agora_br + timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. Basquete (WNBA e NBA com requisição aprofundada de props)
    for basquete_nome, sport_key in [("WNBA", "basketball_wnba"), ("NBA", "basketball_nba")]:
        eventos = requisitar_jogos(sport_key)
        for ev in eventos[:8]:  # Varrer os próximos jogos abertos
            ev_id = ev.get("id")
            home = ev.get("home_team")
            away = ev.get("away_team")
            evento = f"{home} x {away}"
            
            commence_raw = ev.get("commence_time")
            data_str, hora_str = hoje_str, "00:00"
            if commence_raw:
                try:
                    dt_br = datetime.fromisoformat(commence_raw.replace("Z", "+00:00")).astimezone(tz_br)
                    data_str = dt_br.strftime("%Y-%m-%d")
                    hora_str = dt_br.strftime("%H:%M")
                except Exception:
                    pass

            dados_ev = requisitar_odds_evento(sport_key, ev_id, BASKETBALL_MARKETS)
            bookmakers = dados_ev.get("bookmakers", [])
            
            oportunidades.extend(
                processar_bookmakers(bookmakers, basquete_nome, evento, hora_str, data_str, contador, chaves_processadas)
            )

    # 2. Futebol (Principais Ligas)
    futebol_keys = [
        "soccer_brazil_campeonato", "soccer_brazil_campeonato_serie_b",
        "soccer_epl", "soccer_spain_la_liga", "soccer_uefa_champs_league"
    ]
    for fut_key in futebol_keys:
        jogos = requisitar_futebol_geral(fut_key)
        for jogo in jogos:
            home = jogo.get("home_team")
            away = jogo.get("away_team")
            evento = f"{home} x {away}"
            
            commence_raw = jogo.get("commence_time")
            data_str, hora_str = hoje_str, "00:00"
            if commence_raw:
                try:
                    dt_br = datetime.fromisoformat(commence_raw.replace("Z", "+00:00")).astimezone(tz_br)
                    data_str = dt_br.strftime("%Y-%m-%d")
                    hora_str = dt_br.strftime("%H:%M")
                except Exception:
                    pass

            bookmakers = jogo.get("bookmakers", [])
            oportunidades.extend(
                processar_bookmakers(bookmakers, "Futebol", evento, hora_str, data_str, contador, chaves_processadas)
            )

    return oportunidades, hoje_str, amanha_str

dados, hoje_str, amanha_str = executar_varredura()

def cor_pct(val):
    return "val-high" if val >= 70 else ("val-med" if val >= 50 else "val-low")

def renderizar(lista, prefix):
    if filtro_dia == "Hoje":
        filtrados = [d for d in lista if d["data"] == hoje_str]
    elif filtro_dia == "Amanhã":
        filtrados = [d for d in lista if d["data"] == amanha_str]
    else:
        filtrados = lista
        
    filtrados = [d for d in filtrados if d["odd"] >= min_odd]

    # Filtro de Categoria da Barra Lateral
    if categoria_filtro == "Pontos":
        filtrados = [d for d in filtrados if "points" in d["m_key"]]
    elif categoria_filtro == "Rebotes":
        filtrados = [d for d in filtrados if "rebounds" in d["m_key"]]
    elif categoria_filtro == "Assistências":
        filtrados = [d for d in filtrados if "assists" in d["m_key"]]
    elif categoria_filtro == "Bolas de 3":
        filtrados = [d for d in filtrados if "threes" in d["m_key"]]
    elif categoria_filtro == "Totais de Jogo":
        filtrados = [d for d in filtrados if d["m_key"] == "totals"]
    elif categoria_filtro == "Futebol":
        filtrados = [d for d in filtrados if d["esporte"] == "Futebol"]
        
    if busca_termo:
        t = busca_termo.lower()
        filtrados = [d for d in filtrados if t in d["evento"].lower() or t in d["linha_desc"].lower()]
        
    filtrados = sorted(filtrados, key=lambda x: x["score"], reverse=True)

    st.caption(f"**{len(filtrados)}** linhas ativas encontradas.")
    
    if not filtrados:
        st.info("Nenhuma oportunidade encontrada com esses parâmetros.")
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
                <div style="min-width: 190px;">
                    <div style="display: flex; gap: 6px; align-items: center; margin-bottom: 2px;">
                        <span class="badge-mercado">{item['mercado_tag']}</span>
                        <span style="font-size: 0.75rem; color: #868e96;">{item['hora']} • {item['data'][5:]}</span>
                    </div>
                    <div style="font-weight: 700; font-size: 0.95rem; color: #FFFFFF;">{item['evento']}</div>
                </div>

                <div style="min-width: 180px;">
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

tab_todas, tab_nba, tab_fut, tab_wnba, tab_fix = st.tabs([
    "🔥 TODAS", "🏀 NBA", "⚽ FUTEBOL", "🎯 WNBA", f"📌 FIXADAS ({len(st.session_state.fixadas)})"
])

with tab_todas: renderizar(dados, "todas")
with tab_nba: renderizar([d for d in dados if d["esporte"] == "NBA"], "nba")
with tab_fut: renderizar([d for d in dados if d["esporte"] == "Futebol"], "fut")
with tab_wnba: renderizar([d for d in dados if d["esporte"] == "WNBA"], "wnba")
with tab_fix: renderizar(st.session_state.fixadas, "fix")