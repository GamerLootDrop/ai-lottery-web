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

# --- 1. 深度定制样式表 (🔥 融合了原版 UI 与 VIP 商业锁定样式) ---
st.set_page_config(page_title="AI 大数据决策终端", layout="wide")
st.markdown("""
    <style>
    /* 基础布局 */
    .block-container { padding: 1.5rem !important; max-width: 900px; }
    
    /* 历史数据表格 */
    .hist-table { width: 100%; border-collapse: collapse; text-align: center; background: #fff; border-radius: 8px; overflow: hidden; margin-bottom: 1rem; }
    .hist-table th { background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #eaeaea; color: #666; font-weight: bold; }
    .hist-table td { padding: 12px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 15px; }
    
    /* 号码球样式 */
    .ball { display: inline-block; width: 28px; height: 28px; line-height: 28px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 3px; font-size: 13px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .bg-red { background-color: #f14545; }
    .bg-blue { background-color: #3b71f7; }
    .bg-yellow { background-color: #f9bf15; color: #333 !important; }
    .bg-purple { background-color: #9c27b0; }
    
    /* 预测区样式 */
    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #f14545; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; position: relative; }
    .pred-title { width: 150px; font-weight: bold; color: #444; font-size: 15px; }
    .pred-balls { flex-grow: 1; }
    .pred-ball { display: inline-block; width: 34px; height: 34px; line-height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 4px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.15); }
    
    /* 🔥 新增：VIP 锁定与引导样式 */
    .vip-locked { filter: blur(6px); user-select: none; pointer-events: none; }
    .lock-overlay { position: absolute; right: 20px; top: 50%; transform: translateY(-50%); background: rgba(255,255,255,0.9); padding: 5px 12px; border: 1px dashed #ff4b4b; border-radius: 5px; color: #ff4b4b; font-size: 13px; font-weight: bold; cursor: pointer; z-index: 10; }
    .timer-bar { background: linear-gradient(90deg, #1d2b64, #f8cdda); color: white; padding: 8px; text-align: center; border-radius: 5px; font-weight: bold; margin-bottom: 15px; }
    .download-lock { background: #fff5f5; border: 1px dashed #feb2b2; padding: 15px; text-align: center; border-radius: 8px; margin-bottom: 15px; }
    .wechat-box { background: #f0f2f6; border-radius: 10px; padding: 15px; border: 1px solid #dcdfe6; text-align: center; margin-bottom: 20px;}
    
    /* 📢 跑马灯样式 (滚动播报) */
    .marquee-wrapper { background: linear-gradient(to right, #fff3cd, #fff8e1); padding: 10px 15px; border-radius: 8px; border-left: 4px solid #f9bf15; margin-bottom: 20px; overflow: hidden; display: flex; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .marquee-icon { font-size: 18px; margin-right: 10px; min-width: 25px; }
    .marquee-content { white-space: nowrap; animation: marquee 25s linear infinite; color: #856404; font-weight: bold; font-size: 14px; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-150%); } }
    
    /* 💬 评论区样式 */
    .comment-box { background: #fff; border: 1px solid #eaeaea; border-radius: 8px; padding: 15px; margin-bottom: 10px; }
    .comment-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
    .comment-user { font-weight: bold; color: #1f77b4; font-size: 14px; }
    .comment-time { color: #999; font-size: 12px; }
    .comment-body { color: #444; font-size: 14px; line-height: 1.5; }
    
    /* 底部免责声明 */
    .legal-footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #eaeaea; text-align: center; color: #999; font-size: 12px; line-height: 1.8; }
    
    /* 📱 手机端专属适配 */
    @media (max-width: 768px) {
        .block-container { padding: 0.5rem !important; }
        .hist-table th, .hist-table td { padding: 8px 4px; font-size: 12px; }
        .ball { width: 22px; height: 22px; line-height: 22px; font-size: 11px; margin: 2px 1px; }
        .pred-row { flex-direction: column; align-items: flex-start; }
        .pred-title { margin-bottom: 8px; }
        .pred-ball { width: 28px; height: 28px; line-height: 28px; font-size: 13px; margin: 2px; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 生成倒计时 ---
def get_countdown():
    now = datetime.now()
    target = now.replace(hour=21, minute=30, second=0)
    if now > target: target += timedelta(days=1)
    diff = target - now
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}时{minutes:02d}分{seconds:02d}秒"

# --- 初始化评论数据 ---
if 'comments' not in st.session_state:
    st.session_state.comments = [
        {"user": "📱 广东网友 139****8821", "text": "刚刚加老板微信拿到了【深度拟合】核心号，感觉这期均线要拐头了，跟两注试试水！", "time": "3分钟前"},
        {"user": "📱 山东网友 135****0012", "text": "这工具的冷热分布图太直观了，以前纯瞎蒙，现在起码有数据支撑了，给老板点赞👍", "time": "12分钟前"},
        {"user": "📱 浙江网友 186****5921", "text": "昨天的蒙特卡洛引擎差一点点！就差个蓝球！今天已续费！", "time": "半小时前"},
        {"user": "📱 四川网友 138****3344", "text": "一键提取数据的表格太好用了，省了自己做Excel的时间。", "time": "1小时前"}
    ]

# --- 生成随机滚动播报数据 ---
def get_fake_broadcasts(choice):
    cities = ["广东", "浙江", "江苏", "山东", "河南", "四川", "北京", "上海"]
    algos = ["极热寻踪", "绝地反弹", "黄金均衡", "蒙特卡洛", "深度拟合"]
    broadcast_texts = []
    for _ in range(5):
        city = random.choice(cities)
        phone = f"1{random.randint(3,9)}{random.randint(0,9)}****{random.randint(1000,9999)}"
        algo = random.choice(algos)
        mins = random.randint(1, 59)
        broadcast_texts.append(f"【最新喜报】{city}用户 {phone} {mins}分钟前 解锁了「{algo}」实战策略！")
    return "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🔥&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join(broadcast_texts)

# --- 2. 混合双引擎数据提取 (保持完全不动) ---
@st.cache_data
def load_full_data(file_path, choice):
    try:
        if choice in ["双色球", "大乐透", "福彩3D", "排列3"]:
            raw_df = pd.read_excel(file_path) if file_path.endswith('.xls') else pd.read_csv(file_path)
            if raw_df.empty: return None, None, None, None, None
            raw_df.columns = [str(c).strip() for c in raw_df.columns]
            
            q_col = next((c for c in raw_df.columns if '期' in c or 'NO' in c.upper()), None)
            if not q_col:
                raw_df = pd.read_excel(file_path, skiprows=1) if file_path.endswith('.xls') else pd.read_csv(file_path, skiprows=1)
                raw_df.columns = [str(c).strip() for c in raw_df.columns]
                q_col = next((c for c in raw_df.columns if '期' in c or 'NO' in c.upper()), raw_df.columns[0])
                
            raw_df[q_col] = pd.to_numeric(raw_df[q_col], errors='coerce')
            raw_df = raw_df.dropna(subset=[q_col])

            limits = {"双色球": 7, "大乐透": 7, "福彩3D": 3, "排列3": 3}
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
            q_col = '期号' 
            
            for c in new_names: clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0).astype(int)
            needs_zero = True if choice in ["双色球", "大乐透"] else False
            return clean_df.sort_values(q_col, ascending=False), q_col, new_names[1:], needs_zero, file_path
        else:
            raw_df = pd.read_csv(file_path, header=None, dtype=str) if file_path.endswith('.csv') else pd.read_excel(file_path, header=None, dtype=str)
            if raw_df.empty: return None, None, None, None, None
            limits = {"快乐8": 20, "排列5": 5, "七星彩": 7}
            max_balls = limits.get(choice, 7)
            extracted_rows = []
            for idx, row in raw_df.iterrows():
                nums = pd.to_numeric(row, errors='coerce')
                valid_nums = nums.dropna().tolist()
                if len(valid_nums) >= max_balls + 1:
                    if valid_nums[0] < 1000 and valid_nums[1] > 1000:
                        issue_num = int(valid_nums[1]); balls_start = 2
                    else:
                        issue_num = int(valid_nums[0]); balls_start = 1
                    balls = [int(n) for n in valid_nums[balls_start : balls_start+max_balls]]
                    if all(0 <= b <= 81 for b in balls): extracted_rows.append([issue_num] + balls)
            if not extracted_rows: raise ValueError(f"解析失败")
            new_names = ['期号'] + [f"b_{i+1}" for i in range(max_balls)]
            clean_df = pd.DataFrame(extracted_rows, columns=new_names)
            needs_zero = True if choice == "快乐8" else False
            return clean_df.sort_values('期号', ascending=False), '期号', new_names[1:], needs_zero, file_path
    except Exception as e:
        st.error(f"🚨 解析错误: {str(e)}")
        return None, None, None, None, None

# --- 3. 同步最新数据 (保持完全不动) ---
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

# --- 4. 🔥 全新：基于真实历史频率的预测引擎 (包含 VIP 锁定) ---
def get_real_prediction(df_view, d_cols, choice):
    # 统计所选范围内的所有号码频率
    all_balls = df_view[d_cols].values.flatten()
    count_map = Counter(all_balls)
    sorted_freq = count_map.most_common()
    hot_nums = [x[0] for x in sorted_freq]
    cold_nums = list(reversed(hot_nums))
    
    sets = []
    algos = [
        {"name": "🔥 极热寻踪", "type": "hot", "vip": False},
        {"name": "🧊 绝地反弹", "type": "cold", "vip": False},
        {"name": "⚖️ 黄金均衡", "type": "mix", "vip": False},
        {"name": "🎲 蒙特卡洛", "type": "monte", "vip": True},
        {"name": "🧠 深度拟合", "type": "fit", "vip": True}
    ]
    
    for algo in algos:
        # 为保证程序稳定，主要号码根据真实冷热抽取，特殊球(如蓝球)辅以随机
        r = []
        if choice == "双色球":
            base_pool = hot_nums if algo['type'] in ['hot', 'monte', 'fit'] else (cold_nums if algo['type'] == 'cold' else hot_nums[:10]+cold_nums[:10])
            base_pool = [n for n in base_pool if 1 <= n <= 33]
            r = sorted(random.sample(base_pool[:20] if len(base_pool)>=20 else list(range(1,34)), 6))
            b = random.randint(1, 16)
            html = "".join([f"<span class='pred-ball bg-red'>{n:02d}</span>" for n in r]) + f"<span class='pred-ball bg-blue'>{b:02d}</span>"
            text_copy = " ".join([f"{n:02d}" for n in r]) + f" | {b:02d}"
            
        elif choice == "大乐透":
            base_pool = hot_nums if algo['type'] in ['hot', 'monte', 'fit'] else (cold_nums if algo['type'] == 'cold' else hot_nums[:10]+cold_nums[:10])
            base_pool = [n for n in base_pool if 1 <= n <= 35]
            r = sorted(random.sample(base_pool[:20] if len(base_pool)>=20 else list(range(1,36)), 5))
            b = sorted(random.sample(range(1, 13), 2))
            html = "".join([f"<span class='pred-ball bg-blue'>{n:02d}</span>" for n in r]) + "".join([f"<span class='pred-ball bg-yellow'>{n:02d}</span>" for n in b])
            text_copy = " ".join([f"{n:02d}" for n in r]) + " | " + " ".join([f"{n:02d}" for n in b])
            
        elif choice == "快乐8":
            base_pool = hot_nums if algo['type'] in ['hot', 'monte'] else cold_nums
            r = sorted(random.sample(base_pool[:30] if len(base_pool)>=30 else list(range(1,81)), 20))
            html = "".join([f"<span class='pred-ball bg-red' style='width:26px;height:26px;line-height:26px;font-size:12px;margin:2px;'>{n:02d}</span>" for n in r[:10]])
            html += "<br>" + "".join([f"<span class='pred-ball bg-red' style='width:26px;height:26px;line-height:26px;font-size:12px;margin:2px;'>{n:02d}</span>" for n in r[10:]])
            text_copy = " ".join([f"{n:02d}" for n in r])
            
        else: # 3D, 排列3/5, 七星彩
            n_count = 7 if choice == "七星彩" else (5 if choice == "排列5" else 3)
            base_pool = hot_nums if algo['type'] in ['hot', 'monte', 'fit'] else cold_nums
            base_pool = [n for n in base_pool if 0 <= n <= 9]
            # 允许重复数字
            r = [random.choice(base_pool[:5] if len(base_pool)>=5 else list(range(10))) for _ in range(n_count)]
            if choice == "七星彩":
                html = "".join([f"<span class='pred-ball bg-purple'>{n}</span>" for n in r[:6]]) + f"<span class='pred-ball bg-yellow'>{r[6]}</span>"
            else:
                html = "".join([f"<span class='pred-ball bg-purple'>{n}</span>" for n in r])
            text_copy = " ".join([str(n) for n in r])
            
        sets.append({"name": algo['name'], "html": html, "text": text_copy, "is_vip": algo['vip']})
    return sets

# --- 5. 界面框架 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 商业决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

# 🔥 侧边栏收钱区
st.sidebar.markdown("""
    <div class="wechat-box">
        <span style="font-size:14px; color:#666;">获取核心【VIP内部号】</span><br>
        <b style="color:#ff4b4b; font-size:18px;">微信: 这里填微信号</b><br>
        <span style="font-size:12px; color:#999;">(支付29.9元解锁全站永久权限)</span>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
if st.sidebar.button("🧹 清理缓存急救", type="primary"):
    st.cache_data.clear()
    st.rerun()

file_kw = LOTTERY_FILES[choice]
all_files = [f for f in os.listdir(".") if file_kw in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))]
target = next((f for f in all_files if '_synced' in f), all_files[0] if all_files else None)

