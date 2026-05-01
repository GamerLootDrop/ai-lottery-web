import streamlit as st
import pandas as pd
import os
import time
import requests
import random

# --- 1. 深度定制样式表 ---
st.set_page_config(page_title="AI 大数据决策终端", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 1.5rem !important; max-width: 900px; }
    .hist-table { width: 100%; border-collapse: collapse; text-align: center; background: #fff; border-radius: 8px; overflow: hidden; margin-bottom: 1rem; }
    .hist-table th { background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #eaeaea; color: #666; font-weight: bold; }
    .hist-table td { padding: 12px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 15px; }
    .ball { display: inline-block; width: 30px; height: 30px; line-height: 30px; border-radius: 50%; color: white; font-weight: bold; margin: 0 4px; font-size: 14px; text-align: center; }
    .bg-red { background-color: #f14545; }
    .bg-blue { background-color: #3b71f7; }
    .bg-yellow { background-color: #f9bf15; color: #333 !important; }
    .bg-purple { background-color: #9c27b0; }
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 数据载入引擎 ---
@st.cache_data
def load_full_data(file_path, choice):
    try:
        df = pd.read_excel(file_path) if file_path.endswith('.xls') else pd.read_csv(file_path)
        if "Unnamed" in str(df.columns[0]):
            df = pd.read_excel(file_path, skiprows=1) if file_path.endswith('.xls') else pd.read_csv(file_path, skiprows=1)
        df.columns = [str(c).strip() for c in df.columns]
        q_col = next((c for c in df.columns if '期' in c or 'NO' in c), df.columns[0])
        df[q_col] = pd.to_numeric(df[q_col], errors='coerce')
        df = df.dropna(subset=[q_col])
        
        lottery_params = {"双色球": (7, True), "大乐透": (7, True), "福彩3D": (3, False), "快乐8": (20, True), "排列3": (3, False), "排列5": (5, False), "七星彩": (7, False)}
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
        for col in new_cols: clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce').fillna(0).astype(int)
        return clean_df.sort_values(q_col, ascending=False), q_col, new_cols[1:], needs_zero, file_path
    except: return None, None, None, None, None

# --- 3. 重构：真·全网数据抓取引擎 ---
def fetch_real_data(choice, latest_issue, d_cols):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    new_rows = []
    
    try:
        # 福彩系列 (双色球, 3D, 快乐8)
        if choice in ["双色球", "福彩3D", "快乐8"]:
            code_map = {"双色球": "ssq", "福彩3D": "3d", "快乐8": "kl8"}
            url = f"http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name={code_map[choice]}&issueCount=10"
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()
            for item in data.get('result', []):
                issue = int(item['code'])
                if issue <= latest_issue: continue
                # 解析红蓝球
                reds = [int(x) for x in item['red'].split(',')]
                blues = [int(x) for x in item['blue'].split(',')] if item.get('blue') else []
                all_balls = reds + blues
                if len(all_balls) >= len(d_cols):
                    row = {d_cols[i]: all_balls[i] for i in range(len(d_cols))}
                    new_rows.append((issue, row))

        # 体彩系列 (大乐透, 排列3, 排列5, 七星彩)
        else:
            game_map = {"大乐透": "85", "排列3": "35", "排列5": "35", "七星彩": "04"}
            url = f"https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry?gameNo={game_map[choice]}&provinceId=0&pageSize=10&isVerify=1&pageNo=1"
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()
            for item in data.get('value', {}).get('list', []):
                issue = int(item['lotteryDrawNum'])
                if issue <= latest_issue: continue
                # 解析号码字符串 "01 02 03 04 05 06 07"
                all_balls = [int(x) for x in item['lotteryDrawResult'].split(' ')]
                if choice == "排列3": all_balls = all_balls[:3]
                if len(all_balls) >= len(d_cols):
                    row = {d_cols[i]: all_balls[i] for i in range(len(d_cols))}
                    new_rows.append((issue, row))
    except Exception as e:
        st.error(f"🌐 官网连接异常: {e}")
    return new_rows

# --- 4. 同步执行逻辑 ---
def execute_sync(df, q_col, d_cols, choice, file_path):
    latest_local = int(df[q_col].max())
    with st.status(f"正在从国家官网核对【{choice}】最新开奖...", expanded=True) as status:
        real_data = fetch_real_data(choice, latest_local, d_cols)
        if not real_data:
            status.update(label="✅ 已是最新：本地数据已与官网实时同步。", state="complete")
            return
        
        new_df_rows = []
        for iss, vals in real_data:
            r = {q_col: iss}; r.update(vals)
            new_df_rows.append(r)
        
        new_data_df = pd.DataFrame(new_df_rows)
        # 真正合并数据并彻底去重、排序
        final_df = pd.concat([new_data_df, df], ignore_index=True)
        final_df = final_df.drop_duplicates(subset=[q_col]).sort_values(q_col, ascending=False)
        
        save_path = file_path if '_synced' in file_path else file_path.replace('.xls', '_synced.csv').replace('.csv', '_synced.csv')
        final_df.to_csv(save_path, index=False, encoding='utf-8-sig')
        status.update(label=f"🔥 同步成功！已补全 {len(new_data_df)} 期真实开奖。", state="complete")
        time.sleep(1)
        st.cache_data.clear()
        st.rerun()

# --- 5. 主界面 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 AI 大数据决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

file_keyword = LOTTERY_FILES[choice]
all_match = [f for f in os.listdir(".") if file_keyword in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))]
target_file = None
if all_match:
    synced = [f for f in all_match if '_synced' in f]
    target_file = synced[0] if synced else all_match[0]

if target_file:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target_file, choice)
    if df is not None:
        st.sidebar.subheader("🌐 数据库状态")
        st.sidebar.info(f"最新期号: {int(df[q_col].max())}")
        if st.sidebar.button("🔄 联网同步国家官网开奖", use_container_width=True):
            execute_sync(df, q_col, d_cols, choice, actual_path)

        # 走势及展示略... (保持之前的逻辑)
        st.title(f"🎰 {choice} · 智算中心")
        tab1, tab2 = st.tabs(["📜 历史大数据", "🤖 AI 五维演算"])
        with tab1:
            html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(30).iterrows():
                balls_html = ""
                for i, col in enumerate(d_cols):
                    val = row[col]
                    num_str = f"{val:02d}" if needs_zero else str(val)
                    c = "bg-red"
                    if choice == "双色球": c = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": c = "bg-yellow" if i >= 5 else "bg-blue"
                    balls_html += f"<span class='ball {c}'>{num_str}</span>"
                html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{balls_html}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)
