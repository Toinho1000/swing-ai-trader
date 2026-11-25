import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import date

st.set_page_config(page_title="SWING AI TRADER", page_icon="📈", layout="wide")
st.title("📈 SWING AI TRADER")
st.caption("Versão 2.0 • consulta de dados e simulação educativa")
st.warning("MODO EDUCATIVO: dados consultados via brapi podem ter atraso e limitações. Não são recomendações. Este app não se conecta a corretoras nem executa ordens.")

API = "https://brapi.dev/api/v2"
TICKERS = ["PETR4", "VALE3", "MGLU3", "ITUB4"]

def token():
    try:
        return st.secrets.get("BRAPI_TOKEN", "")
    except Exception:
        return ""

def get(path, params):
    headers = {}
    t = token()
    if t:
        headers["Authorization"] = f"Bearer {t}"
    r = requests.get(f"{API}/{path}", params=params, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=900)
def quote(ticker):
    data = get("stocks/quote", {"symbols": ticker}).get("results", [])
    if not data:
        raise ValueError("Cotação indisponível para este ativo.")
    return data[0].get("data", {})

@st.cache_data(ttl=3600)
def history(ticker):
    data = get("stocks/historical", {
        "symbols": ticker, "range": "3mo", "interval": "1d", "sortOrder": "asc"
    }).get("results", [])
    if not data:
        raise ValueError("Histórico indisponível para este ativo.")
    rows = data[0].get("data", {}).get("historicalDataPrice", [])
    if not rows:
        raise ValueError("A API retornou histórico vazio.")
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["date"], unit="s", errors="coerce")
    df = df.rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"})
    for c in ["Open","High","Low","Close","Volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Date","Open","High","Low","Close"]).sort_values("Date").set_index("Date")
    df["MM20"] = df.Close.rolling(20).mean()
    df["MM50"] = df.Close.rolling(50).mean()
    d = df.Close.diff()
    gain, loss = d.clip(lower=0).rolling(14).mean(), -d.clip(upper=0).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI14"] = 100 - 100/(1+rs)
    e12, e26 = df.Close.ewm(span=12, adjust=False).mean(), df.Close.ewm(span=26, adjust=False).mean()
    df["MACD"] = e12-e26
    df["MACD_signal"] = df.MACD.ewm(span=9, adjust=False).mean()
    return df

def brl(v):
    if v is None or pd.isna(v): return "—"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

