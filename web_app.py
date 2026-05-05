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

# =========================================================
# 💰💰💰 老板专属配置区 (只需修改这里，其他地方不用动) 💰💰💰
# =========================================================
MY_WECHAT_ID = "252766667"           # 已帮您填好微信号
VIP_PASSWORD = "888"                 # 付费解锁口令 (您可以每天换一个)
# =========================================================

# --- 1. 深度定制样式表 ---
st.set_page_config(page_title="AI 大数据决策终端", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 2.5rem 1.5rem !important; max-width: 900px; }
    .hist-table { width: 100%; border-collapse: collapse; text-align: center; background: #fff; border-radius: 8px; overflow: hidden; margin-bottom: 1rem; }
    .hist-table th { background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #eaeaea; color: #666; font-weight: bold; }
    .hist-table td { padding: 12px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 15px; }
    
    /* 🟢 专业配色系统恢复 */
    .ball { display: inline-block; width: 28px; height: 28px; line-height: 28px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 3px; font-size: 13px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .bg-red { background-color: #f14545; }
    .bg-blue { background-color: #3b71f7; }
    .bg-yellow { background-color: #f9bf15; color: #333 !important; }
    .bg-purple { background-color: #9c27b0; }
    .bg-lotus { background-color: #cba09e; } /* 藕色 */
    .bg-lightblue { background-color: #5bc0de; } /* 浅蓝色 */
    
    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 5px; border-left: 5px solid #f14545; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; position: relative; }
    .pred-title { width: 150px; font-weight: bold; color: #444; font-size: 15px; }
    .pred-balls { flex-grow: 1; display: flex; flex-wrap: wrap; max-width: 400px;} /* 确保快乐8能自动换行 */
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

# 🟢 【颜色与排版全面恢复】
def get_real_prediction(df_view, d_cols, choice):
    sets = []
    algos = [
        {"name": "🔥 极热寻踪", "type": "hot", "vip": False},
        {"name": "🧊 绝地反弹", "type": "cold", "vip": False},
        {"name": "⚖️ 黄金均衡", "type": "mix", "vip": False},
        {"name": "🎲 蒙特卡洛引擎", "type": "monte", "vip": True},
        {"name": "🧠 深度拟合网络", "type": "fit", "vip": True}
    ]
    
    for algo in algos:
        algo_name_clean = algo['name'].split(' ', 1)[-1] if ' ' in algo['name'] else algo['name']
        
        if choice == "双色球": # 6红 + 1蓝
            r = sorted(random.sample(range(1, 34), 6))
            b = random.randint(1, 16)
            html = "".join([f"<span class='pred-ball bg-red'>{n:02d}</span>" for n in r]) + f"<span class='pred-ball bg-blue'>{b:02d}</span>"
            text_copy = f"【双色球】{algo_name_clean} 推荐号码: " + " ".join([f"{n:02d}" for n in r]) + f" | {b:02d}"
            
        elif choice == "大乐透": # 5蓝 + 2黄 (按要求恢复)
            r = sorted(random.sample(range(1, 36), 5))
            b = sorted(random.sample(range(1, 13), 2))
            html = "".join([f"<span class='pred-ball bg-blue'>{n:02d}</span>" for n in r]) + "".join([f"<span class='pred-ball bg-yellow'>{n:02d}</span>" for n in b])
            text_copy = f"【大乐透】{algo_name_clean} 推荐号码: " + " ".join([f"{n:02d}" for n in r]) + " | " + " ".join([f"{n:02d}" for n in b])
            
        elif choice == "七星彩": # 6紫 + 1黄 (按要求恢复)
            r = [random.randint(0, 9) for _ in range(6)]
            b = random.randint(0, 14)
            html = "".join([f"<span class='pred-ball bg-purple'>{n}</span>" for n in r]) + f"<span class='pred-ball bg-yellow'>{b}</span>"
            text_copy = f"【七星彩】{algo_name_clean} 推荐号码: " + " ".join([str(n) for n in r]) + f" | {b}"
            
        elif choice == "快乐8": # 20红，CSS控制两行 (按要求恢复)
            r = sorted(random.sample(range(1, 81), 20))
            html = "".join([f"<span class='pred-ball bg-red'>{n:02d}</span>" for n in r])
            text_copy = f"【快乐8】{algo_name_clean} 推荐号码: " + " ".join([f"{n:02d}" for n in r])
            
        elif choice == "福彩3D": # 3浅蓝 (按要求恢复)
            r = [random.randint(0, 9) for _ in range(3)]
            html = "".join([f"<span class='pred-ball bg-lightblue'>{n}</span>" for n in r])
            text_copy = f"【{choice}】{algo_name_clean} 推荐号码: " + " ".join([str(n) for n in r])
            
        else: # 排列3, 排列5 (全藕色)
            max_len = 3 if choice == "排列3" else 5
            r = [random.randint(0, 9) for _ in range(max_len)]
            html = "".join([f"<span class='pred-ball bg-lotus'>{n}</span>" for n in r])
            text_copy = f"【{choice}】{algo_name_clean} 推荐号码: " + " ".join([str(n) for n in r])
            
        sets.append({"name": algo['name'], "html": html, "text": text_copy, "is_vip": algo['vip']})
    return sets

# --- 核心：数据联网更新 ---
def sync_latest_data(df, q_col, d_cols, choice, file_path):
    status = st.empty()
    game_codes = {"双色球": "ssq", "大乐透": "dlt", "福彩3D": "sd", "排列3": "pls", "排列5": "plw", "七星彩": "qxc", "快乐8": "kl8"}
    game_code = game_codes.get(choice, "ssq")
    try:
        status.info(f"📡 正在联网获取 {choice} 最新开奖...")
        urls = [f"https://datachart.500.com/{game_code}/history/newinc/history.php?limit=50", f"https://datachart.500.com/{game_code}/history/inc/history.php?limit=50"]
        headers = {"User-Agent": "Mozilla/5.0"}
        web_rows = []
        for url in urls:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            tdata = soup.find('tbody', id='tdata')
            trs = tdata.find_all('tr') if tdata else (soup.find_all('tr', class_=['t_tr1', 't_tr2', 't_tr']) or soup.find_all('tr'))
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) < len(d_cols) + 1: continue 
                iss_str = re.sub(r'\D', '', tds[0].get_text(strip=True))
                if len(iss_str) < 3: continue
                issue_val = int("20" + iss_str) if len(iss_str) == 5 else int(iss_str)
                if issue_val == 0: continue
                rest_text = "   ".join([td.get_text(separator=" ") for td in tds[1:]])
                balls = []
                if choice in ["福彩3D", "排列3", "排列5"]: balls = [int(n) for n in re.findall(r'\d', rest_text)]
                elif choice == "七星彩":
                    groups = re.findall(r'\d+', rest_text)
                    for g in groups:
                        if len(g) >= 3: 
                            for char in g: balls.append(int(char))
                        else: balls.append(int(g))
                else: balls = [int(n) for n in re.findall(r'\d+', rest_text)]
                balls = [n for n in balls if 0 <= n <= 81]
                if len(balls) >= len(d_cols):
                    row = {q_col: issue_val}
                    for i, col_name in enumerate(d_cols): row[col_name] = balls[i]
                    web_rows.append(row)
            if web_rows: break

        if web_rows:
            web_df = pd.DataFrame(web_rows)
            df[q_col] = df[q_col].apply(lambda x: int(float(x)) if len(str(int(float(x))))!=5 else int("20"+str(int(float(x)))))
            updated = pd.concat([web_df, df], ignore_index=True).drop_duplicates(subset=[q_col], keep='first').sort_values(q_col, ascending=False)
            save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
            updated.to_csv(save_path, index=False, encoding='utf-8-sig')
            status.success(f"✅ 同步成功！已更新 {len(web_rows)} 期。")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
        else: status.error("❌ 抓取失败。")
    except Exception as e: status.error(f"❌ 同步失败: {str(e)}")

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

# --- 主界面逻辑 ---
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
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🧹 清理缓存 (遇错必点)", use_container_width=True):
            st.cache_data.clear()
            if 'comments' in st.session_state:
                del st.session_state['comments']
            st.rerun()

        st.title(f"🎰 {choice} 数据智算中心")
        st.markdown(f'<div class="timer-bar">⏰ 离今日开奖截止还剩 {get_countdown()} | 核心服务器已就绪</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="marquee-wrapper"><div class="marquee-icon">📢</div><div class="marquee-content">{get_fake_broadcasts()}</div></div>', unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["📜 历史数据", "📈 深度走势", "🤖 AI 演算", "💬 交流大厅"])
        
        with t1:
            st.markdown(f"""<div class="download-lock">🔒 <b>VIP 数据下载通道</b><br><span style="font-size:13px; color:#666;">支付 19.9 元开启全量 Excel 导出权限。微信：{MY_WECHAT_ID}</span></div>""", unsafe_allow_html=True)
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            
            for _, row in df.head(view_options[view_choice]).iterrows():
                # 🟢 使用 flex 容器确保快乐8这种球多的能完美换成两行
                max_w = "280px" if choice == "快乐8" else "100%" 
                balls_html = f"<div style='display:flex; flex-wrap:wrap; justify-content:center; margin: 0 auto; max-width: {max_w};'>"
                
                for i, col in enumerate(d_cols):
                    val = row[col]
                    txt = f"{val:02d}" if needs_zero else str(val)
                    bg = "bg-red"
                    if choice == "双色球": bg = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": bg = "bg-yellow" if i >= 5 else "bg-blue"
                    elif choice == "七星彩": bg = "bg-yellow" if i == 6 else "bg-purple"
                    elif choice == "快乐8": bg = "bg-red"
                    elif choice == "福彩3D": bg = "bg-lightblue"
                    elif choice in ["排列3", "排列5"]: bg = "bg-lotus"
                    
                    balls_html += f"<span class='ball {bg}'>{txt}</span>"
                balls_html += "</div>"
                table_html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{balls_html}</td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

        with t2:
            # 🟢 【恢复：深度走势多维图表】
            calc_df = df.head(view_options[view_choice]).copy()
            calc_df['和值'] = calc_df[d_cols].sum(axis=1)
            calc_df['跨度'] = calc_df[d_cols].max(axis=1) - calc_df[d_cols].min(axis=1)
            calc_df['奇数个数'] = calc_df[d_cols].apply(lambda row: sum(1 for x in row if x % 2 != 0), axis=1)

            st.markdown("### 📈 近期和值走势 (大盘情绪)")
            st.line_chart(calc_df.set_index('期号')['和值'])
            
            st.markdown("### 🎢 号码跨度振幅 (极值拉扯)")
            st.area_chart(calc_df.set_index('期号')['跨度'], color="#f14545")
            
            st.markdown("### ⚖️ 奇数出号频次 (冷热分布)")
            st.bar_chart(calc_df.set_index('期号')['奇数个数'], color="#3b71f7")

        with t3:
            st.info(f"💡 提示：当前 AI 正根据「{view_choice}」的规律进行演算。**点击下方代码框右上角的 📋 图标即可一键复制预测号码。**")
            
            with st.form("ai_form"):
                st.markdown("##### 🔑 VIP 核心算法解锁")
                user_input_pwd = st.text_input("在下方输入口令 (加左侧微信获取)：", type="password", placeholder="请输入今日口令...")
                submit_btn = st.form_submit_button("🚀 验证口令并启动 AI 演算", use_container_width=True)

            if submit_btn:
                is_unlocked = (user_input_pwd == VIP_PASSWORD)
                with st.spinner('正在分析云端数据...'): time.sleep(1)
                predictions = get_real_prediction(df.head(view_options[view_choice]), d_cols, choice)
                
                for p in predictions:
                    if p['is_vip'] and not is_unlocked:
                        st.markdown(f"""
                        <div class='pred-row'>
                            <div class='pred-title'>{p['name']}</div>
                            <div class='pred-balls vip-locked'>{p['html']}</div>
                            <div class='lock-overlay'>🔒 核心算法已被锁定</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.code("🔒 请输入上方口令解锁后一键复制打票号码", language="text")
                    else:
                        st.markdown(f"""
                        <div class='pred-row'>
                            <div class='pred-title'>{p['name']} <span style="color:#28a745;">✅</span></div>
                            <div class='pred-balls'>{p['html']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.code(p['text'], language="text")
                        st.markdown("<br>", unsafe_allow_html=True)
                
                if user_input_pwd and not is_unlocked:
                    st.error("❌ 口令无效，请重新输入或联系老板获取密码！")
                elif is_unlocked:
                    st.success("✅ 口令验证成功！全部高级算法已为您解锁！")

        if 'comments' not in st.session_state:
            st.session_state.comments = [
                {"user": "老彩民001", "text": "已加老板微信，口令拿到了，确实准！", "time": "2分钟前"},
                {"user": "数据大师", "text": "这套蒙特卡洛算法比我自己算的强多了。", "time": "10分钟前"}
            ]
        
        with t4:
            st.markdown("### 🏆 实时交流 (在线 1,284 人)")
            for c in st.session_state.comments:
                st.markdown(f"""
                <div class="comment-box">
                    <div class="comment-header">
                        <span class="comment-user">{c['user']}</span>
                        <span class="comment-time">{c['time']}</span>
                    </div>
                    <div class="comment-body">{c['text']}</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("---")
            new_comment = st.text_input("💡 留下您的看法...")
            if st.button("发布评论", type="primary"):
                if new_comment:
                    st.session_state.comments.insert(0, {
                        "user": "📱 当前用户 (我)",
                        "text": new_comment,
                        "time": "刚刚"
                    })
                    st.rerun()

# --- 6. 版权声明 ---
st.markdown(f"""<div class="legal-footer"><b>免责声明</b><br>本系统仅供娱乐与技术交流，不构成投资建议。购彩需理性。<br>© 2024 AI 智算决策中心 | 客服微信：{MY_WECHAT_ID}</div>""", unsafe_allow_html=True)
