import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yaml
import os
from fredapi import Fred
from datetime import datetime, timedelta

# --- 1. 基本設定 ---
st.set_page_config(layout="wide", page_title="KURURUGI Pro", page_icon="🛡️")

# スマホ最適化CSS: 余白の削減とタブの調整
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { height: 40px; font-size: 13px; padding: 0px 10px; }
    [data-testid="stVerticalBlock"] > div { padding: 0px; }
    </style>
    """, unsafe_allow_html=True)

# APIキー取得
FRED_API_KEY = st.secrets.get("FRED_API_KEY") or os.getenv("FRED_API_KEY")
fred = Fred(api_key=FRED_API_KEY)

# 設定読み込み
with open("config/indicators.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# --- 2. サイドバー操作 ---
st.sidebar.title("⚙️ Settings")
timeframe = st.sidebar.radio("時間足", ("日足 (Daily)", "週足 (Weekly)", "月足 (Monthly)"), index=2)
period_years = st.sidebar.slider("表示期間 (年)", 1, 5, 2)

freq_map = {"日足 (Daily)": "D", "週足 (Weekly)": "W", "月足 (Monthly)": "MS"}
target_freq = freq_map[timeframe]

# --- 3. データ取得 ---
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

# --- 4. 描画関数 (スマホ最適化) ---
def draw_adaptive_charts(labels):
    for label in labels:
        if label not in all_data: continue
        
        # データ整形
        series = all_data[label].resample(target_freq).last().ffill()
        shift = 12 if target_freq=="MS" else 52 if target_freq=="W" else 365
        
        if "Curve" in label:
            yoy = series - series.shift(shift)
            yoy_label = "YoY Diff"
        else:
            yoy = (series / series.shift(shift) - 1) * 100
            yoy_label = "YoY (%)"
            
        display_start = datetime.now() - timedelta(days=period_years*365)
        s, y = series[series.index >= display_start], yoy[yoy.index >= display_start]

        # コンテナで一つの指標をグルーピング
        with st.container():
            st.markdown(f"### {label}")
            c1, c2 = st.columns(2)
            
            with c1:
                fig_l = go.Figure()
                fig_l.add_trace(go.Scattergl(x=s.index, y=s, line=dict(color='#00ffcc', width=2)))
                fig_l.update_layout(
                    title=dict(text="Level", font=dict(size=12)),
                    height=250, # 高さを抑えてスマホでの一覧性を向上
                    template="plotly_dark",
                    margin=dict(l=10, r=10, t=30, b=10),
                    xaxis=dict(tickfont=dict(size=10)),
                    yaxis=dict(tickfont=dict(size=10))
                )
                if "Curve" in label: fig_l.add_hline(y=0, line_dash="dash")
                st.plotly_chart(fig_l, use_container_width=True, config={'displayModeBar': False})
                
            with c2:
                fig_y = go.Figure()
                fig_y.add_trace(go.Bar(x=y.index, y=y, marker_color='#ff66cc', opacity=0.8))
                fig_y.update_layout(
                    title=dict(text=yoy_label, font=dict(size=12)),
                    height=250,
                    template="plotly_dark",
                    margin=dict(l=10, r=10, t=30, b=10),
                    xaxis=dict(tickfont=dict(size=10)),
                    yaxis=dict(tickfont=dict(size=10))
                )
                st.plotly_chart(fig_y, use_container_width=True, config={'displayModeBar': False})
            st.markdown("---") # 指標ごとの区切り線

# --- 5. メイン表示 ---
st.title("🛡️ KURURUGI Pro")

t1, t2, t3 = st.tabs(["🔥 物価・消費", "👥 雇用・生産", "💹 市場・金利"])

with t1:
    draw_adaptive_charts(["消費者物価指数 (CPI)", "PCE デフレーター", "小売売上高", "ミシガン大学消費者態度指数"])
with t2:
    draw_adaptive_charts(["非農業部門雇用者数 (NFP)", "失業率", "鉱工業生産指数 (INDPRO)", "新規失業保険申請件数 (Claims)"])
with t3:
    draw_adaptive_charts(["米10年-2年金利差 (Yield Curve)", "実効ドル相場 (Broad USD Index)", "WTI原油価格 (Oil)", "S&P 500 指数"])
