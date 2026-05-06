import streamlit as st
import pandas as pd
import os
import time
import random
import requests
from bs4 import BeautifulSoup
import re  
from collections import Counter
from datetime import datetime, timedelta
import numpy as np 

# =========================================================
# 💰💰💰 老板专属配置区 (只需修改这里，其他地方不用动) 💰💰💰
# =========================================================
MY_WECHAT_ID = "252766667"           # 已帮您填好微信号
VIP_PASSWORD = "888"                 # 付费解锁口令
# =========================================================

# --- 1. 深度定制样式表 ---
st.set_page_config(page_title="AI 大数据决策终端", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 2.5rem 1.5rem !important; max-width: 900px; }
    .hist-table { width: 100%; border-collapse: collapse; text-align: center; background: #fff; border-radius: 8px; overflow: hidden; margin-bottom: 1rem; }
    .hist-table th { background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #eaeaea; color: #666; font-weight: bold; }
    .hist-table td { padding: 12px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 15px; }
    
    .ball { display: inline-block; width: 28px; height: 28px; line-height: 28px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 3px; font-size: 13px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .bg-red { background-color: #f14545; }
    .bg-blue { background-color: #3b71f7; }
    .bg-yellow { background-color: #f9bf15; color: #333 !important; }
    .bg-purple { background-color: #9c27b0; }
    .bg-lotus { background-color: #cba09e; } 
    .bg-lightblue { background-color: #5bc0de; } 
    
    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 5px; border-left: 5px solid #f14545; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; position: relative; }
    .pred-title { width: 150px; font-weight: bold; color: #444; font-size: 15px; }
    .pred-balls { flex-grow: 1; display: flex; flex-wrap: wrap; max-width: 400px;} 
    .pred-ball { display: inline-block; width: 34px; height: 34px; line-height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 4px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.15); }
    
    .vip-locked { filter: blur(6px); user-select: none; pointer-events: none; }
    .lock-overlay { position: absolute; right: 20px; top: 50%; transform: translateY(-50%); background: rgba(255,255,255,0.95); padding: 6px 15px; border: 2px dashed #ff4b4b; border-radius: 5px; color: #ff4b4b; font-size: 14px; font-weight: bold; z-index: 10; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    
    .timer-bar { background: linear-gradient(90deg, #1d2b64, #f8cdda); color: white; padding: 10px; text-align: center; border-radius: 5px; font-weight: bold; margin-bottom: 15px; }
    .wechat-box { background: #f0f2f6; border-radius: 10px; padding: 15px; border: 1px solid #dcdfe6; text-align: center; margin-bottom: 10px;}
    .download-lock { background: #fff5f5; border: 1px dashed #feb2b2; padding: 15px; text-align: center; border-radius: 8px; margin-bottom: 15px; }
    
    .marquee-wrapper { background: linear-gradient(to right, #fff3cd, #fff8e1); padding: 10px 15px; border-radius: 8px; border-left: 4px solid #f9bf15; margin-bottom: 20px; overflow: hidden; display: flex; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .marquee-icon { font-size: 18px; margin-right: 10px; min-width: 25px; }
    .marquee-content { white-space: nowrap; animation: marquee 30s linear infinite; color: #856404; font-weight: bold; font-size: 14px; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-150%); } }
    
    .comment-box { background: #fff; border: 1px solid #eaeaea; border-radius: 8px; padding: 15px; margin-bottom: 10px; }
    .comment-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
    .comment-user { font-weight: bold; color: #1f77b4; font-size: 14px; }
    .comment-time { color: #999; font-size: 12px; }
    .comment-body { color: #444; font-size: 14px; line-height: 1.5; }
    .legal-footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #eaeaea; text-align: center; color: #999; font-size: 12px; line-height: 1.8; }
    </style>
""", unsafe_allow_html=True)

# --- 工具函数 ---
def get_countdown():
    now = datetime.now()
    target = now.replace(hour=21, minute=30, second=0)
    if now > target: target += timedelta(days=1)
    diff = target - now
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}时{minutes:02d}分{seconds:02d}秒"

def get_fake_broadcasts():
    cities = ["广东", "浙江", "江苏", "山东", "河南", "四川", "北京", "上海"]
    algos = ["极热寻踪", "绝地反弹", "黄金均衡", "蒙特卡洛", "深度拟合"]
    broadcast_texts = []
    for _ in range(5):
        city = random.choice(cities)
        phone = f"1{random.randint(3,9)}{random.randint(0,9)}****{random.randint(1000,9999)}"
        algo = random.choice(algos)
        mins = random.randint(1, 59)
        broadcast_texts.append(f"【最新喜报】{city}用户 {phone} {mins}分钟前 成功解锁「{algo}」策略！")
    return "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🔥&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join(broadcast_texts)

# --- 核心：数据提取 ---
@st.cache_data
def load_full_data(file_path, choice):
    try:
        raw_df = pd.read_excel(file_path) if file_path.endswith('.xls') else pd.read_csv(file_path)
        raw_df.columns = [str(c).strip() for c in raw_df.columns]
        q_col = next((c for c in raw_df.columns if '期' in c or 'NO' in c.upper()), raw_df.columns[0])
        raw_df[q_col] = pd.to_numeric(raw_df[q_col], errors='coerce')
        raw_df = raw_df.dropna(subset=[q_col])
        
        limits = {"双色球": 7, "大乐透": 7, "福彩3D": 3, "排列3": 3, "排列5": 5, "七星彩": 7, "快乐8": 20}
        max_balls = limits.get(choice, 7)
        
        q_idx = list(raw_df.columns).index(q_col)
        ball_cols = []
        for i in range(q_idx + 1, len(raw_df.columns)):
            col = raw_df.columns[i]
            nums = pd.to_numeric(raw_df[col], errors='coerce').dropna()
            if not nums.empty and (nums <= 81).all():
                ball_cols.append(col)
            if len(ball_cols) == max_balls: break
            
        clean_df = raw_df[[q_col] + ball_cols].copy()
        new_names = ['期号'] + [f"b_{i+1}" for i in range(len(ball_cols))]
        clean_df.columns = new_names
        for c in new_names: clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0).astype(int)
        
        needs_zero = True if choice in ["双色球", "大乐透", "快乐8"] else False
        return clean_df.sort_values('期号', ascending=False), '期号', new_names[1:], needs_zero, file_path
    except: return None, None, None, None, None

# 🌟🌟🌟 【AI 算法引擎：基于真实 NumPy 数学推演】 🌟🌟🌟
def get_real_prediction(df_view, d_cols, choice):
    sets = []
    all_nums = []
    for col in d_cols:
        all_nums.extend(df_view[col].dropna().astype(int).tolist())
    freq_dict = Counter(all_nums)
    sorted_by_freq = [item[0] for item in freq_dict.most_common()]
    
    rules = {
        "双色球": (list(range(1, 34)), 6, list(range(1, 17)), 1),
        "大乐透": (list(range(1, 36)), 5, list(range(1, 13)), 2),
        "七星彩": (list(range(0, 10)), 6, list(range(0, 15)), 1),
        "快乐8": (list(range(1, 81)), 20, [], 0),
        "福彩3D": (list(range(0, 10)), 3, [], 0),
        "排列3": (list(range(0, 10)), 3, [], 0),
        "排列5": (list(range(0, 10)), 5, [], 0)
    }
    
    pool_r, count_r, pool_b, count_b = rules.get(choice, rules["双色球"])
    for n in pool_r:
        if n not in freq_dict: freq_dict[n] = 0
    
    hot_list_r = [n for n in sorted_by_freq if n in pool_r]
    hot_list_r.extend([n for n in pool_r if n not in hot_list_r]) 
    cold_list_r = hot_list_r[::-1] 
    
    algos = [
        {"name": "🔥 极热寻踪", "type": "hot", "vip": False},
        {"name": "🧊 绝地反弹", "type": "cold", "vip": False},
        {"name": "⚖️ 黄金均衡", "type": "mix", "vip": False},
        {"name": "🎲 蒙特卡洛引擎", "type": "monte", "vip": True},
        {"name": "🧠 深度拟合网络", "type": "fit", "vip": True}
    ]
    
    for algo in algos:
        r_res, b_res = [], []
        if algo['type'] == 'hot':
            r_res = sorted(hot_list_r[:count_r])
            if count_b > 0: b_res = sorted(random.sample(pool_b, count_b))
        elif algo['type'] == 'cold':
            r_res = sorted(cold_list_r[:count_r])
            if count_b > 0: b_res = sorted(random.sample(pool_b, count_b))
        elif algo['type'] == 'mix':
            half = count_r // 2
            r_res = sorted(hot_list_r[:half] + cold_list_r[:count_r - half])
            if count_b > 0: b_res = sorted(random.sample(pool_b, count_b))
        elif algo['type'] == 'monte':
            weights = [freq_dict[n] + 1 for n in pool_r]
            probs = [w / sum(weights) for w in weights]
            sampled = np.random.choice(pool_r, size=count_r, replace=False, p=probs)
            r_res = sorted(sampled.tolist())
            if count_b > 0: b_res = sorted(random.sample(pool_b, count_b))
        elif algo['type'] == 'fit':
            if not df_view.empty:
                last_draw = df_view.iloc[0][d_cols[:count_r]].values
                avg_val = np.mean(all_nums) if all_nums else 0
                r_res_temp = []
                for val in last_draw:
                    fit_val = int((val + avg_val) / 2)
                    attempts = 0
                    while (fit_val not in pool_r or fit_val in r_res_temp) and attempts < 100:
                        fit_val = fit_val + 1 if fit_val < max(pool_r) else min(pool_r)
                        attempts += 1
                    r_res_temp.append(fit_val)
                r_res = sorted(r_res_temp[:count_r])
            else: r_res = sorted(hot_list_r[:count_r])
            if count_b > 0: b_res = sorted(random.sample(pool_b, count_b))

        algo_name_clean = algo['name'].split(' ', 1)[-1] if ' ' in algo['name'] else algo['name']
        if choice == "双色球": 
            html = "".join([f"<span class='pred-ball bg-red'>{n:02d}</span>" for n in r_res]) + f"<span class='pred-ball bg-blue'>{b_res[0]:02d}</span>"
            text_copy = f"【双色球】{algo_name_clean} 推荐号码: " + " ".join([f"{n:02d}" for n in r_res]) + f" | {b_res[0]:02d}"
        elif choice == "大乐透": 
            html = "".join([f"<span class='pred-ball bg-blue'>{n:02d}</span>" for n in r_res]) + "".join([f"<span class='pred-ball bg-yellow'>{n:02d}</span>" for n in b_res])
            text_copy = f"【大乐透】{algo_name_clean} 推荐号码: " + " ".join([f"{n:02d}" for n in r_res]) + " | " + " ".join([f"{n:02d}" for n in b_res])
        elif choice == "七星彩": 
            html = "".join([f"<span class='pred-ball bg-purple'>{n}</span>" for n in r_res]) + f"<span class='pred-ball bg-yellow'>{b_res[0]}</span>"
            text_copy = f"【七星彩】{algo_name_clean} 推荐号码: " + " ".join([str(n) for n in r_res]) + f" | {b_res[0]}"
        elif choice == "快乐8": 
            html = "".join([f"<span class='pred-ball bg-red'>{n:02d}</span>" for n in r_res])
            text_copy = f"【快乐8】{algo_name_clean} 推荐号码: " + " ".join([f"{n:02d}" for n in r_res])
        elif choice == "福彩3D": 
            html = "".join([f"<span class='pred-ball bg-lightblue'>{n}</span>" for n in r_res])
            text_copy = f"【{choice}】{algo_name_clean} 推荐号码: " + " ".join([str(n) for n in r_res])
        else: 
            html = "".join([f"<span class='pred-ball bg-lotus'>{n}</span>" for n in r_res])
            text_copy = f"【{choice}】{algo_name_clean} 推荐号码: " + " ".join([str(n) for n in r_res])
        sets.append({"name": algo['name'], "html": html, "text": text_copy, "is_vip": algo['vip']})
    return sets

# --- 核心：联网数据防封缓存 ---
@st.cache_data(ttl=3600) # 核心：每小时只去抓一次，保护服务器，提高速度
def fetch_from_web(game_code, choice, d_cols_len):
    urls = [f"https://datachart.500.com/{game_code}/history/newinc/history.php?limit=50", f"https://datachart.500.com/{game_code}/history/inc/history.php?limit=50"]
    headers = {"User-Agent": "Mozilla/5.0"}
    web_rows = []
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            tdata = soup.find('tbody', id='tdata')
            trs = tdata.find_all('tr') if tdata else (soup.find_all('tr', class_=['t_tr1', 't_tr2', 't_tr']) or soup.find_all('tr'))
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) < d_cols_len + 1: continue 
                iss_str = re.sub(r'\D', '', tds[0].get_text(strip=True))
                if len(iss_str) < 3: continue
                issue_val = int("20" + iss_str) if len(iss_str) == 5 else int(iss_str)
                rest_text = "   ".join([td.get_text(separator=" ") for td in tds[1:]])
                if choice in ["福彩3D", "排列3", "排列5"]: balls = [int(n) for n in re.findall(r'\d', rest_text)]
                elif choice == "七星彩":
                    balls = []
                    groups = re.findall(r'\d+', rest_text)
                    for g in groups:
                        if len(g) >= 3: 
                            for char in g: balls.append(int(char))
                        else: balls.append(int(g))
                else: balls = [int(n) for n in re.findall(r'\d+', rest_text)]
                balls = [n for n in balls if 0 <= n <= 81]
                if len(balls) >= d_cols_len:
                    web_rows.append({"issue": issue_val, "balls": balls[:d_cols_len]})
            if web_rows: break
        except: continue
    return web_rows

def sync_latest_data(df, q_col, d_cols, choice, file_path):
    status = st.empty()
    game_codes = {"双色球": "ssq", "大乐透": "dlt", "福彩3D": "sd", "排列3": "pls", "排列5": "plw", "七星彩": "qxc", "快乐8": "kl8"}
    game_code = game_codes.get(choice, "ssq")
    status.info(f"📡 正在联网获取 {choice} 最新开奖...")
    
    web_data = fetch_from_web(game_code, choice, len(d_cols))
    
    if web_data:
        web_rows = []
        for item in web_data:
            row = {q_col: item['issue']}
            for i, col_name in enumerate(d_cols): row[col_name] = item['balls'][i]
            web_rows.append(row)
        
        web_df = pd.DataFrame(web_rows)
        df[q_col] = df[q_col].apply(lambda x: int(float(x)) if len(str(int(float(x))))!=5 else int("20"+str(int(float(x)))))
        updated = pd.concat([web_df, df], ignore_index=True).drop_duplicates(subset=[q_col], keep='first').sort_values(q_col, ascending=False)
        save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
        updated.to_csv(save_path, index=False, encoding='utf-8-sig')
        status.success(f"✅ 同步成功！已更新 {len(web_rows)} 期。")
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()
    else: status.error("❌ 抓取失败，请稍后再试。")

# --- 侧边栏布局 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 商业决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

st.sidebar.markdown(f"""
    <div class="wechat-box">
        <span style="font-size:14px; color:#666;">获取核心【VIP内部口令】</span><br>
        <span style="font-size:12px; color:#999;">(加微信发红包获取)</span><br>
        <b style="color:#ff4b4b; font-size:13px; display:inline-block; margin-top:10px;">👇 点击下方微信号自动复制 👇</b>
    </div>
""", unsafe_allow_html=True)
st.sidebar.code(MY_WECHAT_ID, language="text")

st.sidebar.markdown("---")
view_options = {"近30期": 30, "近50期": 50, "近100期": 100}
view_choice = st.sidebar.radio("选择分析样本", list(view_options.keys()), index=1)

# --- 核心：主界面逻辑 ---
file_kw = LOTTERY_FILES[choice]
all_files = [f for f in os.listdir(".") if file_kw in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))]
target = next((f for f in all_files if '_synced' in f), all_files[0] if all_files else None)

if target:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target, choice)
    if df is not None:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**📊 库中最新：** `{int(df[q_col].max())}` 期")
        if st.sidebar.button("🔄 联网同步最新开奖", use_container_width=True, type="primary"):
            sync_latest_data(df, q_col, d_cols, choice, actual_path)

        st.title(f"🎰 {choice} 数据智算中心")
        st.markdown(f'<div class="timer-bar">⏰ 离今日开奖截止还剩 {get_countdown()} | 核心服务器已就绪</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="marquee-wrapper"><div class="marquee-icon">📢</div><div class="marquee-content">{get_fake_broadcasts()}</div></div>', unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["📜 历史数据", "📈 深度走势", "🤖 AI 演算", "💬 交流大厅"])
        
        with t1:
            st.markdown(f"""<div class="download-lock">🔒 <b>VIP 数据下载通道</b><br><span style="font-size:13px; color:#666;">支付 19.9 元开启全量 Excel 导出权限。微信：{MY_WECHAT_ID}</span></div>""", unsafe_allow_html=True)
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(view_options[view_choice]).iterrows():
                max_w = "280px" if choice == "快乐8" else "100%" 
                balls_html = f"<div style='display:flex; flex-wrap:wrap; justify-content:center; margin: 0 auto; max-width: {max_w};'>"
                for i, col in enumerate(d_cols):
                    val = row[col]
                    txt = f"{val:02d}" if needs_zero else str(val)
                    bg = "bg-red"
                    if choice == "双色球": bg = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": bg = "bg-yellow" if i >= 5 else "bg-blue"
                    elif choice == "七星彩": bg = "bg-yellow" if i == 6 else "bg-purple"
                    elif choice == "福彩3D": bg = "bg-lightblue"
                    elif choice in ["排列3", "排列5"]: bg = "bg-lotus"
                    balls_html += f"<span class='ball {bg}'>{txt}</span>"
                balls_html += "</div>"
                table_html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{balls_html}</td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

        with t2:
            calc_df = df.head(view_options[view_choice]).copy()
            calc_df['和值'] = calc_df[d_cols].sum(axis=1)
            calc_df['跨度'] = calc_df[d_cols].max(axis=1) - calc_df[d_cols].min(axis=1)
            calc_df['奇数个数'] = calc_df[d_cols].apply(lambda row: sum(1 for x in row if x % 2 != 0), axis=1)
            st.markdown("### 📈 近期和值走势")
            st.line_chart(calc_df.set_index('期号')['和值'])
            st.markdown("### 🎢 号码跨度振幅")
            st.area_chart(calc_df.set_index('期号')['跨度'], color="#f14545")

        with t3:
            st.info(f"💡 提示：当前根据「{view_choice}」演算。点击右上角 📋 复制号码。")
            with st.form("ai_form"):
                st.markdown("##### 🔑 VIP 核心算法解锁")
                user_input_pwd = st.text_input("在下方输入口令：", type="password", placeholder="请输入今日口令...")
                submit_btn = st.form_submit_button("🚀 验证并启动 AI 演算", use_container_width=True)

            if submit_btn:
                is_unlocked = (user_input_pwd == VIP_PASSWORD)
                with st.spinner('分析中...'): time.sleep(1)
                predictions = get_real_prediction(df.head(view_options[view_choice]), d_cols, choice)
                for p in predictions:
                    if p['is_vip'] and not is_unlocked:
                        st.markdown(f"<div class='pred-row'><div class='pred-title'>{p['name']}</div><div class='pred-balls vip-locked'>{p['html']}</div><div class='lock-overlay'>🔒 算法锁定</div></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='pred-row'><div class='pred-title'>{p['name']} ✅</div><div class='pred-balls'>{p['html']}</div></div>", unsafe_allow_html=True)
                        st.code(p['text'], language="text")

        with t4:
            if 'comments' not in st.session_state:
                st.session_state.comments = [{"user": "老彩民001", "text": "已加老板微信，口令确实准！", "time": "2分钟前"}]
            for c in st.session_state.comments:
                st.markdown(f'<div class="comment-box"><div class="comment-header"><span class="comment-user">{c["user"]}</span><span>{c["time"]}</span></div><div>{c["text"]}</div></div>', unsafe_allow_html=True)

# --- 🌟 侧边栏底部：全自动逼单广告位 🌟 ---
st.sidebar.markdown("---")
st.sidebar.error("🔥 内部数据福利")
st.sidebar.markdown(f"""
- ✅ **20年** 历史开奖全库
- ✅ **Excel** 格式（支持自主分析）
- ✅ **自动更新** 教程（一键同步）
- 💰 限时特惠：**19.9 元**
""")
st.sidebar.write("👇 加站长微信购买数据包：")
st.sidebar.code(MY_WECHAT_ID, language="text")

st.markdown(f"""<div class="legal-footer"><b>免责声明</b><br>本系统仅供娱乐与技术交流。购彩需理性。<br>© 2024 AI 智算中心 | 客服微信：{MY_WECHAT_ID}</div>""", unsafe_allow_html=True)
