import streamlit as st
import pandas as pd
import random
import time
import os
import plotly.graph_objects as go
import plotly.express as px

# 1. 网页基础配置
st.set_page_config(page_title="AI 双引擎彩票平台 V3.2", page_icon="📈", layout="wide")

st.markdown("""<style>.main { background-color: #f8f9fa; }.stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }</style>""", unsafe_allow_html=True)

# 2. 数据加载引擎
@st.cache_data
def load_and_process_data(file_name, game_type):
    if not os.path.exists(file_name):
        return None
    try:
        df_raw = pd.read_csv(file_name, encoding='utf-8', keep_default_na=False)
        processed_rows = []
        big_threshold = 18 if game_type == "中国大乐透" else 17 
        for _, row in df_raw.iterrows():
            try:
                # 兼容性修复：处理可能的逗号或空格分隔
                red_str = str(row['红球']).replace(',', ' ').strip()
                blue_str = str(row['蓝球']).replace(',', ' ').strip()
                if not red_str or not blue_str: continue
                
                balls = [int(x) for x in red_str.split()]
                blue_balls = [int(x) for x in blue_str.split()]
                
                processed_rows.append({
                    '期号': row['期号'], '红球': red_str, '蓝球': blue_str,
                    '和值': sum(balls),
                    '奇数个数': sum(1 for x in balls if x % 2 != 0),
                    '偶数个数': sum(1 for x in balls if x % 2 == 0),
                    '大号个数': sum(1 for x in balls if x >= big_threshold),
                    '小号个数': sum(1 for x in balls if x < big_threshold)
                })
            except: continue
        return pd.DataFrame(processed_rows)
    except Exception as e:
        st.error(f"数据读取失败: {e}")
        return None

def get_omission(df, ball_type='red', max_num=35):
    column = '红球' if ball_type == 'red' else '蓝球'
    all_balls = [[int(x) for x in str(row).replace(',', ' ').split()] for row in df[column]]
    omission = {i: next((idx for idx, balls in enumerate(all_balls) if i in balls), len(all_balls)) for i in range(1, max_num + 1)}
    return omission

def draw_classic_trend_chart(df, game_type, red_max, red_need):
    display_num = min(len(df), 100)
    recent_df = df.head(display_num).copy().iloc[::-1] 
    fig = go.Figure()
    theme_color = "#e63946" if game_type == "双色球" else "#1d3557"
    for i in range(red_need):
        x_vals, y_vals, texts = [], [], []
        for index, row in recent_df.iterrows():
            balls = sorted([int(x) for x in str(row['红球']).replace(',', ' ').split()])
            if i < len(balls):
                x_vals.append(balls[i]); y_vals.append(str(row['期号'])); texts.append(str(balls[i]).zfill(2))
        fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines+markers+text', text=texts,
            textfont=dict(color='white', size=12), textposition='middle center',
            marker=dict(size=24, color=theme_color, line=dict(width=1, color='white')),
            line=dict(width=2), name=f'位{i+1}'))
    fig.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[0.5, red_max+0.5], side='top'),
        yaxis=dict(type='category', autorange="reversed"), plot_bgcolor='white', height=800, showlegend=False)
    return fig

# --- 侧边栏 ---
st.sidebar.title("平台控制台")
game_type = st.sidebar.radio("🎰 选择彩种", ["中国大乐透", "双色球"])
file, red_max, blue_max, red_need, blue_need = ("dlt_data.csv", 35, 12, 5, 2) if game_type == "中国大乐透" else ("ssq_data.csv", 33, 16, 6, 1)

df = load_and_process_data(file, game_type)

# --- 主界面 ---
st.title(f"📊 {game_type} 决策中心")
if df is not None and not df.empty:
    st.caption(f"🟢 数据已加载最新 {len(df)} 期")
    tab1, tab2, tab3 = st.tabs(["📈 专业走势", "🤖 智能出号", "🔮 AI 模拟"])
    with tab1:
        st.plotly_chart(draw_classic_trend_chart(df, game_type, red_max, red_need), use_container_width=True)
    with tab2:
        if st.button("🎲 生成方案", type="primary"):
            for i in range(1, 6):
                r = sorted(random.sample(range(1, red_max+1), red_need))
                b = sorted(random.sample(range(1, blue_max+1), blue_need))
                st.success(f"方案{i}: 红{[str(x).zfill(2) for x in r]} 蓝{[str(x).zfill(2) for x in b]}")
    with tab3:
        st.info("数据分析引擎运行正常。")
else:
    st.error("数据未连接！请检查 GitHub 中的 CSV 文件内容。")
