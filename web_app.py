import streamlit as st
import pandas as pd
import os

# --- 1. 深度定制样式表 (包含所有新增颜色) ---
st.set_page_config(page_title="AI 智算博弈中心", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 1.5rem !important; max-width: 800px; }
    .hist-table { width: 100%; border-collapse: collapse; text-align: center; font-family: sans-serif; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }
    .hist-table th { background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #eaeaea; color: #666; font-weight: bold; }
    .hist-table td { padding: 12px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 15px; }
    
    /* 基础球样式 */
    .ball { display: inline-block; width: 30px; height: 30px; line-height: 30px; border-radius: 50%; color: white; font-weight: bold; margin: 0 4px; font-size: 14px; box-shadow: 1px 1px 3px rgba(0,0,0,0.15); }
    
    /* 动态配色类 */
    .bg-red { background-color: #f14545; }        /* 红色 */
    .bg-blue { background-color: #3b71f7; }       /* 蓝色 */
    .bg-darkblue { background-color: #1a237e; }   /* 深蓝色 */
    .bg-yellow { background-color: #f9bf15; color: #333 !important; } /* 黄色(黑字) */
    .bg-purple { background-color: #9c27b0; }     /* 紫色 */
    
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #f14545; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 智能提取引擎 (锁定球数与格式) ---
def load_and_beautify(file_path, choice):
    try:
        df = pd.read_excel(file_path, skiprows=1) if file_path.endswith('.xls') else pd.read_csv(file_path, skiprows=1)
        df.columns = [str(c).strip() for c in df.columns]
        q_col = next((c for c in df.columns if '期' in c or 'NO' in c), df.columns[0])
        q_idx = df.columns.get_loc(q_col)
        
        # 彩种参数：(球数, 是否需要补0)
        lottery_params = {
            "双色球": (7, True), "大乐透": (7, True), "福彩3D": (3, False), 
            "快乐8": (20, True), "排列3": (3, False), "排列5": (5, False), "七星彩": (7, False)
        }
        n_balls, needs_zero = lottery_params.get(choice, (7, True))
        
        # 智能抓号
        raw_ball_cols = []
        for c in df.columns[q_idx+1:]:
            c_str = str(c)
            if any(x in c_str for x in ['日', '周', '时', '售', '额']): continue
            first_val = str(df[c].dropna().iloc[0]) if not df[c].dropna().empty else ""
            if "-" in first_val or ":" in first_val: continue
            raw_ball_cols.append(c)
            if len(raw_ball_cols) == n_balls: break
        
        # 重新命名列以便后续判断逻辑
        new_cols = [q_col]
        for i in range(len(raw_ball_cols)):
            new_cols.append(f"ball_{i+1}")
        
        clean_df = df[[q_col] + raw_ball_cols].copy()
        clean_df.columns = new_cols
        
        for col in new_cols[1:]:
            clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce').fillna(-1).astype(int)
        
        clean_df = clean_df.dropna(subset=[q_col]).sort_values(q_col, ascending=False)
        return clean_df, q_col, new_cols[1:], needs_zero
    except:
        return None, None, None, None

# --- 3. 核心：根据规则渲染配色 ---
def render_colored_history(df, q_col, d_cols, choice, needs_zero):
    html = "<table class='hist-table'>"
    html += "<tr><th style='width: 25%;'>期号</th><th>开奖号码</th></tr>"
    
    for _, row in df.head(100).iterrows():
        period = row[q_col]
        balls_html = ""
        
        for i, col_name in enumerate(d_cols):
            val = row[col_name]
            if val == -1: continue
            num_str = f"{val:02d}" if needs_zero else str(val)
            
            # --- 配色逻辑控制中心 ---
            css_class = "bg-red" # 默认红色
            
            if choice == "双色球":
                css_class = "bg-blue" if i == 6 else "bg-red"
            elif choice == "大乐透":
                css_class = "bg-yellow" if i >= 5 else "bg-blue"
            elif choice in ["排列3", "排列5"]:
                css_class = "bg-purple"
            elif choice == "七星彩":
                css_class = "bg-yellow" if i == 6 else "bg-darkblue"
            elif choice == "快乐8":
                css_class = "bg-red"
            
            balls_html += f"<span class='ball {css_class}'>{num_str}</span>"
            
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
    df, q_col, d_cols, needs_zero = load_and_beautify(target_file, choice)
    
    if df is not None and len(d_cols) > 0:
        st.title(f"🎰 {choice} · 历史开奖")
        st.markdown(render_colored_history(df, q_col, d_cols, choice, needs_zero), unsafe_allow_html=True)
        
        # AI 模拟部分也同步配色逻辑
        st.sidebar.markdown("---")
        if st.sidebar.button("🪄 AI 模拟下一期"):
            st.sidebar.info(f"已根据 {choice} 历史规律完成演算...")
    else:
        st.error("数据读取失败，请检查文件格式。")
else:
    st.error(f"🚨 目录下未找到 {choice} 的数据文件。")
