import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="AI 全彩种决策中心", layout="wide")

# --- 第一步：定义智能搜寻函数 ---
def smart_find_file(keyword):
    # 扫描当前目录下所有 CSV 文件
    all_files = [f for f in os.listdir(".") if f.endswith(".csv")]
    for f in all_files:
        # 只要文件名里包含关键字（不分大小写），就认为是我们要的文件
        if keyword.lower() in f.lower():
            return f
    return None

# 彩种关键字配置
LOTTERY_MAP = {
    "福彩3D": "3d",
    "中国大乐透": "dlt",
    "双色球": "ssq",
    "快乐8": "kl8",
    "七星彩": "7xc",
    "排列3": "p3",
    "排列5": "p5"
}

# --- 第二步：侧边栏控制 ---
st.sidebar.title("💎 AI 大数据决策系统")
choice = st.sidebar.selectbox("🎯 选择彩种", list(LOTTERY_MAP.keys()))

# --- 第三步：自动加载与纠错 ---
keyword = LOTTERY_MAP[choice]
actual_file = smart_find_file(keyword)

if actual_file:
    try:
        # 读取数据
        df = pd.read_csv(actual_file, skiprows=1, dtype=str)
        # 去掉列名里的空格
        df.columns = [c.strip() for c in df.columns]
        
        # 过滤掉空行
        df = df.dropna(subset=['开奖期号'])
        
        st.title(f"📊 {choice} · 历史数据分析")
        st.success(f"✅ 自动匹配成功！已加载文件：{actual_file}")
        st.info(f"🔢 累计分析历史数据：{len(df)} 期")
        
        # 展示数据
        st.subheader("历史开奖明细")
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"数据解析失败，可能是表格格式有变：{e}")
else:
    st.error(f"🚨 搜寻失败：仓库里找不到包含 '{keyword}' 的CSV文件")
    st.info("目前的搜寻清单：" + str([f for f in os.listdir(".") if f.endswith(".csv")]))
