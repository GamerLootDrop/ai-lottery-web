import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="AI 全彩种决策中心", layout="wide")

# --- 核心：自动搜寻文件函数（同时支持 xls 和 csv） ---
def find_my_file(keyword):
    all_files = os.listdir(".")
    for f in all_files:
        # 只要包含关键字，且后缀是 .xls 或 .csv 
        if keyword.lower() in f.lower() and (f.endswith(".xls") or f.endswith(".csv")):
            return f
    return None

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

keyword = LOTTERY_MAP[choice]
actual_file = find_my_file(keyword)

if actual_file:
    try:
        # 💡 关键点：即使后缀是 .xls，你上传的其实是文本格式，所以继续用 read_csv 读
        df = pd.read_csv(actual_file, skiprows=1, dtype=str, on_bad_lines='skip')
        df.columns = [c.strip() for c in df.columns] 
        
        st.title(f"📊 {choice} · 历史数据分析")
        st.success(f"✅ 成功锁定文件: {actual_file}")
        
        if '开奖期号' in df.columns:
            df = df.dropna(subset=['开奖期号'])
            st.info(f"🔢 累计分析：{len(df)} 期数据")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("读取成功但找不到'开奖期号'列。")
            st.write("现有列名：", list(df.columns))
            
    except Exception as e:
        st.error(f"解析出错 (可能不是纯文本格式): {e}")
else:
    st.error(f"🚨 找不到文件！")
    st.info(f"仓库里所有文件：{os.listdir('.')}")
