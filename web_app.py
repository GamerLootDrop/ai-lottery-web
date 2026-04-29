import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="AI 全彩种决策中心", layout="wide")

# 🛠️ 这里的名字必须和你上传到 GitHub 的文件名完全一模一样！
LOTTERY_CONFIG = {
    "福彩3D": {"file": "3d.xls - data.csv", "r_cols": range(2, 5), "b_cols": []},
    "中国大乐透": {"file": "dlt.xls - data.csv", "r_cols": range(2, 7), "b_cols": range(7, 9)},
    "快乐8": {"file": "kl8.xls - data.csv", "r_cols": range(2, 22), "b_cols": []},
    "双色球": {"file": "ssq.xls - 双色球-历史开奖数据.csv", "r_cols": range(2, 8), "b_cols": [8]},
    "七星彩": {"file": "7xc.xls - 七星彩-历史开奖数据.csv", "r_cols": range(2, 8), "b_cols": [8]},
    "排列3": {"file": "p3.xls - 排列3-历史开奖数据.csv", "r_cols": range(2, 5), "b_cols": []},
    "排列5": {"file": "p5.xls - 排列五-历史开奖数据.csv", "r_cols": range(2, 7), "b_cols": []}
}

@st.cache_data
def load_historical_data(conf):
    if not os.path.exists(conf['file']):
        return None
    try:
        # 自动清洗逻辑：跳过空行，读取期号和开奖号
        df = pd.read_csv(conf['file'], skiprows=1, dtype=str)
        # 统一列名（适配你上传的表格）
        df.columns = [c.strip() for c in df.columns]
        res = []
        for _, row in df.iterrows():
            if pd.isna(row['开奖期号']): continue
            # 提取红球/前区
            r = " ".join([str(row.iloc[i]).split('.')[0].zfill(2) for i in conf['r_cols'] if i < len(row)])
            # 提取蓝球/后区
            b = " ".join([str(row.iloc[i]).split('.')[0].zfill(2) for i in conf['b_cols'] if i < len(row)])
            res.append({"期号": str(row['开奖期号']).split('.')[0], "红球": r, "蓝球": b})
        return pd.DataFrame(res)
    except Exception as e:
        st.sidebar.error(f"读取失败: {e}")
        return None

# --- 网页界面 ---
st.sidebar.title("💎 AI 大数据决策系统")
choice = st.sidebar.selectbox("🎯 选择彩种", list(LOTTERY_CONFIG.keys()))
num_periods = st.sidebar.select_slider("🧠 AI 计算跨度", options=[50, 100, 500, 1000, 2000, 5000], value=100)

data = load_historical_data(LOTTERY_CONFIG[choice])

if data is not None and not data.empty:
    st.title(f"📊 {choice} · 20年历史大数据分析")
    st.success(f"✅ 已加载 {len(data)} 期数据。正在分析最近 {min(num_periods, len(data))} 期。")
    
    # 展示走势图
    analysis_df = data.head(num_periods).copy()
    analysis_df['首号'] = analysis_df['红球'].str.split().str[0].astype(float)
    fig = px.line(analysis_df[::-1], x='期号', y='首号', title="首位号码历史波动走势")
    st.plotly_chart(fig, use_container_width=True)

    # 展示数据表
    st.subheader("历史明细预览")
    st.dataframe(data, use_container_width=True)
else:
    st.error(f"🚨 找不到文件: {LOTTERY_CONFIG[choice]['file']}")
    st.info("请确保文件名在 GitHub 里和代码里写的一模一样。")
