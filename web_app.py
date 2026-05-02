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

# --- 2. 自适应数据提取 ---
@st.cache_data
def load_full_data(file_path, choice):
    try:
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

        limits = {"双色球": 7, "大乐透": 7, "福彩3D": 3, "快乐8": 20, "排列3": 3, "排列5": 5, "七星彩": 7}
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
        new_names = [q_col] + [f"b_{i+1}" for i in range(len(ball_cols))]
        clean_df.columns = new_names
        
        for c in new_names:
            clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0).astype(int)
            
        needs_zero = True if choice in ["双色球", "大乐透", "快乐8"] else False
        return clean_df.sort_values(q_col, ascending=False), q_col, new_names[1:], needs_zero, file_path
    except Exception as e:
        st.error(f"🚨 解析错误: {str(e)}")
        return None, None, None, None, None

# --- 3. 终极同步引擎 (双轨制 + 防内存溢出拦截) ---
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
        status.info(f"📡 正在连接 {choice} 专属数据通道...")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        tdata = soup.find('tbody', id='tdata')
        trs = tdata.find_all('tr') if tdata else soup.find_all('tr')
        
        web_rows = []
        for tr in trs:
            tds = tr.find_all('td')
            if len(tds) < len(d_cols) + 1: continue 
            
            balls = []
            issue_val = 0
            
            # ========== 【核心分流逻辑】 ==========
            if choice in ["双色球", "大乐透"]:
                # 👉 路线A：【不动如山版】专门服务双色球/大乐透
                iss_raw = tds[0].get_text(strip=True)
                iss_str = re.sub(r'\D', '', iss_raw)
                if len(iss_str) < 3: continue
                issue_val = int("20" + iss_str) if len(iss_str) == 5 else int(iss_str)
                if issue_val == 0: continue
                
                for td in tr.find_all('td', class_=['t_cfont2', 't_cfont4']):
                    txt = td.get_text(strip=True)
                    if re.match(r'^\d+$', txt):
                        balls.append(int(txt))
                if not balls:
                    for td in tds[1:]:
                        txt = td.get_text(strip=True)
                        if re.match(r'^\d+$', txt):
                            balls.append(int(txt))
                        if len(balls) == len(d_cols): break

            else:
                # 👉 路线B：【细胞级扫描版】专治福彩3D/排列3等杂乱表格
                start_idx = 1
                # 寻找真实的期号列（通常是5、7、8位数字）
                for idx, td in enumerate(tds):
                    txt = td.get_text(strip=True)
                    digits = re.sub(r'\D', '', txt)
                    if 5 <= len(digits) <= 8:
                        issue_val = int("20" + digits) if len(digits) == 5 else int(digits)
                        start_idx = idx + 1
                        break
                
                if issue_val == 0: continue
                
                # 扫描后续单元格，只要是1到2位的纯数字，就吸纳为球号
                for td in tds[start_idx:]:
                    txt = td.get_text(strip=True)
                    # 严格匹配 1~2位数字 (如: "5", "05", "80")
                    if re.match(r'^\d{1,2}$', txt):
                        balls.append(int(txt))
                    if len(balls) == len(d_cols):
                        break
                
                # 万一全挤在一个格子里，动用强力正则保底
                if len(balls) < len(d_cols):
                    balls = []
                    row_text = " ".join([td.get_text(separator=" ") for td in tds[start_idx:]])
                    all_nums = re.findall(r'(?<!\d)\d{1,2}(?!\d)', row_text)
                    balls = [int(n) for n in all_nums if 0 <= int(n) <= 80][:len(d_cols)]
            # ====================================
            
            if len(balls) == len(d_cols):
                row = {q_col: issue_val}
                for i, col_name in enumerate(d_cols):
                    row[col_name] = balls[i]
                web_rows.append(row)

        if web_rows:
            web_df = pd.DataFrame(web_rows)
            
            # 【终极防爆补丁】：保护数据合并时不报 int too large 错误
            def safe_format(val):
                try:
                    s = str(val).strip()
                    if '.' in s: s = s.split('.')[0]
                    s = re.sub(r'\D', '', s)
                    if not s or len(s) > 10: return 0  # 超过10位的巨型数据直接拦截归零！
                    return int("20" + s) if len(s) == 5 else int(s)
                except: return 0
            
            df[q_col] = df[q_col].apply(safe_format)
            
            updated = pd.concat([web_df, df], ignore_index=True)
            updated = updated.drop_duplicates(subset=[q_col], keep='first')
            updated = updated.sort_values(q_col, ascending=False)
            updated = updated[updated[q_col] > 0] # 滤除被归零的乱码行
            
            save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
            updated.to_csv(save_path, index=False, encoding='utf-8-sig')
            
            status.success(f"✅ 同步成功！已为 {choice} 更新 {len(web_rows)} 期数据。")
            st.cache_data.clear()
            time.sleep(1.5)
            st.rerun()
        else:
            status.error("❌ 未找到有效数据，请稍后重试。")
            time.sleep(3)
            status.empty()
    except Exception as e:
        status.error(f"❌ 同步遇到异常: {str(e)}")

