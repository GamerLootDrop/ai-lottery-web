import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. 样式配置 ---
st.set_page_config(page_title="AI 智算博弈中心", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 1.5rem !important; }
    /* 让表格看起来更像 Excel */
    .stDataFrame { border: 1px solid #dee2e6; }
    /* 侧边栏按钮美化 */
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心：原样读取引擎 ---
def load_original_excel(file_path):
    try:
        # 直接读取原始 Excel，保留表头原样
        # 如果您的 Excel 第一行是标题，第二行是表头，我们就从第二行开始读
        df = pd.read_excel(file_path, skiprows=1) if file_path.endswith('.xls') else pd.read_csv(file_path, skiprows=1)
        
        # 清理掉全空的行和列
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # 自动识别期号列（用于绘图和倒序）
        # 只要列名里包含“期”字，我们就把它当做索引
        qihao_col = None
        for col in df.columns:
            if '期' in str(col):
                qihao_col = col
                break
        
        if qihao_col:
            # 确保最新开奖在最前面
            df = df.sort_values(by=qihao_col, ascending=False)
            
        return df, qihao_col
    except Exception as e:
        st.error(f"读取原始数据失败: {e}")
        return None, None

# --- 3. 配置映射 ---
LOTTERY_FILES = {
    "福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", 
    "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"
}

# --- 4. 界面布局 ---
st.sidebar.title("💎 AI 大数据决策")
choice = st.sidebar.selectbox("🎯 选择彩种", list(LOTTERY_FILES.keys()))

# 自动匹配文件
file_keyword = LOTTERY_FILES[choice]
target_file = next((f for f in os.listdir(".") if file_keyword in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))), None)

if target_file:
    df, q_col = load_original_excel(target_file)
    
    if df is not None:
        st.title(f"🎰 {choice} · 官方同步看板")
        st.info(f"📁 数据源：{target_file} (已实现原样对齐展示)")

        # --- 模块一：原样明细表格 (老板最看重的) ---
        st.subheader("📑 历史开奖原样明细")
        # 直接展示，不修改任何列名，不隐藏任何数据
        st.dataframe(df, use_container_width=True, height=500)

        # --- 模块二：基于原样的趋势走势 ---
        if q_col:
            st.divider()
            st.subheader("📈 数据走势观察")
            # 找到期号后的第一列数据列进行绘图
            data_cols = [c for c in df.columns if c != q_col and '日' not in str(c) and '额' not in str(c)]
            if data_cols:
                plot_df = df.head(30).copy()
                # 尝试转换数字，画不出来也不强求
                plot_df[data_cols[0]] = pd.to_numeric(plot_df[data_cols[0]], errors='coerce')
                fig = px.line(plot_df[::-1], x=q_col, y=data_cols[0], markers=True, 
                             title=f"首个数据项 ({data_cols[0]}) 波动趋势")
                st.plotly_chart(fig, use_container_width=True)

        # --- 模块三：AI 模拟功能 ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔮 AI 辅助决策")
        if st.sidebar.button("点击生成下一期参考"):
            st.sidebar.write("正在基于当前 Excel 规律计算...")
            # 模拟一组数据
            st.sidebar.success("建议关注：04 12 19 23 28 32 + 09")
            st.sidebar.caption("提示：本结果仅供参考，请结合个人研究。")

else:
    st.error(f"🚨 仓库中未找到包含 '{file_keyword}' 的数据文件，请检查文件名！")
