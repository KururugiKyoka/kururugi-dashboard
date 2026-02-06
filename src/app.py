import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yaml
import os
from fredapi import Fred
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="KURURUGI Pro", page_icon="🛡️")

st.markdown("""<style>.stTabs [data-baseweb="tab-list"] { gap: 8px; } .stTabs [data-baseweb="tab"] { height: 45px; font-size: 14px; }</style>""", unsafe_allow_html=True)

FRED_API_KEY = st.secrets.get("FRED_API_KEY") or os.getenv("FRED_API_KEY")
fred = Fred(api_key=FRED_API_KEY)

if os.path.exists("config/indicators.yml"):
    with open("config/indicators.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
else:
    st.error("config/indicators.yml が見つかりません")
    st.stop()

st.sidebar.title("⚙️ Settings")
timeframe = st.sidebar.radio("時間足", ("日足 (Daily)", "週足 (Weekly)", "月足 (Monthly)"), index=2)
period_years = st.sidebar.slider("表示期間 (年)", 1, 5, 2)

freq_map = {"日足 (Daily)": "D", "週足 (Weekly)": "W", "月足 (Monthly)": "MS"}
target_freq = freq_map[timeframe]

@st.cache_data(ttl=3600)
def load_all_data(indicators):
    data_dict = {}
    start_date = datetime.now() - timedelta(days=365*6)
    for item in indicators:
        try:
            data_dict[item['label']] = fred.get_series(item['id'], observation_start=start_date)
        except: continue
    return data_dict

all_data = load_all_data(config['indicators'])

def draw_charts(labels):
    for label in labels:
        if label not in all_data: continue
        series = all_data[label].resample(target_freq).last().ffill()
        shift = 12 if target_freq=="MS" else 52 if target_freq=="W" else 365
        
        if "Curve" in label:
            yoy = series - series.shift(shift)
            yoy_name = "YoY Diff"
        else:
            yoy = (series / series.shift(shift) - 1) * 100
            yoy_name = "YoY (%)"
            
        display_start = datetime.now() - timedelta(days=period_years*365)
        s, y = series[series.index >= display_start], yoy[yoy.index >= display_start]

        fig = make_subplots(rows=1, cols=2, subplot_titles=(f"{label}", f"{yoy_name}"))
        fig.add_trace(go.Scattergl(x=s.index, y=s, name="Level", line=dict(color='#00ffcc', width=2)), row=1, col=1)
        fig.add_trace(go.Bar(x=y.index, y=y, name="YoY", marker_color='#ff66cc', opacity=0.8), row=1, col=2)
        
        if "Curve" in label:
            fig.add_hline(y=0, line_dash="dash", row=1, col=1)
            fig.add_hrect(y0=-1, y1=0, fillcolor="red", opacity=0.15, row=1, col=1)

        fig.update_layout(height=350, showlegend=False, template="plotly_dark", margin=dict(l=10, r=10, t=40, b=10))
        # 2026年最新仕様に統一
        st.plotly_chart(fig, width="stretch")

st.title("🛡️ KURURUGI Macro Dashboard")

tab1, tab2, tab3 = st.tabs(["🔥 物価・消費", "👥 雇用・生産", "💹 市場・金利"])

with tab1:
    draw_charts(["消費者物価指数 (CPI)", "PCE デフレーター", "小売売上高", "ミシガン大学消費者態度指数"])
with tab2:
    draw_charts(["非農業部門雇用者数 (NFP)", "失業率", "鉱工業生産指数 (INDPRO)", "新規失業保険申請件数 (Claims)"])
with tab3:
    draw_charts(["米10年-2年金利差 (Yield Curve)", "実効ドル相場 (Broad USD Index)", "WTI原油価格 (Oil)", "S&P 500 指数"])
