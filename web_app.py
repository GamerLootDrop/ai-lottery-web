import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="AI 全彩种决策中心", layout="wide")

# --- 核心：自动搜寻文件函数 ---
def find_my_file(keyword):
    # 获取当前目录下所有文件
    all_files = os.listdir(".")
    for f in all_files:
        # 只要文件名里包含关键字（比如 3d 或 ssq），且是 csv 结尾
        if keyword.lower() in f.lower() and f.endswith(".csv"):
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

st.sidebar.title("💎 AI 大数据决策系统")
choice = st.sidebar.selectbox("🎯 选择彩种", list(LOTTERY_MAP.keys()))

# 自动搜寻
keyword = LOTTERY_MAP[choice]
actual_file = find_my_file(keyword)

if actual_file:
    try:
        # 读取数据，跳过第一行空行
        df = pd.read_csv(actual_file, skiprows=1, dtype=str)
        df.columns = [c.strip() for c in df.columns] # 清理列名空格
        
        st.title(f"📊 {choice} · 历史数据分析")
        st.success(f"✅ 自动匹配到文件: {actual_file}")
        
        # 过滤掉没有期号的行
        if '开奖期号' in df.columns:
            df = df.dropna(subset=['开奖期号'])
            st.info(f"🔢 累计载入历史数据：{len(df)} 期")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("文件读取成功，但没找到'开奖期号'列，请检查表格表头。")
            st.write("当前表格列名：", list(df.columns))
            
    except Exception as e:
        st.error(f"解析文件出错: {e}")
else:
    st.error(f"🚨 搜寻失败！仓库里没找到名字包含 '{keyword}' 的CSV文件。")
    st.info("当前仓库里的文件清单：" + str([f for f in os.listdir(".") if f.endswith(".csv")]))
