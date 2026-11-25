import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date

st.set_page_config(
    page_title="SWING AI TRADER",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px;}
[data-testid="stMetric"] {background: #111827; border: 1px solid #263244; padding: 12px; border-radius: 12px;}
.small-note {color:#9CA3AF; font-size:0.85rem;}
.stTabs [data-baseweb="tab-list"] {gap: 8px;}
.stTabs [data-baseweb="tab"] {padding: 8px 14px;}
</style>
""", unsafe_allow_html=True)

# All values in this first prototype are generated demo data.
TICKERS = ["PETR4", "VALE3", "ITUB4", "BBAS3", "BBDC4", "ABEV3"]
SEED = 17

@st.cache_data
def make_demo_data(ticker: str, days: int = 260):
    rng = np.random.default_rng(SEED + sum(ord(c) for c in ticker))
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    drift = 0.00025
    shocks = rng.normal(drift, 0.014, days)
    start = {"PETR4": 36, "VALE3": 62, "ITUB4": 34, "BBAS3": 27, "BBDC4": 15, "ABEV3": 13}[ticker]
    close = start * np.exp(np.cumsum(shocks))
    open_ = np.r_[close[0], close[:-1]] * (1 + rng.normal(0, 0.004, days))
    high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.012, days))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.012, days))
    volume = rng.integers(1_000_000, 12_000_000, days)
    df = pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=dates)
    df["MM20"] = df["Close"].rolling(20).mean()
    df["MM50"] = df["Close"].rolling(50).mean()
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI14"] = 100 - (100 / (1 + rs))
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df

def brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.title("📈 SWING AI TRADER")
st.caption("Painel educativo de análise e simulação • versão 1.0")

st.warning(
    "MODO DEMONSTRAÇÃO: os preços e gráficos desta versão são fictícios e gerados pelo programa. "
    "Não são cotações reais, recomendações de investimento nem sinais para operar. "
    "Não há conexão com corretoras ou execução de ordens.",
    icon="⚠️"
)

with st.sidebar:
    st.header("Configurações")
    ticker = st.selectbox("Ativo demonstrativo", TICKERS, index=0)
    periodo = st.selectbox("Janela do gráfico", ["3 meses", "6 meses", "1 ano"], index=2)
    st.divider()
    st.caption("Projeto educacional. Não informe senhas, CPF ou dados bancários aqui.")

df = make_demo_data(ticker)
window = {"3 meses": 65, "6 meses": 130, "1 ano": 260}[periodo]
view = df.tail(window).copy()
last = df.iloc[-1]
prev = df.iloc[-2]
variation = (last["Close"] / prev["Close"] - 1) * 100

# Educational classification, not a trade signal.
if pd.notna(last["MM20"]) and pd.notna(last["MM50"]):
    if last["Close"] > last["MM20"] > last["MM50"]:
        condition = "Tendência demonstrativa positiva"
    elif last["Close"] < last["MM20"] < last["MM50"]:
        condition = "Tendência demonstrativa negativa"
    else:
        condition = "Cenário misto / sem confirmação"
else:
    condition = "Dados insuficientes"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ativo em estudo", ticker, "Dado fictício")
c2.metric("Último preço demonstrativo", brl(float(last["Close"])), f"{variation:+.2f}%")
c3.metric("RSI (14)", f"{last['RSI14']:.1f}" if pd.notna(last["RSI14"]) else "—")
c4.metric("Condição técnica", condition, help="Classificação didática baseada em médias móveis; não é recomendação.")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Mercado", "🧠 Análise", "🧪 Simulador", "📘 Como usar"])

with tab1:
    st.subheader(f"{ticker} • histórico fictício")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=view.index, open=view["Open"], high=view["High"],
        low=view["Low"], close=view["Close"], name="Preço demonstrativo"
    ))
    fig.add_trace(go.Scatter(x=view.index, y=view["MM20"], name="Média móvel 20", line=dict(width=1.5)))
    fig.add_trace(go.Scatter(x=view.index, y=view["MM50"], name="Média móvel 50", line=dict(width=1.5)))
    fig.update_layout(
        height=430, template="plotly_dark", xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=25, b=10), legend=dict(orientation="h", y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)
    vol_fig = go.Figure(go.Bar(x=view.index, y=view["Volume"], name="Volume fictício"))
    vol_fig.update_layout(height=190, template="plotly_dark", margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(vol_fig, use_container_width=True)
    st.caption("Série sintética criada apenas para demonstrar a interface. Não representa o histórico real do ativo.")

with tab2:
    st.subheader("Leitura técnica demonstrativa")
    a, b = st.columns(2)
    with a:
        st.metric("Média móvel de 20 períodos", brl(float(last["MM20"])))
        st.metric("Média móvel de 50 períodos", brl(float(last["MM50"])))
        st.metric("MACD", f"{last['MACD']:.3f}")
    with b:
        st.metric("Sinal MACD", f"{last['MACD_signal']:.3f}")
        st.metric("RSI (14)", f"{last['RSI14']:.1f}")
        st.metric("Volume fictício", f"{int(last['Volume']):,}".replace(",", "."))
    st.info(
        f"Resumo didático: {condition}. Indicadores isolados não preveem o futuro. "
        "Uma análise adequada também considera contexto, liquidez, custos, notícias e risco."
    )
    st.markdown("**Como interpretar com cautela**")
    st.write("- RSI é um indicador de força relativa; leituras extremas não garantem reversão.")
    st.write("- Médias móveis ajudam a visualizar tendências, mas podem atrasar em mudanças rápidas.")
    st.write("- MACD compara médias móveis e pode gerar sinais falsos em mercados laterais.")

with tab3:
    st.subheader("Simulador educativo de posição")
    st.caption("Use valores hipotéticos. Nada será enviado a uma corretora.")
    x1, x2, x3 = st.columns(3)
    with x1:
        saldo = st.number_input("Capital fictício (R$)", min_value=100.0, max_value=1_000_000.0, value=10000.0, step=500.0)
    with x2:
        risco_pct = st.slider("Risco hipotético por cenário (%)", 0.25, 2.0, 1.0, 0.25)
    with x3:
        distancia_pct = st.slider("Distância hipotética até o stop (%)", 1.0, 15.0, 5.0, 0.5)
    perda_max = saldo * risco_pct / 100
    exposicao = perda_max / (distancia_pct / 100)
    st.divider()
    r1, r2, r3 = st.columns(3)
    r1.metric("Perda planejada no cenário", brl(perda_max))
    r2.metric("Exposição teórica correspondente", brl(exposicao))
    r3.metric("Percentual do capital exposto", f"{(exposicao/saldo)*100:.1f}%")
    st.caption(
        "Cálculo ilustrativo simplificado: exposição = perda planejada ÷ distância percentual do stop. "
        "Não inclui gaps, slippage, taxas, impostos ou mudanças de preço; não é indicação de tamanho de posição."
    )
    st.markdown("**Diário de simulação**")
    if "journal" not in st.session_state:
        st.session_state.journal = []
    with st.form("trade_form"):
        lado = st.selectbox("Cenário", ["Hipótese de alta", "Hipótese de baixa", "Sem operação"])
        observacao = st.text_input("Observação (opcional)", placeholder="Ex.: tendência ainda sem confirmação")
        submitted = st.form_submit_button("Registrar cenário fictício")
    if submitted:
        st.session_state.journal.append({
            "Data": date.today().strftime("%d/%m/%Y"),
            "Ativo": ticker,
            "Cenário": lado,
            "Observação": observacao or "—"
        })
    if st.session_state.journal:
        st.dataframe(pd.DataFrame(st.session_state.journal), use_container_width=True, hide_index=True)
        if st.button("Limpar diário desta sessão"):
            st.session_state.journal = []
            st.rerun()
    else:
        st.caption("Nenhum cenário registrado nesta sessão.")

with tab4:
    st.subheader("Primeiros passos")
    st.markdown("""
    1. Escolha um ativo demonstrativo no menu lateral.
    2. Observe o gráfico e as médias móveis.
    3. Leia os indicadores sem tratá-los como previsões.
    4. Teste valores hipotéticos no simulador.
    5. Registre cenários e avalie as limitações.

    **Próximas melhorias possíveis**
    - Integração com uma fonte licenciada/confiável de dados de mercado, em modo somente leitura.
    - Backtesting com separação entre dados de treino e teste.
    - Inclusão de custos, liquidez e eventos corporativos.
    - Relatórios de drawdown, volatilidade e retorno ajustado ao risco.
    """)
    st.info("A primeira versão não usa aprendizado de máquina para prever preços. A prioridade é validar dados, cálculos e interface antes de acrescentar modelos de IA.")

st.divider()
st.caption("SWING AI TRADER • Protótipo educacional v1.0 • Sem conexão com corretoras • Sem aconselhamento financeiro")
