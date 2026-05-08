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

# --- 0. 隐形访客统计 (仅后台记录) ---
visit_file = "visit_log.txt"
if not os.path.exists(visit_file):
    with open(visit_file, "w") as f: f.write("0")
with open(visit_file, "r") as f:
    current_v = int(f.read())
new_v = current_v + 1
with open(visit_file, "w") as f: f.write(str(new_v))

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

# --- 🚀 核心修复：穿透式抓取引擎 ---
@st.cache_data(ttl=3600)
def fetch_from_web(game_code, choice, d_cols_len):
    urls = [f"https://datachart.500.com/{game_code}/history/newinc/history.php?limit=50", f"https://datachart.500.com/{game_code}/history/inc/history.php?limit=50"]
    headers = {"User-Agent": "Mozilla/5.0"}
    web_rows = []
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            target_rows = soup.find_all('tr', class_=['t_tr1', 't_tr2', 't_tr'])
            if not target_rows: target_rows = soup.find_all('tr')
            
            for tr in target_rows:
                tds = tr.find_all('td')
                if len(tds) < 3: continue
                
                # 穿透提取期号
                iss_str = re.sub(r'\D', '', tds[0].get_text(strip=True))
                if len(iss_str) < 3: continue
                if len(iss_str) > 12: iss_str = iss_str[:11]
                issue_val = int("20" + iss_str) if len(iss_str) == 5 else int(iss_str)
                
                # 穿透提取全行数字内容
                all_content = " ".join([td.get_text(separator=" ") for td in tds[1:]])
                
                if choice == "快乐8":
                    nums = [int(n) for n in re.findall(r'\b\d{1,2}\b', all_content)]
                    balls = [n for n in nums if 1 <= n <= 80][:20]
                elif choice in ["排列5", "排列3", "福彩3D"]:
                    digits = re.findall(r'\d', "".join(re.findall(r'\d+', all_content)))
                    balls = [int(d) for d in digits][:d_cols_len]
                elif choice == "七星彩":
                    groups = re.findall(r'\d+', all_content)
                    balls = []
                    for g in groups:
                        if len(g) >= 3: balls.extend([int(c) for c in g])
                        else: balls.append(int(g))
                    balls = balls[:7]
                else:
                    balls = [int(n) for n in re.findall(r'\d+', all_content) if 0 <= int(n) <= 80][:d_cols_len]
                
                if len(balls) == d_cols_len:
                    web_rows.append({"issue": issue_val, "balls": balls})
            if web_rows: break
        except: continue
    return web_rows

def sync_latest_data(df, q_col, d_cols, choice, file_path):
    status = st.empty()
    game_codes = {"双色球": "ssq", "大乐透": "dlt", "福彩3D": "sd", "排列3": "pls", "排列5": "plw", "七星彩": "qxc", "快乐8": "kl8"}
    status.info(f"📡 正在联网获取 {choice} 最新开奖...")
    web_data = fetch_from_web(game_codes.get(choice, "ssq"), choice, len(d_cols))
    if web_data:
        try:
            web_df = pd.DataFrame([{q_col: int(str(item['issue'])[:12]), **{d_cols[i]: int(item['balls'][i]) for i in range(len(d_cols))}} for item in web_data]).astype('int64')
            df[q_col] = pd.to_numeric(df[q_col], errors='coerce').fillna(0).astype('int64')
            for c in d_cols: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype('int64')
            updated = pd.concat([web_df, df], ignore_index=True).drop_duplicates(subset=[q_col], keep='first').sort_values(q_col, ascending=False).head(2000)
            save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
            updated.to_csv(save_path, index=False, encoding='utf-8-sig')
            status.success(f"✅ 同步成功！"); st.cache_data.clear(); time.sleep(1); st.rerun()
        except: status.error("🚨 同步冲突，建议手动检查文件")
    else: status.error("❌ 抓取失败")

