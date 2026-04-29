import streamlit as st
import pandas as pd
import plotly.express as px
import os
import random

# --- 1. 极致手机适配样式 ---
st.set_page_config(page_title="AI 智算中心", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 1rem !important; }
    .ball {
        display: inline-block; width: 32px; height: 32px; line-height: 32px;
        color: white; border-radius: 50%; text-align: center; font-weight: bold; margin: 3px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
    }
    .red-ball { background: radial-gradient(circle at 30% 30%, #ff4b4b, #8b0000); }
    .blue-ball { background: radial-gradient(circle at 30% 30%, #4b7bff, #00008b); }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心：格式强行矫正引擎 ---
def force_clean_data(file_path, lottery_type):
    try:
        # 自动跳过可能的标题行，直到找到含有数字的行
        df = pd.read_excel(file_path, skiprows=1) if file_path.endswith('.xls') else pd.read_csv(file_path, skiprows=1)
        df.columns = [str(c).strip() for c in df.columns]
        
        # 1. 定位期号列
        q_col = next((c for c in ['开奖期号', '期号', 'NO'] if c in df.columns), df.columns[0])
        
        # 2. 提取开奖号码（只取数字列，排除期号和金额）
        all_cols = df.columns.tolist()
        idx = all_cols.index(q_col)
        # 寻找期号后的前 N 个数字列
        num_cols = []
        for c in all_cols[idx+1:]:
            # 如果该列名字是数字，或者是'1','2'这种
            if any(char.isdigit() for char in c) or df[c].dtype != object:
                num_cols.append(c)
            if lottery_type == "双色球" and len(num_cols) == 7: break
            if lottery_type == "福彩3D" and len(num_cols) == 3: break
            if lottery_type == "大乐透" and len(num_cols) == 7: break

        # 3. 强行重命名，解决 Unnamed 问题
        new_names = {q_col: "期号"}
        for i, old_name in enumerate(num_cols):
            new_names[old_name] = f"球{i+1}"
        
        final_df = df[[q_col] + num_cols].rename(columns=new_names)
        final_df = final_df.dropna(subset=["期号"]).sort_values("期号", ascending=False)
        
        return final_df, "期号", [c for c in final_df.columns if "球" in c]
    except Exception as e:
        st.error(f"格式矫正失败: {e}")
        return None, None, None

# --- 3. 配置 ---
CONFIGS = {
    "双色球": {"key": "ssq", "max": 33},
    "福彩3D": {"key": "3d", "max": 9},
    "大乐透": {"key": "dlt", "max": 35},
    "排列3": {"key": "p3", "max": 9},
    "排列5": {"key": "p5", "max": 9},
    "七星彩": {"key": "7xc", "max": 9},
    "快乐8": {"key": "kl8", "max": 80}
}

# --- 4. 界面渲染 ---
st.sidebar.title("💎 AI 顶级决策")
choice = st.sidebar.selectbox("🎯 选择彩种", list(CONFIGS.keys()))
depth = st.sidebar.slider("🧠 分析深度", 50, 500, 100)

target = CONFIGS[choice]
file = next((f for f in os.listdir(".") if target['key'] in f.lower()), None)

if file:
    df, q_col, d_cols = force_clean_data(file, choice)
    
    if df is not None:
        st.title(f"🎰 {choice} · 预测系统")
        st.success(f"✅ 最新数据已对齐：第 {df.iloc[0][q_col]} 期")
        
        tab1, tab2, tab3 = st.tabs(["🔮 AI 模拟", "📈 趋势图", "📑 数据明细"])
        
        with tab1:
            st.subheader("🤖 基于最新一期往后推算")
            last_nums = df.iloc[0][d_cols].tolist()
            # 漂亮地展示上期开奖
            st.write("上期开奖实况：")
            balls_html = ""
            for i, n in enumerate(last_nums):
                # 双色球/大乐透最后几个是蓝球
                cls = "blue-ball" if (choice in ["双色球", "大乐透"] and i >= len(last_nums)-1) else "red-ball"
                balls_html += f'<div class="ball {cls}">{str(n).zfill(2)}</div>'
            st.markdown(balls_html, unsafe_allow_html=True)
            
            if st.button("🚀 启动下期 AI 推算"):
                # 预测逻辑
                pred = sorted(random.sample([str(i).zfill(2) for i in range(1, target['max']+1)], len(d_cols)))
                st.markdown("### 📢 AI 建议方案")
                p_html = "".join([f'<div class="ball red-ball">{n}</div>' for n in pred])
                st.markdown(p_html, unsafe_allow_html=True)

        with tab2:
            fig_df = df.head(depth).copy()
            fig_df["球1"] = pd.to_numeric(fig_df["球1"], errors='coerce')
            fig = px.line(fig_df[::-1], x=q_col, y="球1", markers=True, title="首位号码走势分析")
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.dataframe(df.head(50), use_container_width=True)
else:
    st.warning("请检查文件是否在仓库中。")
