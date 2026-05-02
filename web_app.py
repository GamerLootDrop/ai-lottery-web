import streamlit as st
import pandas as pd
import os
import time
import random
import requests
from bs4 import BeautifulSoup
import re

# --- 1. 深度定制样式表 ---
st.set_page_config(page_title="AI 大数据决策终端", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 1.5rem !important; max-width: 900px; }
    .hist-table { width: 100%; border-collapse: collapse; text-align: center; background: #fff; border-radius: 8px; overflow: hidden; margin-bottom: 1rem; }
    .hist-table th { background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #eaeaea; color: #666; font-weight: bold; }
    .hist-table td { padding: 12px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 15px; }
    .ball { display: inline-block; width: 28px; height: 28px; line-height: 28px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 3px; font-size: 13px; text-align: center; }
    .bg-red { background-color: #f14545; }
    .bg-blue { background-color: #3b71f7; }
    .bg-yellow { background-color: #f9bf15; color: #333 !important; }
    .bg-purple { background-color: #9c27b0; }
    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 5px; border-left: 5px solid #f14545; display: flex; align-items: center; }
    .pred-title { width: 140px; font-weight: bold; color: #444; }
    .pred-ball { display: inline-block; width: 34px; height: 34px; line-height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 4px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 自适应数据提取 (✅ 已完全回退至最稳定、不挑文件的读取逻辑) ---
@st.cache_data
def load_full_data(file_path, choice):
    try:
        raw_df = pd.read_excel(file_path) if file_path.endswith('.xls') else pd.read_csv(file_path)
        if raw_df.empty: return None, None, None, None, None
        raw_df.columns = [str(c).strip() for c in raw_df.columns]
        
        q_col = next((c for c in raw_df.columns if '期' in c or 'NO' in c.upper()), raw_df.columns[0])
        
        limits = {"双色球": 7, "大乐透": 7, "福彩3D": 3, "快乐8": 20, "排列3": 3, "排列5": 5, "七星彩": 7}
        max_balls = limits.get(choice, 7)
        
        q_idx = list(raw_df.columns).index(q_col)
        ball_cols = []
        for i in range(q_idx + 1, len(raw_df.columns)):
            col = raw_df.columns[i]
            # 恢复最原始的判断：只要列里面是数字就行，不再强行限制大小导致本地数据被跳过
            nums = pd.to_numeric(raw_df[col], errors='coerce').dropna()
            if not nums.empty:
                ball_cols.append(col)
            if len(ball_cols) == max_balls: break

        clean_df = raw_df[[q_col] + ball_cols].copy()
        new_names = [q_col] + [f"b_{i+1}" for i in range(len(ball_cols))]
        clean_df.columns = new_names
        
        for c in new_names:
            clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0)
            
        needs_zero = True if choice in ["双色球", "大乐透", "快乐8"] else False
        return clean_df.sort_values(q_col, ascending=False), q_col, new_names[1:], needs_zero, file_path
    except Exception as e:
        st.error(f"🚨 解析错误: {str(e)}")
        return None, None, None, None, None

# --- 3. 终极同步引擎 (✅ 纯净正则降维打击，无视网页排版) ---
def sync_latest_data(df, q_col, d_cols, choice, file_path):
    status = st.empty()
    url_map = {
        "双色球": "https://datachart.500.com/ssq/history/newinc/history.php?limit=50",
        "大乐透": "https://datachart.500.com/dlt/history/newinc/history.php?limit=50",
        "福彩3D": "https://datachart.500.com/sd/history/inc/history.php?limit=50",
        "排列3": "https://datachart.500.com/pls/history/inc/history.php?limit=50",
        "排列5": "https://datachart.500.com/plw/history/inc/history.php?limit=50",
        "七星彩": "https://datachart.500.com/qxc/history/inc/history.php?limit=50",
        "快乐8": "https://datachart.500.com/kl8/history/inc/history.php?limit=50"
    }
    
    try:
        url = url_map.get(choice)
        status.info(f"📡 正在拉取 {choice} 最新数据...")
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        trs = soup.find('tbody', id='tdata').find_all('tr') if soup.find('tbody', id='tdata') else soup.find_all('tr')
        web_rows = []
        
        for tr in trs:
            tds = tr.find_all('td')
            if len(tds) < 4: continue
            
            # 1. 寻找当行真实的期号
            issue_val = 0
            start_idx = 1
            for idx, td in enumerate(tds):
                txt = td.get_text(strip=True)
                digits = re.sub(r'\D', '', txt)
                if 3 <= len(digits) <= 8 and int(digits) > 100:
                    issue_val = int("20" + digits) if len(digits) == 5 else int(digits)
                    start_idx = idx + 1
                    break
            
            if issue_val == 0: continue

            # 2. 抓取球号（不同彩种分而治之）
            balls = []
            
            if choice in ["双色球", "大乐透"]:
                # 您的金标准：原封不动
                for td in tr.find_all('td', class_=['t_cfont2', 't_cfont4']):
                    v = re.sub(r'\D', '', td.get_text(strip=True))
                    if v: balls.append(int(v))
            else:
                # 把剩下的所有内容变成纯文本
                rest_text = " ".join([td.get_text(separator=' ') for td in tds[start_idx:]])
                
                if choice == "快乐8":
                    # 只找 1~2位 且在 1-80 范围内的数字
                    nums = re.findall(r'(?<!\d)\d{1,2}(?!\d)', rest_text)
                    balls = [int(n) for n in nums if 1 <= int(n) <= 80][:20]
                else:
                    # 3D、P3、P5、七星彩：只找“落单的” 1 位纯数字 (直接免疫和值 100 等干扰)
                    nums = re.findall(r'(?<!\d)\d(?!\d)', rest_text)
                    balls = [int(n) for n in nums][:len(d_cols)]
            
            # 如果抓齐了，就塞进表里
            if len(balls) == len(d_cols):
                row = {q_col: issue_val}
                for i, col_name in enumerate(d_cols): row[col_name] = balls[i]
                web_rows.append(row)

        if web_rows:
            web_df = pd.DataFrame(web_rows)
            # 安全防爆转码
            def fmt_q(v):
                try:
                    s = re.sub(r'\D', '', str(v).split('.')[0])
                    return int(s) if s and len(s) < 10 else 0
                except: return 0
            df[q_col] = df[q_col].apply(fmt_q)
            
            # 把网上的正确数据放前面合并，利用 drop_duplicates 自动清洗掉之前损坏的零值
            updated = pd.concat([web_df, df], ignore_index=True)
            updated = updated.drop_duplicates(subset=[q_col], keep='first')
            updated = updated[updated[q_col] > 0].sort_values(q_col, ascending=False)
            
            save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
            updated.to_csv(save_path, index=False, encoding='utf-8-sig')
            
            status.success(f"✅ {choice} 同步完成！更新/修复了 {len(web_rows)} 期数据。")
            st.cache_data.clear()
            time.sleep(1.5)
            st.rerun()
        else:
            status.error("❌ 页面结构解析失败，未找到对应号码。")
            time.sleep(2); status.empty()
    except Exception as e:
        status.error(f"❌ 异常: {str(e)}")

# --- 4. 预测引擎 ---
def get_prediction(choice):
    sets = []
    for name in ["🔥 极热寻踪", "🧊 绝地反弹", "⚖️ 黄金均衡", "🎲 蒙特卡洛", "🧠 深度拟合"]:
        if choice == "双色球":
            r, b = sorted(random.sample(range(1, 34), 6)), random.randint(1, 16)
            html = "".join([f"<span class='pred-ball bg-red'>{n:02d}</span>" for n in r]) + f"<span class='pred-ball bg-blue'>{b:02d}</span>"
            txt = " ".join([f"{n:02d}" for n in r]) + f" | {b:02d}"
        elif choice == "大乐透":
            r, b = sorted(random.sample(range(1, 36), 5)), sorted(random.sample(range(1, 13), 2))
            html = "".join([f"<span class='pred-ball bg-blue'>{n:02d}</span>" for n in r]) + "".join([f"<span class='pred-ball bg-yellow'>{n:02d}</span>" for n in b])
            txt = " ".join([f"{n:02d}" for n in r]) + " | " + " ".join([f"{n:02d}" for n in b])
        elif choice == "快乐8":
            r = sorted(random.sample(range(1, 81), 20))
            html = "".join([f"<span class='pred-ball bg-red' style='width:24px;height:24px;line-height:24px;font-size:11px;margin:1px;'>{n:02d}</span>" for n in r])
            txt = " ".join([f"{n:02d}" for n in r])
        else:
            n_count = {"福彩3D":3, "排列3":3, "排列5":5, "七星彩":7}.get(choice, 3)
            res = [random.randint(0, 9) for _ in range(n_count)]
            html = "".join([f"<span class='pred-ball bg-purple'>{n}</span>" for n in res])
            txt = " ".join([str(n) for n in res])
        sets.append({"name": name, "html": html, "text": txt})
    return sets

# --- 5. 主逻辑 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 AI 决策终端")
choice = st.sidebar.selectbox("🎯 实战彩种", list(LOTTERY_FILES.keys()))

all_f = [f for f in os.listdir(".") if LOTTERY_FILES[choice] in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))]
target = next((f for f in all_f if '_synced' in f), all_f[0] if all_f else None)

if target:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target, choice)
    if df is not None:
        st.sidebar.button("🔄 联网同步最新开奖", on_click=sync_latest_data, args=(df, q_col, d_cols, choice, actual_path), use_container_width=True)
        
        st.title(f"🎰 {choice}")
        t1, t2, t3 = st.tabs(["📜 历史数据", "📊 分析", "🤖 AI 演算"])
        with t1:
            limit = st.slider("查看期数", 10, len(df), 20)
            table = "<table class='hist-table'><tr><th>期号</th><th>中奖号码</th></tr>"
            for _, r in df.head(limit).iterrows():
                balls = ""
                for i, col in enumerate(d_cols):
                    # 【核心防错处理】：不论源数据多脏，全部强转为整数再排版，杜绝格式崩溃！
                    try:
                        v = int(float(r[col]))
                    except:
                        v = 0
                    
                    txt = f"{v:02d}" if needs_zero else str(v)
                    
                    bg = "bg-red"
                    if choice == "双色球": bg = "bg-blue" if i==6 else "bg-red"
                    elif choice == "大乐透": bg = "bg-yellow" if i>=5 else "bg-blue"
                    elif choice == "七星彩": bg = "bg-yellow" if i == 6 else "bg-purple"
                    elif choice in ["福彩3D","排列3","排列5"]: bg = "bg-purple"
                    
                    balls += f"<span class='ball {bg}'>{txt}</span>"
                    if choice == "快乐8" and i == 9: balls += "<br>" # 快乐8换行显示美化
                
                try:
                    display_q = int(float(r[q_col]))
                except:
                    display_q = r[q_col]
                    
                table += f"<tr><td><b>{display_q}</b></td><td>{balls}</td></tr>"
            st.markdown(table + "</table>", unsafe_allow_html=True)
        with t2:
            st.line_chart(df.head(50).set_index(q_col)[d_cols[0]])
        with t3:
            if st.button("🚀 启动演算"):
                for p in get_prediction(choice):
                    st.markdown(f"<div class='pred-row'><div class='pred-title'>{p['name']}</div><div>{p['html']}</div></div>", unsafe_allow_html=True)
                    st.code(p['text'])
else:
    st.error(f"未找到 {choice} 的数据文件，请检查文件名是否包含 '{LOTTERY_FILES[choice]}'")
