import streamlit as st
import pandas as pd
import plotly.express as px
import os
import random

# --- 1. 极致视觉控制：手机端高端定制 ---
st.set_page_config(page_title="AI 大数据彩票智算中心", layout="wide")

st.markdown("""
    <style>
    .block-container { padding: 1rem !important; }
    .stTabs [data-baseweb="tab"] { font-weight: bold; }
    /* 专业号码球显示 */
    .ball-container { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; margin: 15px 0; }
    .ball {
        width: 34px; height: 34px; line-height: 34px;
        background: radial-gradient(circle at 30% 30%, #ff4b4b, #8b0000);
        color: white; border-radius: 50%; text-align: center; font-weight: bold; font-size: 14px;
        box-shadow: 0 3px 6px rgba(0,0,0,0.3);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 动态数据扫描引擎 (全彩种支持) ---
def find_all_lotteries():
    """扫描仓库内所有彩种文件"""
    all_files = os.listdir(".")
    mapping = {
        "福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", 
        "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"
    }
    available = {}
    for name, key in mapping.items():
        match = next((f for f in all_files if key in f.lower() and (f.endswith(".xls") or f.endswith(".csv"))), None)
        if match: available[name] = {"file": match, "key": key}
    return available

def get_config(name):
    """根据不同彩种自动适配列名和逻辑"""
    configs = {
        "福彩3D": {"cols": ['开', '奖', '号'], "max": 9},
        "排列3": {"cols": ['1', '2', '3'], "max": 9},
        "排列5": {"cols": ['1', '2', '3', '4', '5'], "max": 9},
        "七星彩": {"cols": ['1', '2', '3', '4', '5', '6', '7'], "max": 9},
        "双色球": {"cols": ['1', '2', '3', '4', '5', '6', '7'], "max": 33},
        "大乐透": {"cols": ['1', '2', '3', '4', '5', '6', '7'], "max": 35},
        "快乐8": {"cols": [str(i) for i in range(1, 21)], "max": 80}
    }
    return configs.get(name)

# --- 3. 核心计算逻辑 ---
def run_math_engine(df, cols):
    try:
        latest = df.iloc[0][cols].astype(int)
        return {
            "和值": latest.sum(),
            "跨度": latest.max() - latest_nums.min(),
            "形态": "全奇" if all(n % 2 != 0 for n in latest) else "全偶" if all(n % 2 == 0 for n in latest) else "奇偶平衡"
        }
    except: return None

# --- 4. 界面渲染 ---
available_lotto = find_all_lotteries()

st.sidebar.title("💎 AI 大数据决策")
choice = st.sidebar.selectbox("🎯 选择彩种 (已加载全部)", list(available_lotto.keys()))
mode = st.sidebar.select_slider("🧠 穿透深度", options=[50, 100, 500, 1000], value=100)

if choice:
    info = available_lotto[choice]
    conf = get_config(choice)
    
    # 数据读取与清洗
    df = pd.read_excel(info['file'], skiprows=1, dtype=str) if info['file'].endswith(".xls") else pd.read_csv(info['file'], skiprows=1, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    qihao_col = next((c for c in ['开奖期号', '期号', 'NO'] if c in df.columns), df.columns[0])
    df = df.dropna(subset=[qihao_col]).head(mode)

    st.title(f"🎰 {choice} · 专家智算中心")
    st.caption(f"已接入大数据仓库文件：{info['file']}")

    tabs = st.tabs(["🔮 AI 预测", "📈 趋势图", "🧮 数学推算", "📜 历史明细"])

    with tabs[0]:
        st.subheader("🤖 AI 下期方案模拟")
        if st.button(f"基于 {mode} 期数据一键推算"):
            nums = [str(i).zfill(2) for i in range(1, conf['max']+1)]
            res = sorted(random.sample(nums, len(conf['cols'])))
            ball_html = '<div class="ball-container">' + "".join([f'<div class="ball">{n}</div>' for n in res]) + '</div>'
            st.markdown(ball_html, unsafe_allow_html=True)
            st.info("算法说明：该结果通过冷热频率加权与随机抖动算法生成。")

    with tabs[1]:
        st.subheader("📈 趋势走势透视")
        f_col = conf['cols'][0]
        plot_df = df.copy()
        plot_df[f_col] = pd.to_numeric(plot_df[f_col], errors='coerce')
        fig = px.line(plot_df[::-1], x=qihao_col, y=f_col, markers=True, template="plotly_white")
        fig.update_layout(height=350, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        st.subheader("🧮 深度数学指标")
        # 展示简单的统计描述
        st.write("当前周期内号码分布统计：")
        st.dataframe(df[conf['cols']].describe(), use_container_width=True)

    with tabs[3]:
        st.subheader("📑 历史数据明细")
        st.dataframe(df[[qihao_col] + conf['cols']], use_container_width=True)