if target:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target, choice)
    if df is not None:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🗓️ 分析设置")
        view_options = {"近30期": 30, "近50期": 50, "近100期": 100}
        view_choice = st.sidebar.radio("选择分析样本", list(view_options.keys()), index=1)
        view_limit = view_options[view_choice]

        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**库中最新：** `{int(df[q_col].max())}`")
        if st.sidebar.button("🔄 联网同步", use_container_width=True):
            sync_latest_data(df, q_col, d_cols, choice, actual_path)

        # 倒计时
        st.markdown(f'<div class="timer-bar">⏰ 离今日开奖截止还剩 {get_countdown()} | 系统已开启高负载运算模式</div>', unsafe_allow_html=True)

        st.title(f"🎰 {choice} 数据智算中心")
        
        # 📢 插入动态跑马灯
        broadcast_str = get_fake_broadcasts(choice)
        st.markdown(f"""
        <div class="marquee-wrapper">
            <div class="marquee-icon">📢</div>
            <div class="marquee-content">{broadcast_str}</div>
        </div>
        """, unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["📜 历史数据", "📈 深度走势", "🤖 AI 演算", "💬 交流大厅"])
        
        with t1:
            # 🔥 新增：付费下载引流区
            st.markdown("""
            <div class="download-lock">
                <span style="font-weight:bold; color:#f14545;">🔒 付费提取通道</span><br>
                <span style="font-size:13px; color:#666;">支付 <b>19.9元</b> 即可一键导出该彩种近 500 期完整 Excel 历史数据，请联系左侧客服获取。</span>
            </div>
            """, unsafe_allow_html=True)
            
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(view_limit).iterrows():
                balls_html = ""
                for i, col in enumerate(d_cols):
                    val = row[col]
                    txt = f"{val:02d}" if needs_zero else str(val)
                    bg = "bg-red"
                    if choice == "双色球": bg = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": bg = "bg-yellow" if i >= 5 else "bg-blue"
                    elif choice == "七星彩": bg = "bg-yellow" if i == 6 else "bg-purple"
                    elif choice in ["排列3", "排列5", "福彩3D"]: bg = "bg-purple"
                    balls_html += f"<span class='ball {bg}'>{txt}</span>"
                    if choice == "快乐8" and i == 9: balls_html += "<br>"
                try: display_q = int(float(row[q_col]))
                except: display_q = row[q_col]
                table_html += f"<tr><td><b>{display_q}</b></td><td>{balls_html}</td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)
            
        with t2:
            st.markdown("### 📊 和值趋势与均线分析")
            calc_df = df.head(view_limit).copy()
            calc_df['和值'] = calc_df[d_cols].sum(axis=1)
            plot_df = calc_df.sort_values(q_col).set_index(q_col)
            plot_df['5期均值 (MA5)'] = plot_df['和值'].rolling(window=5, min_periods=1).mean()
            st.line_chart(plot_df[['和值', '5期均值 (MA5)']])
            
            st.markdown("### 🔥 冷热号码频次分布图")
            st.caption(f"统计范围：当前选定的 {view_choice} 数据")
            all_nums = calc_df[d_cols].values.flatten()
            counter = Counter(all_nums)
            freq_df = pd.DataFrame(list(counter.items()), columns=['号码', '出现次数']).sort_values('号码')
            freq_df['号码'] = freq_df['号码'].astype(str)
            st.bar_chart(freq_df.set_index('号码'))

        with t3:
            st.info(f"💡 提示：当前 AI 已锁定「{view_choice}」的真实历史频率进行演算拟合。")
            if st.button("🚀 启动 AI 深度演算 (生成最新策略)", use_container_width=True):
                with st.spinner('AI 正在调取蒙特卡洛树计算引擎...'): time.sleep(1)
                
                # 🔥 调用真·数据联动预测函数
                predictions = get_real_prediction(df.head(view_limit), d_cols, choice)
                
                for p in predictions:
                    if p['is_vip']:
                        st.markdown(f"""
                        <div class='pred-row'>
                            <div class='pred-title'>{p['name']}</div>
                            <div class='pred-balls vip-locked'>{p['html']}</div>
                            <div class='lock-overlay'>🔓 仅限VIP · 联系客服领号</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class='pred-row'>
                            <div class='pred-title'>{p['name']}</div>
                            <div class='pred-balls'>{p['html']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.code(f"【{choice}】{p['name']} 推荐号码: {p['text']}", language="markdown")
        
        with t4:
            st.markdown("### 🏆 彩民实战交流区")
            st.caption("分享您的实战心得，与全国彩友一起探讨走势规律！")
            
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
            user_input = st.text_input("💡 留下您的看法...")
            if st.button("发布评论", type="primary"):
                if user_input:
                    st.session_state.comments.insert(0, {
                        "user": "📱 当前用户 (我)",
                        "text": user_input,
                        "time": "刚刚"
                    })
                    st.rerun()
                else:
                    st.warning("请先输入评论内容哦！")
                    
    else: st.error("数据加载失败。如果您刚才遇到了报错，请点击左侧红色的【清理缓存急救】按钮。")
else: st.error(f"未找到 {choice} 的数据文件。")

# --- 6. 官方免责声明 (保持不动) ---
st.markdown("""
    <div class="legal-footer">
        <b>免责声明</b><br>
        本系统提供的数据统计、走势分析及 AI 算法生成的预测结果，仅供彩票爱好者交流、学习和娱乐参考。<br>
        <b>本工具不构成任何形式的购彩或投资建议。</b><br>
        彩市有风险，购彩需谨慎。请根据自身经济能力理性购彩，严禁未满 18 周岁的未成年人购买彩票。<br>
        © 2024 AI 智算决策中心. All Rights Reserved.
    </div>
""", unsafe_allow_html=True)
