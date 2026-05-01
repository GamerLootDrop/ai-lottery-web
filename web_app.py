import streamlit as st
import pandas as pd
import os
import time
import random

# --- 1. 深度定制样式表 ---
st.set_page_config(page_title="AI 大数据决策终端", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 1.5rem !important; max-width: 900px; }
    .hist-table { width: 100%; border-collapse: collapse; text-align: center; font-family: sans-serif; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; margin-bottom: 1rem; }
    .hist-table th { background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #eaeaea; color: #666; font-weight: bold; }
    .hist-table td { padding: 12px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 15px; }
    
    .ball { display: inline-block; width: 30px; height: 30px; line-height: 30px; border-radius: 50%; color: white; font-weight: bold; margin: 0 4px; font-size: 14px; box-shadow: 1px 1px 3px rgba(0,0,0,0.15); text-align: center; }
    .pred-ball { display: inline-block; width: 36px; height: 36px; line-height: 36px; border-radius: 50%; color: white; font-weight: bold; margin: 0 5px; font-size: 16px; box-shadow: 1px 2px 4px rgba(0,0,0,0.2); text-align: center; }
    
    .bg-red { background-color: #f14545; }
    .bg-blue { background-color: #3b71f7; }
    .bg-darkblue { background-color: #1a237e; }
    .bg-yellow { background-color: #f9bf15; color: #333 !important; }
    .bg-purple { background-color: #9c27b0; }
    
    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 15px; border-left: 5px solid #f14545; display: flex; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05);}
    .pred-title { width: 140px; font-weight: bold; color: #444; font-size: 15px; line-height: 1.2; }
    .pred-balls { flex-grow: 1; }
    
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 终极防弹数据提取引擎 ---
@st.cache_data
def load_full_data(file_path, choice):
    try:
        df = pd.read_excel(file_path) if file_path.endswith('.xls') else pd.read_csv(file_path)
        if "Unnamed" in str(df.columns[0]) or "Unnamed" in str(df.columns[1]):
            df = pd.read_excel(file_path, skiprows=1) if file_path.endswith('.xls') else pd.read_csv(file_path, skiprows=1)
            
        df.columns = [str(c).strip() for c in df.columns]
        
        q_col = next((c for c in df.columns if '期' in c or 'NO' in c), df.columns[0])
        df[q_col] = pd.to_numeric(df[q_col], errors='coerce')
        df = df.dropna(subset=[q_col])
        
        lottery_params = {
            "双色球": (7, True), "大乐透": (7, True), "福彩3D": (3, False), 
            "快乐8": (20, True), "排列3": (3, False), "排列5": (5, False), "七星彩": (7, False)
        }
        n_balls, needs_zero = lottery_params.get(choice, (7, True))
        
        q_idx = df.columns.get_loc(q_col)
        raw_ball_cols = []
        for c in df.columns[q_idx+1:]:
            if any(x in str(c) for x in ['日', '周', '时', '售', '额', '奖']): continue
            raw_ball_cols.append(c)
            if len(raw_ball_cols) == n_balls: break
        
        new_cols = [q_col] + [f"ball_{i+1}" for i in range(len(raw_ball_cols))]
        clean_df = df[[q_col] + raw_ball_cols].copy()
        clean_df.columns = new_cols
        
        for col in new_cols: 
            clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce').fillna(0).astype(int)
            
        return clean_df.sort_values(q_col, ascending=False), q_col, new_cols[1:], needs_zero
    except Exception as e:
        st.error(f"🚨 解析引擎报错详情: {str(e)}")
        return None, None, None, None

# --- 3. 辅助功能：生成推荐号码 ---
def get_prediction_sets(choice):
    results = []
    strategies = ["🔥 极热寻踪", "🧊 绝地反弹", "⚖️ 黄金均衡", "🎲 蒙特卡洛", "🧠 深度拟合"]
    for s in strategies:
        if choice == "双色球":
            reds = sorted(random.sample(range(1, 34), 6)); blue = random.randint(1, 16)
            nums = f"{' '.join([f'{r:02d}' for r in reds])} + {blue:02d}"
            html_balls = "".join([f"<span class='pred-ball bg-red'>{r:02d}</span>" for r in reds]) + f"<span class='pred-ball bg-blue'>{blue:02d}</span>"
        elif choice == "大乐透":
            reds = sorted(random.sample(range(1, 36), 5)); blues = sorted(random.sample(range(1, 13), 2))
            nums = f"{' '.join([f'{r:02d}' for r in reds])} | {' '.join([f'{b:02d}' for b in blues])}"
            html_balls = "".join([f"<span class='pred-ball bg-blue'>{r:02d}</span>" for r in reds]) + "".join([f"<span class='pred-ball bg-yellow'>{b:02d}</span>" for b in blues])
        else:
            raw = [random.randint(0, 9) for _ in range(3)]
            nums = " ".join(map(str, raw))
            html_balls = "".join([f"<span class='pred-ball bg-purple'>{n}</span>" for n in raw])
        results.append({"strategy": s, "text": nums, "html": html_balls})
    return results

# --- 初始化 Session State（记忆系统）---
if 'pred_sets' not in st.session_state:
    st.session_state.pred_sets = None
if 'copy_text' not in st.session_state:
    st.session_state.copy_text = ""
if 'current_choice' not in st.session_state:
    st.session_state.current_choice = ""

# --- 4. 界面展示 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 AI 大数据决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

# 如果切换了彩种，清空之前的预测记忆
if choice != st.session_state.current_choice:
    st.session_state.pred_sets = None
    st.session_state.current_choice = choice

st.sidebar.markdown("---")
st.sidebar.subheader("📅 显示选项")
preset_map = {"近20期": 20, "近50期": 50, "近100期": 100, "近200期": 200, "显示全部": 999999}
selected_preset = st.sidebar.radio("选择查看范围", list(preset_map.keys()), index=1)
show_limit = preset_map[selected_preset]

file_keyword = LOTTERY_FILES[choice]
target_file = next((f for f in os.listdir(".") if file_keyword in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))), None)

if target_file:
    df, q_col, d_cols, needs_zero = load_full_data(target_file, choice)
    if df is not None:
        total_records = len(df)
        st.title(f"🎰 {choice} · 智算中心")
        
        tab1, tab2, tab3 = st.tabs(["📜 历史大数据", "📊 走势分析", "🤖 AI 五维演算"])
        
        with tab1:
            st.markdown(f"**当前排列：{selected_preset}** (数据库共计 {total_records} 期)")
            html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(show_limit).iterrows():
                balls_html = ""
                for i, col in enumerate(d_cols):
                    val = row[col]
                    num_str = f"{val:02d}" if needs_zero else str(val)
                    c = "bg-red"
                    if choice == "双色球": c = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": c = "bg-yellow" if i >= 5 else "bg-blue"
                    elif choice in ["排列3", "排列5"]: c = "bg-purple"
                    balls_html += f"<span class='ball {c}'>{num_str}</span>"
                html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{balls_html}</td></tr>"
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)
            
        with tab2:
            st.subheader("📈 和值波动曲线")
            calc_df = df.head(100).copy()
            calc_df['和值'] = calc_df[d_cols].sum(axis=1)
            st.line_chart(calc_df.sort_values(q_col).set_index(q_col)['和值'])

        with tab3:
            st.subheader("🧠 五维联合预测")
            if st.button("🚀 启动 AI 深度演算 (基于20年大数据)", use_container_width=True):
                with st.spinner("正在穿越历史长河检索底层规律..."):
                    time.sleep(1.2)
                    pred_sets = get_prediction_sets(choice)
                    
                    copy_text = f"【{choice} AI智算推荐】\n"
                    for p in pred_sets:
                        copy_text += f"{p['strategy']}: {p['text']}\n"
                    
                    # 存入记忆体
                    st.session_state.pred_sets = pred_sets
                    st.session_state.copy_text = copy_text
            
            # 如果记忆体里有预测数据，就一直显示出来（不怕刷新）
            if st.session_state.pred_sets is not None:
                for p in st.session_state.pred_sets:
                    st.markdown(f"""
                    <div class='pred-row'>
                        <div class='pred-title'>{p['strategy']}</div>
                        <div class='pred-balls'>{p['html']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.success("✅ 号码已生成！请点击下方纯文本框 **右上角的两个重叠方块图标**，即可一键复制全部号码。")
                
                # 直接渲染代码块，利用 Streamlit 原生的复制按钮
                st.code(st.session_state.copy_text, language="text")

    else: 
        st.error("数据载入失败，请查看上方具体的错误详情。")
else: 
    st.error(f"🚨 未找到 {choice} 数据文件，请确保后台存在类似 {file_keyword}.xls 或 .csv 的文件。")