# --- 数据载入 ---
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
            if not nums.empty and (nums <= 81).all(): ball_cols.append(col)
            if len(ball_cols) == max_balls: break
        clean_df = raw_df[[q_col] + ball_cols].copy()
        new_names = ['期号'] + [f"b_{i+1}" for i in range(len(ball_cols))]
        clean_df.columns = new_names
        for c in new_names: clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0).astype(int)
        needs_zero = True if choice in ["双色球", "大乐透", "快乐8"] else False
        return clean_df.sort_values('期号', ascending=False), '期号', new_names[1:], needs_zero, file_path
    except: return None, None, None, None, None

def get_real_prediction(df_view, d_cols, choice):
    sets = []
    all_nums = []
    for col in d_cols: all_nums.extend(df_view[col].dropna().astype(int).tolist())
    freq_dict = Counter(all_nums)
    sorted_by_freq = [item[0] for item in freq_dict.most_common()]
    rules = {"双色球": (list(range(1, 34)), 6, list(range(1, 17)), 1), "大乐透": (list(range(1, 36)), 5, list(range(1, 13)), 2), "七星彩": (list(range(0, 10)), 6, list(range(0, 15)), 1), "快乐8": (list(range(1, 81)), 20, [], 0), "福彩3D": (list(range(0, 10)), 3, [], 0), "排列3": (list(range(0, 10)), 3, [], 0), "排列5": (list(range(0, 10)), 5, [], 0)}
    pool_r, count_r, pool_b, count_b = rules.get(choice, rules["双色球"])
    hot_list_r = [n for n in sorted_by_freq if n in pool_r]
    hot_list_r.extend([n for n in pool_r if n not in hot_list_r])
    cold_list_r = hot_list_r[::-1]
    
    algos = [{"name": "🔥 极热寻踪", "type": "hot", "vip": False}, {"name": "🧊 绝地反弹", "type": "cold", "vip": False}, {"name": "⚖️ 黄金均衡", "type": "mix", "vip": False}, {"name": "🎲 蒙特卡洛引擎", "type": "monte", "vip": True}, {"name": "🧠 深度拟合网络", "type": "fit", "vip": True}]
    
    for algo in algos:
        r_res, b_res = [], []
        if algo['type'] == 'hot': r_res = sorted(random.sample(hot_list_r[:count_r+2], count_r))
        elif algo['type'] == 'cold': r_res = sorted(random.sample(cold_list_r[:count_r+2], count_r))
        elif algo['type'] == 'mix': 
            h = count_r // 2
            r_res = sorted(random.sample(hot_list_r[:h+2], h) + random.sample(cold_list_r[:count_r-h+2], count_r-h))
        elif algo['type'] == 'monte':
            w = [freq_dict.get(n, 0) + 1 for n in pool_r]
            r_res = sorted(np.random.choice(pool_r, size=count_r, replace=False, p=[x/sum(w) for x in w]).tolist())
        elif algo['type'] == 'fit':
            r_res = sorted(random.sample(hot_list_r[:count_r+5], count_r))
        
        if count_b > 0: b_res = sorted(random.sample(pool_b, count_b))
        
        if choice == "双色球": html = "".join([f"<span class='pred-ball bg-red'>{n:02d}</span>" for n in r_res]) + f"<span class='pred-ball bg-blue'>{b_res[0]:02d}</span>"
        elif choice == "大乐透": html = "".join([f"<span class='pred-ball bg-blue'>{n:02d}</span>" for n in r_res]) + "".join([f"<span class='pred-ball bg-yellow'>{n:02d}</span>" for n in b_res])
        elif choice == "七星彩": html = "".join([f"<span class='pred-ball bg-purple'>{n}</span>" for n in r_res]) + f"<span class='pred-ball bg-yellow'>{b_res[0]}</span>"
        elif choice == "福彩3D": html = "".join([f"<span class='pred-ball bg-lightblue'>{n}</span>" for n in r_res])
        else: html = "".join([f"<span class='pred-ball bg-lotus'>{n}</span>" for n in r_res]) if choice != "快乐8" else "".join([f"<span class='pred-ball bg-red'>{n:02d}</span>" for n in r_res])
        
        sets.append({"name": algo['name'], "html": html, "text": f"【{choice}】{algo['name']} 推荐号码: {' '.join([f'{n:02d}' if choice in ['双色球','大乐透','快乐8'] else str(n) for n in r_res])}", "is_vip": algo['vip']})
    return sets

