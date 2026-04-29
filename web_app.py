import streamlit as st
import pandas as pd
import plotly.express as px
import os
import random

# --- 1. 尖端视觉注入 ---
st.set_page_config(page_title="AI 智算博弈中心", layout="wide")
st.markdown("""
    <style>
    .red-ball { background: #ff4b4b; color: white; border-radius: 50%; padding: 5px 10px; margin: 2px; font-weight: bold; }
    .blue-ball { background: #4b7bff; color: white; border-radius: 50%; padding: 5px 10px; margin: 2px; font-weight: bold; }
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 智能格式修复引擎 ---
def smart_load(file_path, l_type):
    try:
        # 跳过空行，读取数据
        df = pd.read_excel(file_path, skiprows=1) if file_path.endswith('.xls') else pd.read_csv(file_path, skiprows=1)
        df.columns = [str(c).strip() for c in df.columns]
        
        # 1. 找期号列
        q_col = next((c for c in ['开奖期号', '期号', 'NO'] if c in df.columns), df.columns[0])
        
        # 2. 提取纯数字号码列
        # 我们只取期号后面那些真正带数字的列
        all_cols = list(df.columns)
        q_idx = all_cols.index(q_col)
        raw_nums = [c for c in all_cols[q_idx+1:] if not any(x in c for x in ['日期', '金额', 'Unnamed'])]
        
        # 3. 强行标注（让人一眼看懂）
        final_cols = [q_col]
        rename_map = {q_col: "期号"}
        
        num_count = 3 if l_type == "福彩3D" else 7 if l_type in ["双色球", "大乐透"] else 5
        use_data_cols = raw_nums[:num_count]
        
        for i, c in enumerate(use_data_cols):
            new_name = f"球{i+1}"
            if l_type == "双色球" and i == 6: new_name = "蓝球"
            if l_type == "大乐透" and i >= 5: new_name = f"蓝球{i-4}"
            rename_map[c] = new_name
            final_cols.append(c)
            
        res_df = df[final_cols].rename(columns=rename_map).dropna(subset=["期号"])
        res_df = res_df.sort_values("期号", ascending=False) # 最新排第一
        return res_df, "期号", [c for c in rename_map.values() if "球" in c]
    except: return None, None, None

# --- 3. 配置 ---
LOTTO = {
    "双色球": {"key": "ssq", "max": 33},
    "福彩3D": {"key": "3d", "max": 9},
    "大乐透": {"key": "dlt", "max": 35},
    "快乐8": {"key": "kl8", "max": 80}
}

# --- 4. 界面渲染 ---
st.sidebar.title("💎 专家决策系统")
choice = st.sidebar.selectbox("🎯 选择彩种", list(LOTTO.keys()))
target = LOTTO[choice]

# 自动匹配仓库文件
file = next((f for f in os.listdir(".") if target['key'] in f.lower()), None)

if file:
    df, q_col, d_cols = smart_load(file, choice)
    
    if df is not None:
        st.title(f"🎰 {choice} · 专业分析版")
        
        # --- 模块 A: AI 模拟区 ---
        with st.container():
            st.subheader("🤖 AI 模拟推算 (基于最新期)")
            last_row = df.iloc[0]
            st.write(f"最新第 {last_row[q_col]} 期开奖：")
            
            # 漂亮地展示
            ball_html = ""
            for c in d_cols:
                color = "blue-ball" if "蓝" in c else "red-ball"
                ball_html += f'<span class="{color}">{last_row[c]}</span> '
            st.markdown(ball_html, unsafe_allow_html=True)
            
            if st.button("🪄 生成下期 AI 预测"):
                pred = sorted(random.sample([str(i).zfill(2) for i in range(1, target['max']+1)], len(d_cols)))
                st.success(f"建议方案：{' '.join(pred)}")

        # --- 模块 B: 趋势图 ---
        st.divider()
        st.subheader("📈 核心趋势走势图")
        plot_df = df.head(50).copy()
        plot_df[d_cols[0]] = pd.to_numeric(plot_df[d_cols[0]], errors='coerce')
        fig = px.line(plot_df[::-1], x=q_col, y=d_cols[0], markers=True, title="首位球号波动情况")
        st.plotly_chart(fig, use_container_width=True)

        # --- 模块 C: 让人看懂的原始数据 ---
        st.divider()
        st.subheader("📑 历史数据明细 (已清洗对齐)")
        st.dataframe(df.head(50), use_container_width=True)
else:
    st.error("🚨 找不到对应的历史数据文件，请检查上传！")