with st.sidebar:
    st.header("Ativo em estudo")
    ticker = st.selectbox("Ação da B3", TICKERS)
    st.caption("A documentação da brapi informa acesso de teste sem token para estes quatro ativos.")
    if st.button("Atualizar dados"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Não insira senhas de corretora, CPF ou dados bancários.")

try:
    with st.spinner("Consultando provedor de dados..."):
        q = quote(ticker)
        df = history(ticker)
    ok = True
except requests.exceptions.HTTPError as e:
    ok = False
    st.error(f"Falha HTTP ao consultar a API ({e.response.status_code if e.response is not None else 'sem código'}). Confira limites e disponibilidade.")
except requests.exceptions.RequestException:
    ok = False
    st.error("Não foi possível conectar ao provedor. Verifique a internet e tente novamente.")
except (ValueError, KeyError, TypeError):
    ok = False
    st.error("A fonte não retornou dados válidos para esta consulta.")

if ok:
    last = df.iloc[-1]
    price = q.get("regularMarketPrice", last.Close)
    change = q.get("regularMarketChangePercent")
    if change is None and len(df)>1:
        change = (last.Close/df.iloc[-2].Close-1)*100
    if pd.notna(last.MM20) and pd.notna(last.MM50):
        trend = "Positiva (critério didático)" if last.Close>last.MM20>last.MM50 else ("Negativa (critério didático)" if last.Close<last.MM20<last.MM50 else "Mista / sem confirmação")
    else:
        trend = "Histórico insuficiente"

    a,b,c,d = st.columns(4)
    a.metric("Ativo", ticker, "B3")
    b.metric("Último preço informado", brl(price), f"{float(change):+.2f}%" if change is not None else None)
    c.metric("RSI (14)", f"{last.RSI14:.1f}" if pd.notna(last.RSI14) else "—")
    d.metric("Leitura técnica", trend)
    st.caption(f"Horário informado pelo provedor: {q.get('regularMarketTime','não informado')}. Histórico: {df.index.min().date()} a {df.index.max().date()}.")

    t1,t2,t3,t4 = st.tabs(["📊 Mercado","🧠 Análise","🧪 Simulador","📘 Como usar"])
    with t1:
        fig=go.Figure()
        fig.add_trace(go.Candlestick(x=df.index,open=df.Open,high=df.High,low=df.Low,close=df.Close,name="Preço"))
        fig.add_trace(go.Scatter(x=df.index,y=df.MM20,name="Média móvel 20"))
        fig.add_trace(go.Scatter(x=df.index,y=df.MM50,name="Média móvel 50"))
        fig.update_layout(height=420,template="plotly_dark",xaxis_rangeslider_visible=False,margin=dict(l=8,r=8,t=25,b=8))
        st.plotly_chart(fig,use_container_width=True)
        vf=go.Figure(go.Bar(x=df.index,y=df.Volume,name="Volume"))
        vf.update_layout(height=180,template="plotly_dark",margin=dict(l=8,r=8,t=20,b=8))
        st.plotly_chart(vf,use_container_width=True)
        st.caption("Dados fornecidos pela brapi; podem ter atraso, limites ou indisponibilidade.")

    with t2:
        x,y=st.columns(2)
        x.metric("Média móvel 20",brl(last.MM20))
        x.metric("Média móvel 50",brl(last.MM50))
        y.metric("MACD",f"{last.MACD:.3f}" if pd.notna(last.MACD) else "—")
        y.metric("Sinal MACD",f"{last.MACD_signal:.3f}" if pd.notna(last.MACD_signal) else "—")
        st.info(f"Leitura: {trend}. Isso é uma classificação técnica simples, não sinal de compra ou venda.")
        st.write("RSI, médias móveis e MACD podem gerar leituras falsas. Considere contexto, liquidez, custos e incerteza.")

    with t3:
        st.subheader("Simulador educativo — valores hipotéticos")
        x,y,z=st.columns(3)
        capital=x.number_input("Capital fictício (R$)",100.0,1000000.0,10000.0,500.0)
        risk=y.slider("Risco hipotético (%)",0.25,2.0,1.0,0.25)
        stop=z.slider("Distância hipotética do stop (%)",1.0,15.0,5.0,0.5)
        loss=capital*risk/100
        exposure=loss/(stop/100)
        x,y,z=st.columns(3)
        x.metric("Perda planejada",brl(loss))
        y.metric("Exposição teórica",brl(exposure))
        z.metric("Capital exposto",f"{exposure/capital*100:.1f}%")
        st.caption("Cálculo simplificado; não inclui gaps, taxas, impostos ou slippage. Não é recomendação de tamanho de posição.")
        if "journal" not in st.session_state: st.session_state.journal=[]
        with st.form("journal"):
            scenario=st.selectbox("Cenário observado",["Hipótese de alta","Hipótese de baixa","Sem operação"])
            note=st.text_input("Observação (opcional)")
            submit=st.form_submit_button("Registrar cenário fictício")
        if submit:
            st.session_state.journal.append({"Data":date.today().strftime("%d/%m/%Y"),"Ativo":ticker,"Cenário":scenario,"Observação":note or "—"})
        if st.session_state.journal:
            st.dataframe(pd.DataFrame(st.session_state.journal),use_container_width=True,hide_index=True)

    with t4:
        st.markdown("""
        1. Selecione um ativo no menu lateral.
        2. Confira a data e o horário dos dados.
        3. Estude o gráfico e os indicadores sem tratá-los como previsões.
        4. Registre hipóteses no simulador.

        **Limitações:** a API tem limites e pode fornecer dados atrasados. Esta versão não usa IA preditiva, não executa ordens e não se conecta a corretoras.
        """)

else:
    st.info("Nenhum preço fictício será mostrado como se fosse real. Quando a fonte falhar, os dados ficam ocultos.")

st.divider()
st.caption("SWING AI TRADER • V2.0 • Consulta de dados + simulação educativa • Sem conexão com corretoras")
