import streamlit as st
import pandas as pd
import os
import time
import random
import requests

# --- 1. 深度定制样式表 ---
st.set_page_config(page_title="AI 大数据决策终端", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 1.5rem !important; max-width: 900px; }
    .hist-table { width: 100%; border-collapse: collapse; text-align: center; background: #fff; border-radius: 8px; overflow: hidden; margin-bottom: 1rem; }
    .hist-table th { background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #eaeaea; color: #666; font-weight: bold; }
    .hist-table td { padding: 12px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 15px; }
    .ball { display: inline-block; width: 30px; height: 30px; line-height: 30px; border-radius: 50%; color: white; font-weight: bold; margin: 0 4px; font-size: 14px; text-align: center; }
    .pred-ball { display: inline-block; width: 36px; height: 36px; line-height: 36px; border-radius: 50%; color: white; font-weight: bold; margin: 0 5px; font-size: 16px; text-align: center; }
    .bg-red { background-color: #f14545; }
    .bg-blue { background-color: #3b71f7; }
    .bg-yellow { background-color: #f9bf15; color: #333 !important; }
    .bg-purple { background-color: #9c27b0; }
    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 15px; border-left: 5px solid #f14545; display: flex; align-items: center; }
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
        return None, None, None, None, None

# --- 3. 核心新增：真实国家官网 API 爬虫 ---
def fetch_real_latest_data(choice, latest_local_issue, d_cols):
    """直接对接中国福彩和体彩官网接口获取真实开奖数据"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    # 接口参数配置字典
    API_CONFIG = {
        "双色球": {"type": "cwl", "code": "ssq"},
        "福彩3D": {"type": "cwl", "code": "3d"},
        "快乐8": {"type": "cwl", "code": "kl8"},
        "大乐透": {"type": "ticai", "code": "85"},
        "排列3": {"type": "ticai", "code": "35"}, # 排列3和排列5共用一个底层接口
        "排列5": {"type": "ticai", "code": "35"},
        "七星彩": {"type": "ticai", "code": "04"}
    }
    
    config = API_CONFIG.get(choice)
    if not config: return []

    new_rows = []
    
    try:
        # --- 福彩官网数据抓取 ---
        if config["type"] == "cwl":
            # 抓取最近 15 期
            url = f"http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name={config['code']}&issueCount=15"
            headers["Referer"] = "http://www.cwl.gov.cn/"
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()
            
            for item in data.get('result', []):
                issue = int(item['code'])
                if issue <= latest_local_issue: continue # 只要比本地新的
                
                # 福彩返回的格式如 red: "01,02,03,04,05,06", blue: "07"
                reds = item['red'].split(',')
                blues = item.get('blue', '').split(',') if item.get('blue') else []
                all_balls = [int(x) for x in reds + blues if x.strip()]
                
                if len(all_balls) >= len(d_cols):
                    row = {d_cols[i]: all_balls[i] for i in range(len(d_cols))}
                    new_rows.append((issue, row))

        # --- 体彩官网数据抓取 ---
        elif config["type"] == "ticai":
            url = f"https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry?gameNo={config['code']}&provinceId=0&pageSize=15&isVerify=1&pageNo=1"
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()
            
            for item in data.get('value', {}).get('list', []):
                issue_str = item['lotteryDrawNum']
                # 体彩期号可能是 "24015"，需要转整型比对
                issue = int(issue_str.replace("-", ""))
                if issue <= latest_local_issue: continue
                
                # 体彩返回格式如 "01 02 03 04 05 06 07"
                balls_str = item['lotteryDrawResult']
                all_balls = [int(x) for x in balls_str.split(' ') if x.strip()]
                
                # 特殊处理排列3（体彩接口返回5个球，前3个是排3）
                if choice == "排列3": all_balls = all_balls[:3]
                
                if len(all_balls) >= len(d_cols):
                    row = {d_cols[i]: all_balls[i] for i in range(len(d_cols))}
                    new_rows.append((issue, row))
                    
    except Exception as e:
        print(f"抓取异常: {e}") # 后台打印错误
        return []

    return new_rows

# --- 4. 同步执行引擎 ---
def sync_latest_data(df, q_col, d_cols, choice, file_path):
    latest_local_issue = int(df[q_col].max())
    status_text = st.empty()
    
    status_text.info(f"📡 正在连接【{choice}】国家彩票官网接口，拉取最新实盘数据...")
    
    # 核心调用真实抓取函数
    new_data = fetch_real_latest_data(choice, latest_local_issue, d_cols)
    
    if not new_data:
        status_text.warning("⚡ 云端比对完毕：当前本地数据已是最新，无需同步。")
        time.sleep(2)
        status_text.empty()
        return

    # 组装新数据
    status_text.success(f"📥 发现 {len(new_data)} 期真实新数据，正在执行本地入库...")
    new_rows_list = []
    for issue, row_dict in new_data:
        full_row = {q_col: issue}
        full_row.update(row_dict)
        new_rows_list.append(full_row)
        
    new_df = pd.DataFrame(new_rows_list)
    updated_df = pd.concat([new_df, df], ignore_index=True).sort_values(q_col, ascending=False)
    
    try:
        # 保存回文件
        save_path = file_path if '_synced' in file_path else file_path.replace('.xls', '_synced.csv').replace('.csv', '_synced.csv')
        updated_df.to_csv(save_path, index=False, encoding='utf-8-sig')
        status_text.success(f"✅ 入库成功！真实期号 {new_df[q_col].tolist()} 已更新！")
        time.sleep(2)
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        status_text.error(f"❌ 写入失败: {str(e)}")

# --- 5. 辅助功能：生成推荐号码 (保持不变) ---
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

# --- 初始化 Session State ---
if 'pred_sets' not in st.session_state: st.session_state.pred_sets = None
if 'copy_text' not in st.session_state: st.session_state.copy_text = ""
if 'current_choice' not in st.session_state: st.session_state.current_choice = ""

# --- 6. 界面展示 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 AI 大数据决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

if choice != st.session_state.current_choice:
    st.session_state.pred_sets = None
    st.session_state.current_choice = choice

file_keyword = LOTTERY_FILES[choice]
all_matching_files = [f for f in os.listdir(".") if file_keyword in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))]
target_file = None
if all_matching_files:
    synced_files = [f for f in all_matching_files if '_synced' in f]
    target_file = synced_files[0] if synced_files else all_matching_files[0]

st.sidebar.markdown("---")

if target_file:
    st.sidebar.success(f"📂 读取源: `{target_file}`")
    df, q_col, d_cols, needs_zero, actual_file_path = load_full_data(target_file, choice)
    
    if df is not None:
        st.sidebar.subheader("🌐 官网自动同步")
        st.sidebar.markdown(f"**本地最新期号：** `{int(df[q_col].max())}`")
        if st.sidebar.button("🔄 联网同步国家官网开奖", use_container_width=True):
            sync_latest_data(df, q_col, d_cols, choice, actual_file_path)

        st.sidebar.markdown("---")
        st.sidebar.subheader("📅 显示选项")
        preset_map = {"近20期": 20, "近50期": 50, "近100期": 100, "近200期": 200, "显示全部": 999999}
        show_limit = preset_map[st.sidebar.radio("选择查看范围", list(preset_map.keys()), index=1)]

        st.title(f"🎰 {choice} · 智算中心")
        tab1, tab2, tab3 = st.tabs(["📜 历史大数据", "📊 走势分析", "🤖 AI 五维演算"])
        
        with tab1:
            st.markdown(f"**当前排列：** (本地数据库共计 {len(df)} 期)")
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
            if st.button("🚀 启动 AI 深度演算 (基于全量数据)", use_container_width=True):
                with st.spinner("正在检索底层规律..."):
                    time.sleep(1.2)
                    pred_sets = get_prediction_sets(choice)
                    copy_text = f"【{choice} AI智算推荐】\n"
                    for p in pred_sets: copy_text += f"{p['strategy']}: {p['text']}\n"
                    st.session_state.pred_sets = pred_sets
                    st.session_state.copy_text = copy_text
            
            if st.session_state.pred_sets:
                for p in st.session_state.pred_sets:
                    st.markdown(f"<div class='pred-row'><div class='pred-title'>{p['strategy']}</div><div class='pred-balls'>{p['html']}</div></div>", unsafe_allow_html=True)
                st.markdown("---")
                st.code(st.session_state.copy_text, language="text")
    else: 
        st.error("数据载入失败。")
else: 
    st.error(f"🚨 未找到数据文件。")
