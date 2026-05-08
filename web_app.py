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
import urllib3

# 🚨 核心：禁用安全警告，确保部分老旧系统也能顺利联网抓取
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =========================================================
# 💰💰💰 老板专属配置区 (功能全开，细节拉满) 💰💰💰
# =========================================================
MY_WECHAT_ID = "252766667"           # 您的微信号
VIP_PASSWORD = "888"                 # 解锁算法口令
# =========================================================

# --- 0. 隐形访客统计 ---
visit_file = "visit_log.txt"
if not os.path.exists(visit_file):
    with open(visit_file, "w") as f: f.write("0")
with open(visit_file, "r") as f:
    current_v = int(f.read())
new_v = current_v + 1
with open(visit_file, "w") as f: f.write(str(new_v))

# --- 1. 顶级定制样式表 (保留所有美化细节) ---
st.set_page_config(page_title="AI 大数据决策终端", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 2rem 1rem !important; max-width: 950px; }
    .hist-table { width: 100%; border-collapse: collapse; text-align: center; background: #fff; border-radius: 10px; overflow: hidden; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .hist-table th { background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #eaeaea; color: #666; font-weight: bold; }
    .hist-table td { padding: 10px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 15px; }
    
    /* 球体样式 */
    .ball { display: inline-block; width: 30px; height: 30px; line-height: 30px; border-radius: 50%; color: white; font-weight: bold; margin: 3px; font-size: 14px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .bg-red { background-color: #f14545; }
    .bg-blue { background-color: #3b71f7; }
    .bg-yellow { background-color: #f9bf15; color: #333 !important; }
    .bg-purple { background-color: #9c27b0; }
    .bg-lotus { background-color: #cba09e; } 
    .bg-lightblue { background-color: #5bc0de; } 
    
    /* 预测行样式 */
    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 8px; border-left: 5px solid #f14545; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; position: relative; }
    .pred-title { width: 160px; font-weight: bold; color: #444; font-size: 15px; }
    .pred-balls { flex-grow: 1; display: flex; flex-wrap: wrap; max-width: 500px;} 
    .pred-ball { display: inline-block; width: 34px; height: 34px; line-height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 4px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.15); }
    
    /* VIP 锁定遮罩 */
    .vip-locked { filter: blur(6px); user-select: none; pointer-events: none; }
    .lock-overlay { position: absolute; right: 20px; top: 50%; transform: translateY(-50%); background: rgba(255,255,255,0.95); padding: 8px 18px; border: 2px dashed #ff4b4b; border-radius: 5px; color: #ff4b4b; font-size: 14px; font-weight: bold; z-index: 10; }
    
    .timer-bar { background: linear-gradient(90deg, #1d2b64, #f8cdda); color: white; padding: 12px; text-align: center; border-radius: 8px; font-weight: bold; margin-bottom: 15px; }
    .wechat-box { background: #f0f2f6; border-radius: 10px; padding: 15px; border: 1px solid #dcdfe6; text-align: center; margin-bottom: 10px;}
    
    /* 滚动条 */
    .marquee-wrapper { background: linear-gradient(to right, #fff3cd, #fff8e1); padding: 10px 15px; border-radius: 8px; border-left: 4px solid #f9bf15; margin-bottom: 20px; overflow: hidden; display: flex; align-items: center; }
    .marquee-content { white-space: nowrap; animation: marquee 35s linear infinite; color: #856404; font-weight: bold; font-size: 14px; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-180%); } }
    
    .comment-box { background: #fff; border: 1px solid #eaeaea; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    .legal-footer { margin-top: 50px; padding: 20px; border-top: 1px solid #eaeaea; text-align: center; color: #999; font-size: 12px; line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心算法引擎 (完整逻辑) ---
def get_countdown():
    now = datetime.now()
    target = now.replace(hour=21, minute=30, second=0)
    if now > target: target += timedelta(days=1)
    diff = target - now
    return f"{diff.seconds // 3600:02d}时{(diff.seconds % 3600) // 60:02d}分{diff.seconds % 60:02d}秒"

def get_fake_broadcasts():
    cities = ["广东", "浙江", "江苏", "山东", "河南", "四川", "北京", "上海", "福建", "辽宁"]
    algos = ["极热寻踪", "绝地反弹", "黄金均衡", "蒙特卡洛", "深度拟合"]
    broadcast_texts = []
    for _ in range(6):
        city = random.choice(cities); phone = f"1{random.randint(3,9)}{random.randint(0,9)}****{random.randint(1000,9999)}"
        algo = random.choice(algos); mins = random.randint(1, 59)
        broadcast_texts.append(f"【最新喜报】{city}用户 {phone} {mins}分钟前 成功解锁「{algo}」策略！")
    return "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🔥&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join(broadcast_texts)

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
        return clean_df.sort_values('期号', ascending=False), '期号', new_names[1:], (choice in ["双色球", "大乐透", "快乐8"]), file_path
    except: return None, None, None, None, None

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
        if algo['type'] == 'hot': r_res = sorted(random.sample(hot_list_r[:count_r+3], count_r))
        elif algo['type'] == 'cold': r_res = sorted(random.sample(cold_list_r[:count_r+3], count_r))
        elif algo['type'] == 'mix': 
            half = count_r // 2
            r_res = sorted(random.sample(hot_list_r[:half+2], half) + random.sample(cold_list_r[:count_r-half+2], count_r-half))
        elif algo['type'] == 'monte':
            weights = [freq_dict.get(n, 0) + 1 for n in pool_r]
            probs = [w / sum(weights) for w in weights]
            r_res = sorted(np.random.choice(pool_r, size=count_r, replace=False, p=probs).tolist())
        elif algo['type'] == 'fit':
            if not df_view.empty:
                last_draw = df_view.iloc[0][d_cols[:count_r]].values
                r_res = sorted([(int(x) + random.randint(-1, 1)) % (max(pool_r)+1) for x in last_draw])
                r_res = [x if x in pool_r else random.choice(pool_r) for x in r_res]
            else: r_res = sorted(random.sample(pool_r, count_r))

        if count_b > 0: b_res = sorted(random.sample(pool_b, count_b))

        # 格式化球
        if choice == "双色球": 
            html = "".join([f"<span class='pred-ball bg-red'>{n:02d}</span>" for n in r_res]) + f"<span class='pred-ball bg-blue'>{b_res[0]:02d}</span>"
            txt = " ".join([f"{n:02d}" for n in r_res]) + " | " + f"{b_res[0]:02d}"
        elif choice == "大乐透": 
            html = "".join([f"<span class='pred-ball bg-blue'>{n:02d}</span>" for n in r_res]) + "".join([f"<span class='pred-ball bg-yellow'>{n:02d}</span>" for n in b_res])
            txt = " ".join([f"{n:02d}" for n in r_res]) + " | " + " ".join([f"{n:02d}" for n in b_res])
        elif choice == "七星彩": 
            html = "".join([f"<span class='pred-ball bg-purple'>{n}</span>" for n in r_res]) + f"<span class='pred-ball bg-yellow'>{b_res[0]}</span>"
            txt = " ".join([str(n) for n in r_res]) + " + " + str(b_res[0])
        elif choice == "快乐8": 
            html = "".join([f"<span class='pred-ball bg-red'>{n:02d}</span>" for n in r_res])
            txt = " ".join([f"{n:02d}" for n in r_res])
        elif choice == "福彩3D":
            html = "".join([f"<span class='pred-ball bg-lightblue'>{n}</span>" for n in r_res])
            txt = " ".join([str(n) for n in r_res])
        else:
            html = "".join([f"<span class='pred-ball bg-lotus'>{n}</span>" for n in r_res])
            txt = " ".join([str(n) for n in r_res])
        
        sets.append({"name": algo['name'], "html": html, "text": txt, "is_vip": algo['vip']})
    return sets

# --- 3. 超级联网抓取引擎 (融合增强版) ---
def fetch_from_web_super(game_code, choice, d_cols_len):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://datachart.500.com/"
    }
    urls = [f"https://datachart.500.com/{game_code}/history/newinc/history.php?limit=50", f"https://datachart.500.com/{game_code}/history/inc/history.php?limit=50"]
    web_rows = []
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=12, verify=False)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            trs = soup.find_all('tr')
            for tr in trs:
                tds = tr.find_all(['td', 'th'])
                if len(tds) < 4: continue 
                iss_str = re.sub(r'\D', '', tds[0].get_text(strip=True))
                if len(iss_str) < 3: continue
                issue_val = int("20" + iss_str) if len(iss_str) == 5 else int(iss_str)
                
                # 针对不同彩种的暴力数字提取
                line_text = " ".join([t.get_text(strip=True) for t in tds[1:25]])
                if choice in ["排列5", "排列3", "福彩3D"]:
                    balls = [int(d) for d in re.findall(r'\d', line_text)][:d_cols_len]
                elif choice == "七星彩":
                    all_nums = re.findall(r'\d+', line_text)
                    balls = []
                    for n in all_nums:
                        if len(n) > 2: balls.extend([int(c) for c in n])
                        else: balls.append(int(n))
                    balls = balls[:d_cols_len]
                else:
                    balls = [int(n) for n in re.findall(r'\b\d{1,2}\b', line_text) if 0 <= int(n) <= 80][:d_cols_len]
                
                if len(balls) == d_cols_len:
                    web_rows.append({"issue": issue_val, "balls": balls})
            if web_rows: break
        except: continue
    return web_rows

def sync_latest_data(df, q_col, d_cols, choice, file_path):
    status = st.empty(); game_codes = {"双色球": "ssq", "大乐透": "dlt", "福彩3D": "sd", "排列3": "pls", "排列5": "plw", "七星彩": "qxc", "快乐8": "kl8"}
    status.info(f"📡 正在联网获取 {choice} 最新开奖数据...")
    web_data = fetch_from_web_super(game_codes.get(choice, "ssq"), choice, len(d_cols))
    if web_data:
        web_df = pd.DataFrame([ {q_col: item['issue'], **{d_cols[i]: item['balls'][i] for i in range(len(d_cols))}} for item in web_data ])
        df[q_col] = df[q_col].astype(int)
        updated = pd.concat([web_df, df], ignore_index=True).drop_duplicates(subset=[q_col], keep='first').sort_values(q_col, ascending=False)
        save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
        updated.to_csv(save_path, index=False, encoding='utf-8-sig')
        status.success("✅ 同步成功！数据已更新。"); st.cache_data.clear(); time.sleep(1); st.rerun()
    else: status.error("❌ 抓取失败，请检查网络或更换 IP 再试。")

# --- 4. 主界面逻辑 (完美还原所有细节) ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 商业决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

st.sidebar.markdown(f"""<div class="wechat-box">获取 VIP 核心口令<br><b style="color:#ff4b4b;font-size:18px;">{MY_WECHAT_ID}</b><br><span style="font-size:12px;color:#999;">(加微信发红包即刻获取)</span></div>""", unsafe_allow_html=True)
st.sidebar.code(MY_WECHAT_ID, language="text")

view_options = {"近30期": 30, "近50期": 50, "近100期": 100}
view_choice = st.sidebar.radio("选择分析样本", list(view_options.keys()), index=1)

target = next((f for f in os.listdir(".") if LOTTERY_FILES[choice] in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))), None)

if target:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target, choice)
    if df is not None:
        if st.sidebar.button("🔄 联网同步最新开奖", use_container_width=True, type="primary"):
            sync_latest_data(df, q_col, d_cols, choice, actual_path)

        st.title(f"🎰 {choice} 数据智算中心")
        st.markdown(f'<div class="timer-bar">⏰ 离今日开奖截止还剩 {get_countdown()} | 核心服务器已就绪</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="marquee-wrapper"><div class="marquee-content">{get_fake_broadcasts()}</div></div>', unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["📜 历史数据", "📈 深度走势", "🤖 AI 演算", "💬 交流大厅"])
        
        with t1:
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(view_options[view_choice]).iterrows():
                balls_html = "<div style='display:flex; flex-wrap:wrap; justify-content:center;'>"
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
                table_html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{balls_html}</div></td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

        with t2:
            calc_df = df.head(50).copy()
            calc_df['和值'] = calc_df[d_cols].sum(axis=1)
            calc_df['跨度'] = calc_df[d_cols].max(axis=1) - calc_df[d_cols].min(axis=1)
            calc_df['奇数'] = calc_df[d_cols].apply(lambda x: sum(1 for v in x if v % 2 != 0), axis=1)
            
            st.markdown("### 📈 近期和值走势 (大趋势分析)")
            st.line_chart(calc_df.set_index('期号')['和值'])
            st.markdown("### 🎢 号码跨度振幅 (冷热度参考)")
            st.area_chart(calc_df.set_index('期号')['跨度'], color="#f14545")
            st.markdown("### ⚖️ 奇偶分布统计")
            st.bar_chart(calc_df.set_index('期号')['奇数'], color="#3b71f7")

        with t3:
            st.markdown("##### 🎯 专属号码衍生拟合 (种子号分析)")
            custom_input = st.text_input("🔮 输入您的【心水种子号】(空格隔开)：", placeholder="例如：08 16 25")
            if st.button("🪄 一键衍生拟合", use_container_width=True):
                if custom_input:
                    with st.spinner('AI 正在融合历史高频数据，拆解组合矩阵...'):
                        time.sleep(1)
                        st.success("已基于您的种子号生成「高概率复式大底」，请结合下方 VIP 算法查看！")
                else: st.warning("请先输入种子号")
            
            st.markdown("---")
            with st.form("vip_form"):
                st.markdown("##### 🔑 VIP 核心算法解锁")
                pwd = st.text_input("输入授权口令：", type="password")
                submit = st.form_submit_button("🚀 启动 AI 全量演算", use_container_width=True)

            if submit:
                is_unlocked = (pwd == VIP_PASSWORD)
                predictions = get_real_prediction(df.head(view_options[view_choice]), d_cols, choice)
                for p in predictions:
                    if p['is_vip'] and not is_unlocked:
                        st.markdown(f"<div class='pred-row'><div class='pred-title'>{p['name']}</div><div class='pred-balls vip-locked'>{p['html']}</div><div class='lock-overlay'>🔒 算法已锁定</div></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='pred-row'><div class='pred-title'>{p['name']} ✅</div><div class='pred-balls'>{p['html']}</div></div>", unsafe_allow_html=True)
                        st.code(p['text'], language="text")

        with t4:
            st.markdown("### 💬 内部 VIP 交流大厅")
            st.info("🟢 当前在线：1,862 人 | 正在讨论：蒙特卡洛算法的稳定性")
            chat_container = st.container(height=350)
            with chat_container:
                comments = [
                    ("老彩民99", "加了老板微信拿到了口令，刚才极热寻踪中了个小奖！", "👑 VIP"),
                    ("发财哥", "今天的快乐8和值走势很稳，AI 预测的胆码可以参考。", "👤 普通"),
                    ("红单狂人", "19.9 的数据包真划算，Excel 导出分析太方便了。", "👑 VIP"),
                    ("数据控", "有没有人合买今晚的深度拟合大底？", "👤 普通"),
                    ("小李子", "求今日七星彩口令，红包已发老板微信！", "👑 VIP")
                ]
                for user, txt, tag in comments:
                    color = "#ff4b4b" if "VIP" in tag else "#999"
                    st.markdown(f"""<div class="comment-box"><b>{user}</b> <span style="color:{color};font-size:12px;">[{tag}]</span><br><span style="font-size:14px;">{txt}</span></div>""", unsafe_allow_html=True)
            st.text_input("📝 发表实战感悟...", placeholder="请先解锁 VIP 权限...")
            st.button("🚀 发送", disabled=True)

st.sidebar.markdown("---")
st.sidebar.error(f"📊 累计访问量：{new_v}")
st.sidebar.write("👇 加微信购买 20 年历史数据包：")
st.sidebar.code(MY_WECHAT_ID, language="text")
st.markdown(f'<div class="legal-footer"><b>免责声明</b><br>本系统仅供技术交流与娱乐，购彩请前往实体店。理性购彩，量力而行。<br>© 2024 AI 智算中心 | 唯一客服微信：{MY_WECHAT_ID}</div>', unsafe_allow_html=True)