# --- 主页面布局 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 商业决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

st.sidebar.markdown(f'<div class="wechat-box"><span style="font-size:14px; color:#666;">获取核心【VIP内部口令】</span><br><b style="color:#ff4b4b; font-size:13px; display:inline-block; margin-top:10px;">👇 点击下方微信号自动复制 👇</b></div>', unsafe_allow_html=True)
st.sidebar.code(MY_WECHAT_ID, language="text")
st.sidebar.markdown("---")
view_options = {"近30期": 30, "近50期": 50, "近100期": 100}
view_choice = st.sidebar.radio("选择分析样本", list(view_options.keys()), index=1)

file_kw = LOTTERY_FILES[choice]
all_files = [f for f in os.listdir(".") if file_kw in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))]
target = next((f for f in all_files if '_synced' in f), all_files[0] if all_files else None)

if target:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target, choice)
    if df is not None:
        st.sidebar.markdown(f"**📊 库中最新：** `{int(df[q_col].max())}` 期")
        if st.sidebar.button("🔄 联网同步最新开奖", use_container_width=True, type="primary"):
            sync_latest_data(df, q_col, d_cols, choice, actual_path)

        st.title(f"🎰 {choice} 数据智算中心")
        st.markdown(f'<div class="timer-bar">⏰ 离今日开奖截止还剩 {get_countdown()} | 核心服务器已就绪</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="marquee-wrapper"><div class="marquee-icon">📢</div><div class="marquee-content">{get_fake_broadcasts()}</div></div>', unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["📜 历史数据", "📈 深度走势", "🤖 AI 演算", "💬 交流大厅"])
        
        with t1:
            st.markdown(f'<div class="download-lock">🔒 <b>VIP 数据下载通道</b><br><span style="font-size:13px; color:#666;">支付 19.9 元开启全量 Excel 导出权限。微信：{MY_WECHAT_ID}</span></div>', unsafe_allow_html=True)
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(view_options[view_choice]).iterrows():
                max_w = "280px" if choice == "快乐8" else "100%"
                balls_html = f"<div style='display:flex; flex-wrap:wrap; justify-content:center; margin: 0 auto; max-width: {max_w};'>"
                for i, col in enumerate(d_cols):
                    txt = f"{row[col]:02d}" if needs_zero else str(row[col])
                    bg = "bg-red"
                    if choice == "双色球": bg = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": bg = "bg-yellow" if i >= 5 else "bg-blue"
                    elif choice == "七星彩": bg = "bg-yellow" if i == 6 else "bg-purple"
                    elif choice == "福彩3D": bg = "bg-lightblue"
                    elif choice in ["排列3", "排列5"]: bg = "bg-lotus"
                    balls_html += f"<span class='ball {bg}'>{txt}</span>"
                table_html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{balls_html}</div></td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

        with t2:
            calc_df = df.head(view_options[view_choice]).copy()
            calc_df['和值'] = calc_df[d_cols].sum(axis=1)
            calc_df['跨度'] = calc_df[d_cols].max(axis=1) - calc_df[d_cols].min(axis=1)
            calc_df['奇数个数'] = calc_df[d_cols].apply(lambda row: sum(1 for x in row if x % 2 != 0), axis=1)
            st.markdown("### 📈 近期和值走势"); st.line_chart(calc_df.set_index('期号')['和值'])
            st.markdown("### 🎢 号码跨度振幅"); st.area_chart(calc_df.set_index('期号')['跨度'], color="#f14545")
            st.markdown("### ⚖️ 奇偶分布走势"); st.bar_chart(calc_df.set_index('期号')['奇数个数'], color="#3b71f7")

        with t3:
            st.info(f"💡 提示：当前根据「{view_choice}」演算。")
            st.markdown("##### 🎯 专属号码多维衍算")
            custom_input = st.text_input("🔮 输入您的【心水种子号】(用空格隔开)：", placeholder="例如：06 18")
            if st.button("🪄 一键衍生拟合", use_container_width=True):
                if custom_input.strip():
                    with st.spinner('AI 正在融合数据...'):
                        time.sleep(1)
                        seed_nums = [int(n) for n in re.findall(r'\d+', custom_input)]
                        rules = {"双色球": (list(range(1, 34)), 6), "大乐透": (list(range(1, 36)), 5), "快乐8": (list(range(1, 81)), 20), "福彩3D": (list(range(0, 10)), 3), "排列3": (list(range(0, 10)), 3), "排列5": (list(range(0, 10)), 5), "七星彩": (list(range(0, 10)), 6)}
                        p_r, c_r = rules.get(choice, (range(1, 34), 6))
                        valid = [n for n in seed_nums if n in p_r]
                        def get_c(count):
                            res = set(random.sample(valid, min(len(valid), count)))
                            while len(res) < count: res.add(random.choice(p_r))
                            return sorted(list(res))
                        ma_1 = get_c(1); ma_3 = get_c(3); ma_5 = get_c(5); ma_6 = get_c(6)
                        def fmt(ns): 
                            color = "bg-red" if choice in ["双色球","快乐8"] else "bg-blue"
                            return "".join([f"<span class='pred-ball {color}'>{n:02d if needs_zero else n}</span>" for n in ns])
                        st.markdown(f"<div class='pred-row'><div class='pred-title'>🎯 核心胆码</div><div class='pred-balls'>{fmt(ma_1)}</div></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='pred-row'><div class='pred-title'>🥉 精选组合</div><div class='pred-balls'>{fmt(ma_3)}</div></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='pred-row'><div class='pred-title'>🥇 大底复式</div><div class='pred-balls'>{fmt(ma_6)}</div></div>", unsafe_allow_html=True)
                else: st.warning("⚠️ 请输入心水号")
            
            st.markdown("---")
            with st.form("ai_form"):
                user_pwd = st.text_input("🔑 VIP 口令", type="password")
                if st.form_submit_button("🚀 验证并启动 AI 演算", use_container_width=True):
                    is_unlocked = (user_pwd == VIP_PASSWORD)
                    preds = get_real_prediction(df.head(view_options[view_choice]), d_cols, choice)
                    for p in preds:
                        if p['is_vip'] and not is_unlocked:
                            st.markdown(f"<div class='pred-row'><div class='pred-title'>{p['name']}</div><div class='pred-balls vip-locked'>{p['html']}</div><div class='lock-overlay'>🔒 算法锁定</div></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='pred-row'><div class='pred-title'>{p['name']} ✅</div><div class='pred-balls'>{p['html']}</div></div>", unsafe_allow_html=True)
                            st.code(p['text'])

        with t4:
            st.info("🟢 当前在线：1,862 人")
            if 'comments' not in st.session_state:
                st.session_state.comments = [{"user": f"用户{random.randint(10,99)}", "text": "拿到口令了，确实好使！", "time": "3分钟前", "vip": True} for _ in range(5)]
            for c in st.session_state.comments:
                st.markdown(f'<div class="comment-box"><div class="comment-header"><span class="comment-user">{c["user"]}</span><span class="comment-time">{c["time"]}</span></div><div class="comment-body">{c["text"]}</div></div>', unsafe_allow_html=True)
            if st.button("🚀 发送留言", use_container_width=True): st.error("游客禁言！请联系站长。")

st.sidebar.error("🔥 内部数据福利")
st.sidebar.markdown(f"- ✅ **20年** 历史开奖全库\n- 💰 限时特惠：**19.9 元**")
st.sidebar.code(MY_WECHAT_ID, language="text")
st.markdown(f'<div class="legal-footer"><b>免责声明</b><br>仅供娱乐与交流。购彩需理性。<br>© 2024 AI 智算中心 | 客服微信：{MY_WECHAT_ID}</div>', unsafe_allow_html=True)
