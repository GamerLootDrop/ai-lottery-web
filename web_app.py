import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="AI 智算博弈中心", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 1rem !important; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #ff4b4b; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- 1. 数据清洗引擎 ---
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
                clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce').fillna(-1).astype(int)
        
        clean_df = clean_df.dropna(subset=['期号']).sort_values('期号', ascending=False)
        return clean_df, "期号", [rename_dict[c] for c in raw_ball_cols]
    except Exception as e:
        return None, None, None

# --- 2. 完美复刻：红蓝双区全盘分布图 ---
def render_professional_grid(df, q_col, d_cols, choice):
    # 动态设定彩种范围
    if choice == "双色球": red_max, blue_max, start_num = 33, 16, 1
    elif choice == "大乐透": red_max, blue_max, start_num = 35, 12, 1
    elif choice == "快乐8": red_max, blue_max, start_num = 80, 0, 1
    else: red_max, blue_max, start_num = 9, 0, 0 # 3D, 排列等

    html = '<div style="width: 100%; overflow-x: auto; border: 1px solid #e0e0e0; border-radius: 8px;">'
    html += '<table style="border-collapse: collapse; text-align: center; font-size: 13px; font-family: sans-serif; white-space: nowrap; width: 100%; background-color: #ffffff;">'
    
    # === 表头部分 ===
    html += '<tr><th style="border: 1px solid #ccc; padding: 8px; position: sticky; left: 0; background: #f8f9fa; z-index: 2; color: #333;">期号</th>'
    
    # 渲染红球区表头
    for i in range(start_num, red_max + 1):
        num_str = f"{i:02d}" if start_num == 1 else str(i)
        html += f'<th style="border: 1px solid #e8e8e8; padding: 6px; background: #fff5f5; color: #d93025; min-width: 28px;">{num_str}</th>'
    
    # 渲染蓝球区表头 (如果有)
    for i in range(1, blue_max + 1):
        html += f'<th style="border: 1px solid #e8e8e8; padding: 6px; background: #f0f4ff; color: #1a73e8; min-width: 28px;">{i:02d}</th>'
    html += '</tr>'

    # === 数据渲染部分 ===
    for idx, row in df.head(50).iterrows():
        period = row[q_col]
        red_drawn, blue_drawn = set(), set()
        
        # 分离红蓝球
        for c in d_cols:
            val = int(row[c])
            if val == -1: continue
            if "蓝" in c: blue_drawn.add(val)
            else: red_drawn.add(val)

        # 锁定左侧期号
        html += f'<tr><td style="border: 1px solid #ccc; padding: 8px; position: sticky; left: 0; background: #f8f9fa; z-index: 1; font-weight: bold; color: #444;">{period}</td>'

        # 渲染红球区格子
        for i in range(start_num, red_max + 1):
            num_str = f"{i:02d}" if start_num == 1 else str(i)
            if i in red_drawn:
                # 命中！显示醒目红底圆球
                html += f'<td style="border: 1px solid #eee; padding: 2px;"><div style="display:inline-block; width:22px; height:22px; line-height:22px; border-radius:50%; background:#ea4335; color:white; font-weight:bold;">{num_str}</div></td>'
            else:
                # 没命中，极淡灰色（不会干扰视线）
                html += f'<td style="border: 1px solid #eee; padding: 2px; color: #e0e0e0;">{num_str}</td>'

        # 渲染蓝球区格子
        for i in range(1, blue_max + 1):
            if i in blue_drawn:
                # 命中！显示醒目蓝底圆球
                html += f'<td style="border: 1px solid #eee; padding: 2px; background: #f8faff;"><div style="display:inline-block; width:22px; height:22px; line-height:22px; border-radius:50%; background:#4285f4; color:white; font-weight:bold;">{i:02d}</div></td>'
            else:
                html += f'<td style="border: 1px solid #eee; padding: 2px; background: #f8faff; color: #d0d8f0;">{i:02d}</td>'
                
        html += '</tr>'

    html += '</table></div>'
    return html

# --- 3. 界面组装 ---
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
        st.title(f"🎰 {choice} · 专业红蓝双区走势")
        st.caption("👈 手机用户可左右滑动查看完整区域")
        
        # 召唤专业渲染引擎
        st.markdown(render_professional_grid(df, q_col, d_cols, choice), unsafe_allow_html=True)
        
        # 明细备查模块
        with st.expander("点击查看纯文字原始明细表"):
            st.dataframe(df.head(50), use_container_width=True)

else:
    st.error("🚨 找不到对应数据文件，请检查仓库！")
