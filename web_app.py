import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="AI 全彩种决策中心", layout="wide")

# 定义彩种配置及其对应的文件名和列名处理逻辑
LOTTERY_CONFIG = {
    "中国大乐透": {"file": "dlt.xls - data.csv", "r_cols": range(2, 7), "b_cols": range(7, 9)},
    "双色球": {"file": "ssq.xls - 双色球-历史开奖数据.csv", "r_cols": range(2, 8), "b_cols": [8]},
    "福彩3D": {"file": "3d.xls - data.csv", "r_cols": range(2, 5), "b_cols": []},
    "排列3": {"file": "p3.xls - 排列3-历史开奖数据.csv", "r_cols": range(2, 5), "b_cols": []},
    "排列5": {"file": "p5.xls - 排列五-历史开奖数据.csv", "r_cols": range(2, 7), "b_cols": []},
    "七星彩": {"file": "7xc.xls - 七星彩-历史开奖数据.csv", "r_cols": range(2, 8), "b_cols": [8]},
    "快乐8": {"file": "kl8.xls - data.csv", "r_cols": range(2, 22), "b_cols": []}
}

@st.cache_data
def load_historical_data(conf):
    if not os.path.exists(conf['file']): return None
    try:
        # 跳过表头的脏数据，读取原始数据
        df = pd.read_csv(conf['file'], skiprows=1, dtype=str).dropna(subset=['开奖期号'])
        # 提取期号和球号
        res = []
        for _, row in df.iterrows():
            r = " ".join([str(row.iloc[i]).split('.')[0].zfill(2) for i in conf['r_cols'] if not pd.isna(row.iloc[i])])
            b = " ".join([str(row.iloc[i]).split('.')[0].zfill(2) for i in conf['b_cols'] if not pd.isna(row.iloc[i])])
            res.append({"期号": str(row['开奖期号']).split('.')[0], "红球": r, "蓝球": b})
        return pd.DataFrame(res)
    except: return None

# 侧边栏导航
st.sidebar.title("💎 AI 大数据决策系统")
choice = st.sidebar.selectbox("选择要分析的彩种", list(LOTTERY_CONFIG.keys()))
num_periods = st.sidebar.select_slider("AI 计算跨度", options=[50, 100, 500, 1000, 2000, 5000], value=100)

# 加载数据
data = load_historical_data(LOTTERY_CONFIG[choice])

if data is not None and not data.empty:
    st.title(f"📊 {choice} · 20年历史大数据分析")
    st.success(f"已成功加载该彩种历史数据：{len(data)} 期。正在基于最近 {min(num_periods, len(data))} 期进行推演。")
    
    # AI 走势图展示
    analysis_df = data.head(num_periods).copy()
    st.subheader("趋势走势图")
    # 示例走势：将红球第一位取出绘图
    analysis_df['首号'] = analysis_df['红球'].str.split().str[0].astype(float)
    fig = px.line(analysis_df[::-1], x='期号', y='首号', title="首位号码历史波动走势")
    st.plotly_chart(fig, use_container_width=True)

    # 数据表展示
    st.subheader("历史明细预览")
    st.dataframe(data, use_container_width=True)
else:
    st.error(f"未能正确读取 {choice} 的数据文件，请确认文件名是否匹配。")