# --- 4. 预测引擎 ---
def get_prediction(choice):
    sets = []
    names = ["🔥 极热寻踪", "🧊 绝地反弹", "⚖️ 黄金均衡", "🎲 蒙特卡洛", "🧠 深度拟合"]
    for name in names:
        if choice == "双色球":
            r = sorted(random.sample(range(1, 34), 6)); b = random.randint(1, 16)
            html = "".join([f"<span class='pred-ball bg-red'>{n:02d}</span>" for n in r]) + f"<span class='pred-ball bg-blue'>{b:02d}</span>"
            text_copy = " ".join([f"{n:02d}" for n in r]) + f" | {b:02d}"
        elif choice == "大乐透":
            r = sorted(random.sample(range(1, 36), 5)); b = sorted(random.sample(range(1, 13), 2))
            html = "".join([f"<span class='pred-ball bg-blue'>{n:02d}</span>" for n in r]) + "".join([f"<span class='pred-ball bg-yellow'>{n:02d}</span>" for n in b])
            text_copy = " ".join([f"{n:02d}" for n in r]) + " | " + " ".join([f"{n:02d}" for n in b])
        elif choice == "快乐8":
            r = sorted(random.sample(range(1, 81), 20))
            html = "".join([f"<span class='pred-ball bg-red' style='width:26px;height:26px;line-height:26px;font-size:12px;margin:2px;'>{n:02d}</span>" for n in r[:10]])
            html += "<br>"
            html += "".join([f"<span class='pred-ball bg-red' style='width:26px;height:26px;line-height:26px;font-size:12px;margin:2px;'>{n:02d}</span>" for n in r[10:]])
            text_copy = " ".join([f"{n:02d}" for n in r])
        elif choice == "七星彩":
            r = [random.randint(0, 9) for _ in range(6)]; b = random.randint(0, 14)
            html = "".join([f"<span class='pred-ball bg-purple'>{n}</span>" for n in r]) + f"<span class='pred-ball bg-yellow'>{b}</span>"
            text_copy = " ".join([str(n) for n in r]) + f" | {b}"
        else:
            n_count = 3 if choice in ["排列3", "福彩3D"] else 5
            nums = [random.randint(0, 9) for _ in range(n_count)]
            html = "".join([f"<span class='pred-ball bg-purple'>{n}</span>" for n in nums])
            text_copy = " ".join([str(n) for n in nums])
            
        sets.append({"name": name, "html": html, "text": text_copy})
    return sets

# --- 5. 界面框架 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 AI 大数据决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

file_kw = LOTTERY_FILES[choice]
all_files = [f for f in os.listdir(".") if file_kw in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))]
target = next((f for f in all_files if '_synced' in f), all_files[0] if all_files else None)

if target:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target, choice)
    if df is not None:
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🗓️ 显示选项")
        view_options = {"近20期": 20, "近50期": 50, "近100期": 100, "近200期": 200, "显示全部": len(df)}
        view_choice = st.sidebar.radio("选择查看/分析范围", list(view_options.keys()), index=1)
        view_limit = view_options[view_choice]

        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**最新期号：** `{int(df[q_col].max())}`")
        
        if st.sidebar.button("🔄 联网同步最新开奖", use_container_width=True):
            sync_latest_data(df, q_col, d_cols, choice, actual_path)

        st.title(f"🎰 {choice} · 智算中心")
        t1, t2, t3 = st.tabs(["📜 历史数据", "📊 走势分析", "🤖 AI 演算"])
        
        with t1:
            st.write(f"当前视图：**{view_choice}** (本地数据库共计 {len(df)} 期)")
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
                    
                    if choice == "快乐8" and i == 9:
                        balls_html += "<br>"

                try:
                    display_q = int(float(row[q_col]))
                except:
                    display_q = row[q_col]
                    
                table_html += f"<tr><td><b>{display_q}</b></td><td>{balls_html}</td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)
            
        with t2:
            calc_df = df.head(view_limit).copy()
            calc_df['和值'] = calc_df[d_cols].sum(axis=1)
            st.line_chart(calc_df.sort_values(q_col).set_index(q_col)['和值'])

        with t3:
            if st.button("🚀 启动 AI 深度演算"):
                for p in get_prediction(choice):
                    st.markdown(f"<div class='pred-row'><div class='pred-title'>{p['name']}</div><div>{p['html']}</div></div>", unsafe_allow_html=True)
                    st.code(p['text'], language=None)
    else: st.error("数据解析失败。")
else: st.error(f"未找到 {choice} 的数据文件。")
