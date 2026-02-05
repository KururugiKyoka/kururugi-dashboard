import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. ページ全体の基本設定（ワイドモード・タイトル）
st.set_page_config(page_title="Macro Canary Dashboard", layout="wide")

# 2. モダン・ミニマルな質感を出すためのカスタムCSS
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    [data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 700; color: #F8FAFC; }
    .stPlotlyChart { border: 1px solid #334155; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 3. データの読み込み
@st.cache_data
def load_data():
    df = pd.read_csv('canary_data.csv', index_col=0, parse_dates=True)
    return df

try:
    df = load_data()

    # --- ヘッダーエリア ---
    st.title("🐤 Macro Canary Dashboard v3")
    st.caption(f"Brand: KURURUGI | Last Updated: {df.index[-1].strftime('%Y-%m-%d')}")

    # --- Section 1: KPIカード（最上段） ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        val = df['10Y2Y_Spread'].iloc[-1]
        delta = val - df['10Y2Y_Spread'].iloc[-2]
        st.metric("10Y-2Y Spread", f"{val:.2f}%", delta=f"{delta:.2f}%", delta_color="inverse")
    with c2:
        val_hy = df['HY_Spread'].iloc[-1]
        st.metric("HY Spread", f"{val_hy:.2f}%", delta="Stable")
    with c3:
        # リスクスコアの簡易計算（例）
        risk_score = 72 
        st.metric("Composite Risk", f"{risk_score}/100", delta="High", delta_color="off")
    with c4:
        st.metric("Status", "ALERT", delta_color="off")

    st.divider()

    # --- Section 2: メインチャート（中段） ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📉 Leading Indicator: 10Y-2Y Yield Spread")
        fig = go.Figure()
        # グロー効果（エリア塗りつぶし）
        fig.add_trace(go.Scatter(
            x=df.index, y=df['10Y2Y_Spread'],
            mode='lines',
            line=dict(color='#F43F5E', width=3),
            fill='tozeroy',
            fillcolor='rgba(244, 63, 94, 0.1)'
        ))
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("🕸️ Risk Radar")
        # レーダーチャート用のサンプルデータ
        categories = ['Market', 'Physical', 'Housing', 'Labor', 'AI Risk']
        risk_values = [85, 40, 65, 55, 80]
        fig_radar = px.line_polar(r=risk_values, theta=categories, line_close=True)
        fig_radar.update_traces(fill='toself', line_color='#F43F5E', fillcolor='rgba(244, 63, 94, 0.3)')
        fig_radar.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # --- Section 3: 分析ノート（下段） ---
    with st.expander("📝 KURURUGI's Analysis Note", expanded=True):
        st.write(f"""
        現在の分析結果：10Y-2Yスプレッドが {val:.2f}% となり、逆イールド解消後のスティープ化が進行中。
        歴史的なリセッションシグナルが点灯しています。実体経済指標との乖離に注意が必要です。
        """)

except Exception as e:
    st.error(f"データの読み込みに失敗しました。先に data_fetcher.py を実行してください。 エラー: {e}")
