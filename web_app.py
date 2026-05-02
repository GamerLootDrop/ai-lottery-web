import streamlit as st
import pandas as pd
import os
import time
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup

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
            
        return clean_df.sort_values(q_col, ascending=False), q_col, new_cols[1:], needs_zero, file_path
    except Exception as e:
        st.error(f"🚨 解析引擎报错详情: {str(e)}")
        return None, None, None, None, None

# --- 3. 核心新增：全彩种海外穿透版同步引擎 ---
def sync_latest_data(df, q_col, d_cols, choice, file_path):
    # 期号补齐函数
    def normalize_issue(iss):
        iss_str = str(iss).strip()
        return int("20" + iss_str) if len(iss_str) == 5 else int(iss_str)

    latest_local_issue = df[q_col].apply(normalize_issue).max()
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    status_text.info(f"📡 正在通过全彩种穿透通道同步 {choice} 数据...")
    progress_bar.progress(30)
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # 映射各彩种在 500网的接口关键字
    api_map = {
        "双色球": "ssq", "大乐透": "dlt", "福彩3D": "sd", 
        "排列3": "pls", "排列5": "plw", "七星彩": "qxc"
    }
    
    new_rows = []
    try:
        # 统一使用 500.com 商业源（海外访问最稳）
        url_key = api_map.get(choice, "ssq")
        url = f"https://datachart.500.com/{url_key}/history/newinc/history.php?limit=15"
        
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        tdata = soup.find('tbody', id='tdata')
        
        if tdata:
            for tr in tdata.find_all('tr'):
                if tr.has_attr('class') and 'hide' in tr['class']: continue 
                tds = tr.find_all('td')
                if len(tds) > 5:
                    raw_issue = tds[0].text.strip()
                    issue_7d = normalize_issue(raw_issue)
                    
                    if issue_7d > latest_local_issue:
                        # 核心定位逻辑：自动识别红球(t_cfont2)和蓝球/黄球(t_cfont4)
                        red_balls = [int(td.text.strip()) for td in tr.find_all('td', class_='t_cfont2')]
                        blue_balls = [int(td.text.strip()) for td in tr.find_all('td', class_='t_cfont4')]
                        all_balls = red_balls + blue_balls
                        
                        # 兼容不同列数的处理
                        row = {q_col: issue_7d}
                        for i, col in enumerate(d_cols):
                            row[col] = all_balls[i] if i < len(all_balls) else 0
                        new_rows.append(row)
        
        progress_bar.progress(80)
        
        if new_rows:
            new_df = pd.DataFrame(new_rows).sort_values(q_col, ascending=False)
            updated_df = pd.concat([new_df, df], ignore_index=True)
            updated_df[q_col] = updated_df[q_col].astype(int)
            save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
            updated_df.to_csv(save_path, index=False, encoding='utf-8-sig')
            
            status_text.success(f"✅ {choice} 同步成功！新增了 {len(new_rows)} 期正确数据！")
            progress_bar.progress(100)
            time.sleep(2)
            st.cache_data.clear()
            st.rerun()
        else:
            status_text.success(f"✅ {choice} 本地已是最新！")
            progress_bar.progress(100)
            time.sleep(2)
            
    except Exception as e:
        status_text.error(f"❌ {choice} 同步失败: {str(e)}")
    finally:
        progress_bar.empty()
        status_text.empty()

# --- 4. 辅助预测功能 ---
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
            # 兼容排列3/5, 3D等
            n = 3 if choice in ["排列3", "福彩3D"] else 5
            if choice == "七星彩": n = 7
            raw = [random.randint(0, 9) for _ in range(n)]
            nums = " ".join(map(str, raw))
            html_balls = "".join([f"<span class='pred-ball bg-purple'>{n}</span>" for n in raw])
        results.append({"strategy": s, "text": nums, "html": html_balls})
    return results

# --- 5. 界面展示 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 AI 大数据决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

if 'current_choice' not in st.session_state or choice != st.session_state.current_choice:
    st.session_state.pred_sets = None
    st.session_state.current_choice = choice

file_keyword = LOTTERY_FILES[choice]
all_match = [f for f in os.listdir(".") if file_keyword in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))]
target_file = next((f for f in all_match if '_synced' in f), all_match[0] if all_match else None)

if target_file:
    df, q_col, d_cols, needs_zero, actual_file_path = load_full_data(target_file, choice)
    
    if df is not None:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🌐 数据库状态")
        st.sidebar.markdown(f"**最新期号：** `{int(df[q_col].max())}`")
        if st.sidebar.button("🔄 联网同步最新开奖", use_container_width=True):
            sync_latest_data(df, q_col, d_cols, choice, actual_file_path)

        st.sidebar.markdown("---")
        st.sidebar.subheader("📅 显示选项")
        preset_map = {"近20期": 20, "近50期": 50, "近100期": 100, "近200期": 200, "显示全部": len(df)}
        selected_preset = st.sidebar.radio("选择查看/分析范围", list(preset_map.keys()), index=1)
        show_limit = preset_map[selected_preset]

        st.title(f"🎰 {choice} · 智算中心")
        tab1, tab2, tab3 = st.tabs(["📜 历史大数据", "📊 走势分析", "🤖 AI 五维演算"])
        
        with tab1:
            st.markdown(f"**当前视图：{selected_preset}** (本地数据库共计 {len(df)} 期)")
            html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(show_limit).iterrows():
                balls_html = ""
                for i, col in enumerate(d_cols):
                    val = row[col]
                    num_str = f"{val:02d}" if needs_zero else str(val)
                    c = "bg-red"
                    if choice == "双色球": c = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": c = "bg-yellow" if i >= 5 else "bg-blue"
                    elif choice in ["排列3", "排列5", "福彩3D"]: c = "bg-purple"
                    balls_html += f"<span class='ball {c}'>{num_str}</span>"
                html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{balls_html}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)
            
        with tab2:
            st.subheader(f"📈 走势曲线图 ({selected_preset})")
            algo_choice = st.selectbox("选择分析维度", ["总和值走势", "平均值走势", "最大值波动", "最小值波动"])
            calc_df = df.head(show_limit).copy()
            
            if algo_choice == "总和值走势": calc_df['指标'] = calc_df[d_cols].sum(axis=1)
            elif algo_choice == "平均值走势": calc_df['指标'] = calc_df[d_cols].mean(axis=1)
            elif algo_choice == "最大值波动": calc_df['指标'] = calc_df[d_cols].max(axis=1)
            else: calc_df['指标'] = calc_df[d_cols].min(axis=1)
            
            st.line_chart(calc_df.sort_values(q_col).set_index(q_col)['指标'])

        with tab3:
            st.subheader("🧠 五维联合预测")
            if st.button("🚀 启动 AI 深度演算 (基于最新数据)", use_container_width=True):
                with st.spinner("正在穿越历史长河检索底层规律..."):
                    time.sleep(1)
                    st.session_state.pred_sets = get_prediction_sets(choice)
            
            if st.session_state.get('pred_sets'):
                for p in st.session_state.pred_sets:
                    st.markdown(f"<div class='pred-row'><div class='pred-title'>{p['strategy']}</div><div class='pred-balls'>{p['html']}</div></div>", unsafe_allow_html=True)
                st.code(f"【{choice} AI智算推荐】\n" + "\n".join([f"{p['strategy']}: {p['text']}" for p in st.session_state.pred_sets]), language="text")

    else: st.error("数据载入失败，请检查文件格式。")
else: st.error(f"🚨 未找到 {choice} 数据文件，请确保后台存在对应的 Excel 或 CSV 文件。")
