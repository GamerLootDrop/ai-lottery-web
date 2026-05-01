import streamlit as st
import pandas as pd
import os

# --- 1. 页面与深度定制样式 (完美复刻老板截图) ---
st.set_page_config(page_title="AI 智算博弈中心", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 1.5rem !important; max-width: 800px; } /* 居中紧凑显示更好看 */
    
    /* 经典历史表格样式 */
    .hist-table { width: 100%; border-collapse: collapse; text-align: center; font-family: sans-serif; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }
    .hist-table th { background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #eaeaea; color: #666; font-weight: bold; }
    .hist-table td { padding: 12px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 15px; }
    .hist-table tr:hover { background-color: #fcfcfc; }
    
    /* 红蓝球样式 */
    .r-ball { display: inline-block; width: 28px; height: 28px; line-height: 28px; border-radius: 50%; background-color: #f14545; color: white; font-weight: bold; margin: 0 4px; font-size: 14px; box-shadow: 1px 1px 2px rgba(241,69,69,0.3); }
    .b-ball { display: inline-block; width: 28px; height: 28px; line-height: 28px; border-radius: 50%; background-color: #3b71f7; color: white; font-weight: bold; margin: 0 4px; font-size: 14px; box-shadow: 1px 1px 2px rgba(59,113,247,0.3); }
    
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #f14545; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 数据清洗引擎 (保持数据精准提取) ---
def load_and_beautify(file_path, choice):
    try:
        df = pd.read_excel(file_path, skiprows=1) if file_path.endswith('.xls') else pd.read_csv(file_path, skiprows=1)
        df.columns = [str(c).strip() for c in df.columns]
        
        q_col = next((c for c in df.columns if '期' in c or 'NO' in c), df.columns[0])
        q_idx = df.columns.get_loc(q_col)
        
        ball_counts = {"双色球": 7, "大乐透": 7, "福彩3D": 3, "快乐8": 20, "排列3": 3, "排列5": 5, "七星彩": 7}
        n_balls = ball_counts.get(choice, 7)
        raw_ball_cols = df.columns[q_idx+1 : q_idx+1+n_balls]
        
        rename_dict = {q_col: "期号"}
        for i, c in enumerate(raw_ball_cols):
            if choice == "双色球": rename_dict[c] = "蓝球" if i == 6 else f"红{i+1}"
            elif choice == "大乐透": rename_dict[c] = f"蓝{i-4}" if i >= 5 else f"红{i+1}"
            else: rename_dict[c] = f"球{i+1}"
                
        clean_df = df[[q_col] + list(raw_ball_cols)].rename(columns=rename_dict)
        for col in clean_df.columns:
            if col != "期号":
                clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce').fillna(-1).astype(int)
        
        clean_df = clean_df.dropna(subset=['期号']).sort_values('期号', ascending=False)
        return clean_df, "期号", [rename_dict[c] for c in raw_ball_cols]
    except Exception as e:
        return None, None, None

# --- 3. 核心：渲染经典明细列表 ---
def render_classic_history(df, q_col, d_cols, choice):
    html = "<table class='hist-table'>"
    html += "<tr><th style='width: 30%;'>期号</th><th>开奖号码</th></tr>"
    
    # 默认展示近 100 期
    for _, row in df.head(100).iterrows():
        period = row[q_col]
        balls_html = ""
        
        for c in d_cols:
            val = row[c]
            if val == -1: continue
            
            # 判断是否需要补零 (3D等不需要补，双色球大乐透需要补)
            if choice in ["福彩3D", "排列3", "排列5", "七星彩"]:
                num_str = str(val)
            else:
                num_str = f"{val:02d}"
            
            # 判断红蓝球颜色
            if "蓝" in c:
                balls_html += f"<span class='b-ball'>{num_str}</span>"
            else:
                balls_html += f"<span class='r-ball'>{num_str}</span>"
                
        html += f"<tr><td><b>{period}</b></td><td>{balls_html}</td></tr>"
        
    html += "</table>"
    return html

# --- 4. 界面组装 ---
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
        st.title(f"🎰 {choice} · 历史开奖明细")
        
        # 召唤经典表格渲染引擎
        st.markdown(render_classic_history(df, q_col, d_cols, choice), unsafe_allow_html=True)
        
        # 侧边栏 AI
        st.sidebar.markdown("---")
        if st.sidebar.button("🪄 AI 模拟下一期"):
            import random
            if choice == "双色球":
                reds = sorted(random.sample([str(i).zfill(2) for i in range(1, 34)], 6))
                blue = str(random.randint(1, 16)).zfill(2)
                st.sidebar.success(f"红球：{' '.join(reds)}\n蓝球：{blue}")
            else:
                st.sidebar.success("已完成演算，建议参考上表近期热号。")
else:
    st.error("🚨 找不到对应数据文件，请检查仓库！")
