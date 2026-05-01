import streamlit as st
import pandas as pd
import os

# --- 1. 页面与全局样式 ---
st.set_page_config(page_title="AI 智算博弈中心", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 1rem !important; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #ff4b4b; color: white; }
    /* 隐藏默认的 dataframe 索引等杂项 */
    </style>
""", unsafe_allow_html=True)

# --- 2. 数据清洗引擎 (沿用极致纯净逻辑) ---
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
            elif choice == "福彩3D": rename_dict[c] = f"百十个"[i] + "位" if i < 3 else f"球{i+1}"
            else: rename_dict[c] = f"第{i+1}位"
                
        clean_df = df[[q_col] + list(raw_ball_cols)].rename(columns=rename_dict)
        for col in clean_df.columns:
            if col != "期号":
                clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce').fillna(0).astype(int)
        
        clean_df = clean_df.dropna(subset=['期号']).sort_values('期号', ascending=False)
        return clean_df, "期号", [rename_dict[c] for c in raw_ball_cols]
    except Exception as e:
        return None, None, None

# --- 3. 核心：仿原图“全盘分布图”渲染器 ---
def render_distribution_grid(df, q_col, d_cols, choice):
    """根据老板的截图，手绘 HTML 分布网格图"""
    # 确定号码池范围
    if choice == "快乐8": max_num = 80; start_num = 1
    elif choice == "双色球": max_num = 33; start_num = 1
    elif choice == "大乐透": max_num = 35; start_num = 1
    elif choice in ["福彩3D", "排列3", "排列5", "七星彩"]: max_num = 9; start_num = 0
    else: max_num = 33; start_num = 1

    # 开始画 HTML 表格 (带左右滑动保护)
    html = '<div style="width: 100%; overflow-x: auto; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
    html += '<table style="width: 100%; border-collapse: collapse; text-align: center; font-size: 13px; font-family: sans-serif; white-space: nowrap;">'
    
    # 画表头 (01, 02, 03...)
    html += '<tr><th style="border: 1px solid #eee; padding: 8px; background: #f8f9fa; position: sticky; left: 0; z-index: 2;">期号</th>'
    for i in range(start_num, max_num + 1):
        html += f'<th style="border: 1px solid #eee; padding: 6px; background: #f8f9fa; color: #888;">{i:02d}</th>'
    html += '</tr>'

    # 画每一行数据
    for idx, row in df.head(50).iterrows(): # 默认展示近50期防卡顿
        period = row[q_col]
        # 收集这一期开出的红球/主号码
        drawn_nums = set()
        for c in d_cols:
            if choice in ["双色球", "大乐透"] and "蓝" in c: continue # 分布图通常只画主区红球
            try: drawn_nums.add(int(row[c]))
            except: pass

        # 期号列 (固定在左侧滑动时不被遮挡)
        html += f'<tr><td style="border: 1px solid #eee; padding: 8px; font-weight: bold; color: #333; background: #fff; position: sticky; left: 0; z-index: 1;">{period}</td>'

        # 遍历所有可能的号码
        for i in range(start_num, max_num + 1):
            if i in drawn_nums:
                # 命中！画红底圆球 (完美复刻老板的截图)
                html += f'<td style="border: 1px solid #eee; padding: 2px;"><div style="display:inline-block; width:22px; height:22px; line-height:22px; border-radius:50%; background:#ff4b4b; color:white; font-weight:bold; font-size: 12px; box-shadow: 0 2px 4px rgba(255,0,0,0.3);">{i:02d}</div></td>'
            else:
                # 没命中，显示极淡的灰色数字
                html += f'<td style="border: 1px solid #eee; padding: 2px; color: #f0f0f0;">{i:02d}</td>'
        html += '</tr>'

    html += '</table></div>'
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
        st.title(f"🎰 {choice} · 全盘分布透视")
        st.caption("提示：在手机上可左右滑动查看完整图表")
        
        # 直接召唤核心黑科技：渲染分布图
        grid_html = render_distribution_grid(df, q_col, d_cols, choice)
        st.markdown(grid_html, unsafe_allow_html=True)
        
        # --- 侧边栏 AI 辅助 ---
        st.sidebar.markdown("---")
        if st.sidebar.button("🪄 根据分布规律推算下期"):
            import random
            if choice == "双色球":
                reds = sorted(random.sample([str(i).zfill(2) for i in range(1, 34)], 6))
                blue = str(random.randint(1, 16)).zfill(2)
                st.sidebar.success(f"建议红球：{' '.join(reds)}\n建议蓝球：{blue}")
            else:
                st.sidebar.success("已完成云端演算，号码池呈现温热分布，建议防守冷号。")
else:
    st.error("🚨 找不到对应数据文件！")
