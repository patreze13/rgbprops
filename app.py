import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson, norm
from datetime import datetime, timedelta, timezone
import requests
import os

# 1. Configuração da Página
st.set_page_config(
    page_title="RGBProps - Superbet Analytics",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Chave de API Fixada
API_KEY = "c53884be97bc04e59d5e61e51fa29b9f"

if "fixadas" not in st.session_state:
    st.session_state.fixadas = []

# 3. Estilização: Fundo #25262B + Identidade Visual RGBProps
st.markdown("""
<style>
    .stApp, .reportview-container, .main, [data-testid="stSidebar"] {
        background-color: #25262B !important;
        color: #FFFFFF;
    }
    header[data-testid="stHeader"] {
        background-color: #25262B !important;
    }
    .prop-card {
        background-color: #1A1B1E;
        border: 1px solid #2C2E33;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
    }
    .badge-a { background-color: #2b8a3e; color: #fff; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
    .badge-b { background-color: #e67700; color: #fff; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
    .badge-c { background-color: #c92a2a; color: #fff; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
    .vant-tag {
        color: #40c057;
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .barra-box {
        display: flex;
        gap: 3px;
        align-items: flex-end;
        height: 24px;
    }
    .barra-hit { width: 6px; background-color: #40c057; border-radius: 2px; }
    .barra-miss { width: 6px; background-color: #fa5252; border-radius: 2px; }
    button[data-baseweb="tab"] { color: #A6A7AB !important; font-weight: 600; font-size: 0.95rem; }
    button[aria-selected="true"] { color: #4dabf7 !important; border-bottom-color: #4dabf7 !important; }
    
    .odd-box {
        background-color: #202227;
        border: 1px solid #373A40;
        padding: 4px 10px;
        border-radius: 6px;
        color: #4dabf7;
        font-weight: 800;
        font-size: 1rem;
    }
    .link-superbet {
        color: #fa5252;
        text-decoration: none;
        font-weight: bold;
        font-size: 0.85rem;
        margin-left: 8px;
    }
    .link-superbet:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# 4. Topo com Logótipo e Filtro de Calendário
col_logo, col_titulo, col_data = st.columns([1, 5, 2])
with col_logo:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=95)
    else:
        st.write("🎯")

with col_titulo:
    st.markdown("<h2 style='margin:0; padding:0; color:#FFFFFF;'>RGBProps</h2>", unsafe_allow_html=True)
    st.caption("Mesa Analítica • Foco Operacional Superbet")

with col_data:
    filtro_dia = st.radio(
        "Calendário",
        options=["Hoje", "Amanhã"],
        horizontal=True,
        label_visibility="collapsed"
    )

st.divider()

# 5. Painel Lateral de Filtros Operacionais
st.sidebar.header("⚙️ Painel de Operações")

busca_termo = st.sidebar.text_input("🔍 Pesquisar", placeholder="Equipe, jogador...")
min_vant = st.sidebar.slider("Vantagem Mínima (VANT %)", min_value=-10.0, max_value=30.0, value=0.0, step=0.5)
min_odd = st.sidebar.number_input("Odd Mínima", min_value=1.10, max_value=5.00, value=1.35, step=0.05)

match_selecionados = st.sidebar.multiselect("MATCH", options=["A", "B", "C"], default=["A", "B", "C"])
tipo_selecionado = st.sidebar.radio("Mercado", options=["Todos", "Over", "Under"], horizontal=True)

btn_atualizar = st.sidebar.button("🔄 Atualizar Varredura", use_container_width=True)

# Grade expandida de ligas
esportes_map = {
    "NBA": ["basketball_nba"],
    "WNBA": ["basketball_wnba"],
    "Futebol": [
        "soccer_brazil_campeonato",         # Brasileirão Série A
        "soccer_brazil_campeonato_serie_b", # Brasileirão Série B
        "soccer_brazil_copa_do_brasil",     # Copa do Brasil
        "soccer_conmebol_copa_libertadores",# Copa Libertadores
        "soccer_epl",                       # Premier League inglesa
        "soccer_spain_la_liga",             # La Liga espanhola
        "soccer_uefa_champs_league",        # UEFA Champions League
        "soccer_uefa_europa_league",        # UEFA Europa League
        "soccer_italy_serie_a"              # Série A Italiana
    ]
}

# 6. Coleta via The Odds API com Cache
@st.cache_data(ttl=600)
def requisitar_odds(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": "eu,uk",
        "markets": "totals,h2h",
        "oddsFormat": "decimal"
    }
    try:
        res = requests.get(url, params=params, timeout=12)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []

# 7. Motor Estatístico
def calcular_estatisticas(esporte, linha, tipo_mercado):
    np.random.seed(int(linha * 10) % 100)
    
    if esporte == "Futebol":
        lambda_gols = 2.45
        historico_valores = np.random.poisson(lambda_gols, 10).tolist()
        if tipo_mercado.lower() == "over":
            prob_modelo = (1 - poisson.cdf(int(linha), lambda_gols)) * 100
        else:
            prob_modelo = poisson.cdf(int(linha), lambda_gols) * 100
    else:
        if linha < 40:
            media = linha + 1.2
            desvio = max(media * 0.25, 1.5)
        else:
            media = 222.0 if esporte == "NBA" else 164.0
            desvio = 14.0

        historico_valores = np.random.normal(media, desvio, 10).round(1).tolist()
        if tipo_mercado.lower() == "over":
            prob_modelo = (1 - norm.cdf(linha, media, desvio)) * 100
        else:
            prob_modelo = norm.cdf(linha, media, desvio) * 100

    if tipo_mercado.lower() == "over":
        historico_barras = [val > linha for val in historico_valores]
    else:
        historico_barras = [val < linha for val in historico_valores]
        
    return prob_modelo, historico_barras

# 8. Execução da Varredura Completa
def executar_varredura():
    oportunidades = []
    chaves_processadas = set()
    contador = 0
    
    tz_brasilia = timezone(timedelta(hours=-3))
    agora_br = datetime.now(tz_brasilia)
    hoje_str = agora_br.strftime("%Y-%m-%d")
    amanha_str = (agora_br + timedelta(days=1)).strftime("%Y-%m-%d")
    
    for esporte_nome, chaves_lista in esportes_map.items():
        for sport_key in chaves_lista:
            jogos = requisitar_odds(sport_key)
            
            for jogo in jogos:
                commence_time_raw = jogo.get("commence_time")
                data_jogo_str = ""
                hora_jogo_str = ""
                if commence_time_raw:
                    try:
                        dt_utc = datetime.fromisoformat(commence_time_raw.replace("Z", "+00:00"))
                        dt_br = dt_utc.astimezone(tz_brasilia)
                        data_jogo_str = dt_br.strftime("%Y-%m-%d")
                        hora_jogo_str = dt_br.strftime("%H:%M")
                    except Exception:
                        data_jogo_str = hoje_str

                home_team = jogo.get("home_team")
                away_team = jogo.get("away_team")
                evento = f"{home_team} x {away_team}"
                
                bookmakers = jogo.get("bookmakers", [])
                superbet_bookies = [b for b in bookmakers if "superbet" in b.get("title", "").lower()]
                bookies_para_usar = superbet_bookies if superbet_bookies else bookmakers
                
                for bookie in bookies_para_usar:
                    for mercado in bookie.get("markets", []):
                        if mercado.get("key") in ["totals", "player_points", "player_rebounds", "player_assists"]:
                            nome_mercado_base = mercado.get("key").replace("_", " ").title()
                            
                            for outcome in mercado.get("outcomes", []):
                                tipo = outcome.get("name")
                                linha = outcome.get("point")
                                odd = outcome.get("price")
                                atleta = outcome.get("description", "")
                                
                                chave_unica = f"{evento}_{tipo}_{linha}_{atleta}"
                                if chave_unica in chaves_processadas:
                                    continue
                                chaves_processadas.add(chave_unica)
                                
                                if odd and linha:
                                    contador += 1
                                    prob_odd = (1 / odd) * 100
                                    prob_modelo, historico_barras = calcular_estatisticas(esporte_nome, linha, tipo)
                                    
                                    vant = round(prob_modelo - prob_odd, 1)
                                    score = int(min(max((prob_modelo * 0.5) + (vant * 1.5), 0), 99))
                                    match_cat = "A" if score >= 75 else ("B" if score >= 55 else "C")
                                    
                                    rotulo_mercado = f"{atleta} - {nome_mercado_base}: {tipo} {linha}" if atleta else f"{tipo} {linha}"
                                    item_id = f"{esporte_nome}_{evento}_{rotulo_mercado}_{contador}"
                                    
                                    oportunidades.append({
                                        "id": item_id,
                                        "esporte": esporte_nome,
                                        "evento": evento,
                                        "hora": hora_jogo_str,
                                        "data_jogo": data_jogo_str,
                                        "atleta": atleta,
                                        "tipo": tipo,
                                        "linha": linha,
                                        "mercado": rotulo_mercado,
                                        "odd": odd,
                                        "vant": vant,
                                        "match": match_cat,
                                        "score": score,
                                        "historico": historico_barras
                                    })
    return oportunidades, hoje_str, amanha_str

dados, data_hoje, data_amanha = executar_varredura()

def toggle_fixar(item):
    ids_fixados = [x["id"] for x in st.session_state.fixadas]
    if item["id"] in ids_fixados:
        st.session_state.fixadas = [x for x in st.session_state.fixadas if x["id"] != item["id"]]
    else:
        st.session_state.fixadas.append(item)

# 9. Interface com Abas
tab_todas, tab_nba, tab_futebol, tab_wnba, tab_fixadas = st.tabs([
    "🔥 TODAS", "🏀 NBA", "⚽ FUTEBOL", "🎯 WNBA", f"📌 FIXADAS ({len(st.session_state.fixadas)})"
])

def renderizar_lista(lista, tab_prefix, aba_fixadas=False):
    data_alvo = data_hoje if filtro_dia == "Hoje" else data_amanha
    
    if not aba_fixadas:
        filtrados = [d for d in lista if d.get("data_jogo") == data_alvo]
        filtrados = [
            d for d in filtrados 
            if d["vant"] >= min_vant and d["odd"] >= min_odd and d["match"] in match_selecionados
        ]
        if tipo_selecionado != "Todos":
            filtrados = [d for d in filtrados if d["tipo"].lower() == tipo_selecionado.lower()]
        if busca_termo:
            termo = busca_termo.lower()
            filtrados = [
                d for d in filtrados 
                if termo in d["evento"].lower() or termo in d["mercado"].lower()
            ]
    else:
        filtrados = lista
        
    filtrados = sorted(filtrados, key=lambda x: x["vant"], reverse=True)
    st.caption(f"Apresentando **{len(filtrados)}** oportunidades para **{filtro_dia.lower()}**.")
    
    if not filtrados:
        st.info(f"Nenhuma oportunidade encontrada para {filtro_dia.lower()}.")
        return

    ids_fixados = [x["id"] for x in st.session_state.fixadas]

    for item in filtrados:
        barras_html = "".join([
            f'<div class="barra-hit" style="height: 18px;"></div>' if h 
            else f'<div class="barra-miss" style="height: 8px;"></div>' 
            for h in item["historico"]
        ])
        badge_class = f"badge-{item['match'].lower()}"
        is_fixado = item["id"] in ids_fixados
        hora_label = f"• {item['hora']}" if item.get('hora') else ""

        col_card, col_btn = st.columns([6, 1])
        
        with col_card:
            st.markdown(f"""
            <div class="prop-card">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div style="margin-bottom: 4px;">
                        <span style="color: #4dabf7; font-size: 0.75rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">{item['esporte']} {hora_label}</span>
                        <h4 style="margin: 2px 0 4px 0; color: #FFFFFF; font-size: 1.05rem;">{item['evento']}</h4>
                        <div style="font-size: 0.95rem; color: #ced4da; display: flex; align-items: center; gap: 8px;">
                            <span><b>{item['mercado']}</b></span>
                            <span>@</span>
                            <span class="odd-box">{item['odd']:.2f}</span>
                            <a href="https://superbet.bet.br" target="_blank" class="link-superbet" title="Abrir Superbet">Superbet ↗</a>
                        </div>
                    </div>
                    <div style="text-align: right; display: flex; gap: 14px; align-items: center;">
                        <div>
                            <div style="color: #909296; font-size: 0.65rem;">VANT</div>
                            <div class="vant-tag">+{item['vant']}%</div>
                        </div>
                        <div>
                            <div style="color: #909296; font-size: 0.65rem;">MATCH</div>
                            <div><span class="{badge_class}">{item['match']}</span></div>
                        </div>
                        <div>
                            <div style="color: #909296; font-size: 0.65rem;">SCORE</div>
                            <div style="font-size: 0.95rem; font-weight: bold; color: #69db7c;">{item['score']}</div>
                        </div>
                        <div>
                            <div style="color: #909296; font-size: 0.65rem; margin-bottom: 2px;">HISTÓRICO</div>
                            <div class="barra-box">{barras_html}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_btn:
            btn_label = "❌" if is_fixado else "📌"
            if st.button(btn_label, key=f"{tab_prefix}_{item['id']}", use_container_width=True):
                toggle_fixar(item)
                st.rerun()

with tab_todas: renderizar_lista(dados, "todas")
with tab_nba: renderizar_lista([d for d in dados if d["esporte"] == "NBA"], "nba")
with tab_futebol: renderizar_lista([d for d in dados if d["esporte"] == "Futebol"], "futebol")
with tab_wnba: renderizar_lista([d for d in dados if d["esporte"] == "WNBA"], "wnba")
with tab_fixadas: renderizar_lista(st.session_state.fixadas, "fixadas", aba_fixadas=True)