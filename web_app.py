import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="AI 全彩种决策中心", layout="wide")

def find_my_file(keyword):
    all_files = os.listdir(".")
    for f in all_files:
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
        # 💡 智能判断读取方式
        if actual_file.endswith(".xls"):
            # 使用 Excel 模式读取
            df = pd.read_excel(actual_file, skiprows=1, dtype=str)
        else:
            # 使用 CSV 模式读取
            df = pd.read_csv(actual_file, skiprows=1, dtype=str, encoding='gbk')
            
        df.columns = [c.strip() for c in df.columns]
        
        st.title(f"📊 {choice} · 历史数据分析")
        st.success(f"✅ 已通过专业格式加载文件: {actual_file}")
        
        if '开奖期号' in df.columns:
            df = df.dropna(subset=['开奖期号'])
            st.info(f"🔢 累计分析：{len(df)} 期数据")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("读取成功，但表头不匹配。")
            st.write("现在的列名是：", list(df.columns))
            
    except Exception as e:
        st.error(f"⚠️ 读取失败: {e}")
        st.info("建议：请尝试在本地将文件另存为 'CSV (逗号分隔)' 格式再上传。")
else:
    st.error("🚨 找不到文件，请检查仓库。")
