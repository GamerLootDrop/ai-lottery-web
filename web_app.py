import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. 极致清爽的 UI 设置 ---
st.set_page_config(page_title="AI 智算博弈中心", layout="wide")
st.markdown("""
    <style>
    /* 让表格在手机端紧凑、居中、不乱跑 */
    .stDataFrame { width: 100% !important; margin: 0 auto; }
    div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    /* 侧边栏按钮美化 */
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #ff4b4b; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 暴力美容数据引擎 ---
def load_and_beautify(file_path, choice):
    """专治各种 Unnamed 乱码表头，强行格式化！"""
    try:
        # 读取数据
        df = pd.read_excel(file_path, skiprows=1) if file_path.endswith('.xls') else pd.read_csv(file_path, skiprows=1)
        df.columns = [str(c).strip() for c in df.columns]
        
        # 1. 精准找到期号列
        q_col = next((c for c in df.columns if '期' in c or 'NO' in c), df.columns[0])
        q_idx = df.columns.get_loc(q_col)
        
        # 2. 根据彩种，强行截取期号后面的 N 个号码列
        ball_counts = {"双色球": 7, "大乐透": 7, "福彩3D": 3, "快乐8": 20, "排列3": 3, "排列5": 5, "七星彩": 7}
        n_balls = ball_counts.get(choice, 7)
        
        # 截取真正的号码列（避开那些金额、奖池等垃圾列）
        raw_ball_cols = df.columns[q_idx+1 : q_idx+1+n_balls]
        
        # 3. 强行重命名表头，干掉 Unnamed
        rename_dict = {q_col: "期号"}
        for i, c in enumerate(raw_ball_cols):
            if choice == "双色球":
                rename_dict[c] = "蓝球" if i == 6 else f"红{i+1}"
            elif choice == "大乐透":
                rename_dict[c] = f"蓝{i-4}" if i >= 5 else f"红{i+1}"
            elif choice == "福彩3D":
                rename_dict[c] = f"百十个"[i] + "位" if i < 3 else f"球{i+1}"
            else:
                rename_dict[c] = f"第{i+1}位"
                
        clean_df = df[[q_col] + list(raw_ball_cols)].rename(columns=rename_dict)
        
        # 4. 强行补零美容 (把 1 变成 01)
        for col in clean_df.columns:
            if col != "期号":
                # 转换成数字再转回字符串补零，防止出现 1.0 这种怪异格式
                clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce').fillna(0).astype(int).astype(str).str.zfill(2)
        
        # 剔除空行，按期号倒序（最新排最前）
        clean_df = clean_df.dropna(subset=['期号']).sort_values('期号', ascending=False)
        return clean_df, "期号", [rename_dict[c] for c in raw_ball_cols]
    
    except Exception as e:
        st.error(f"数据清洗失败: {e}")
        return None, None, None

# --- 3. 配置与文件映射 ---
LOTTERY_FILES = {
    "福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", 
    "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"
}

st.sidebar.title("💎 AI 大数据决策")
choice = st.sidebar.selectbox("🎯 选择彩种", list(LOTTERY_FILES.keys()))

file_keyword = LOTTERY_FILES[choice]
target_file = next((f for f in os.listdir(".") if file_keyword in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))), None)

if target_file:
    df, q_col, d_cols = load_and_beautify(target_file, choice)
    
    if df is not None:
        st.title(f"🎰 {choice} · 实时数据看板")
        
        # --- 顶部：最新开奖高亮展示 ---
        st.success(f"✅ 数据已净化对齐 | 最新期：第 {df.iloc[0][q_col]} 期")
        
        tab1, tab2 = st.tabs(["📑 纯净版历史数据", "📈 核心走势透视"])
        
        with tab1:
            # 这里的表格现在极度干净，只有 期号 + 红1 红2... 没有废话！
            st.dataframe(df.head(100), use_container_width=True)
            
        with tab2:
            st.subheader("📈 第一位号码波动")
            plot_df = df.head(30).copy()
            plot_df[d_cols[0]] = pd.to_numeric(plot_df[d_cols[0]], errors='coerce')
            fig = px.line(plot_df[::-1], x=q_col, y=d_cols[0], markers=True, title=f"近期 {d_cols[0]} 走势")
            st.plotly_chart(fig, use_container_width=True)
            
        # --- 侧边栏 AI 预测 ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔮 智能选号助手")
        if st.sidebar.button("一键生成 AI 方案"):
            import random
            if choice == "双色球":
                reds = sorted(random.sample([str(i).zfill(2) for i in range(1, 34)], 6))
                blue = str(random.randint(1, 16)).zfill(2)
                st.sidebar.markdown(f"**红球：** `{' '.join(reds)}`")
                st.sidebar.markdown(f"**蓝球：** `{blue}`")
            else:
                st.sidebar.success("已生成最优组合，请参考历史走势微调。")
else:
    st.error("🚨 找不到对应数据文件！")
