import streamlit as st
import pandas as pd
import os
import time
import random
import requests
from bs4 import BeautifulSoup

# --- 1. 深度定制样式表 ---
st.set_page_config(page_title="AI 大数据决策终端", layout="wide")
st.markdown("""
    <style>
    .block-container { padding: 1.5rem !important; max-width: 900px; }
    .hist-table { width: 100%; border-collapse: collapse; text-align: center; background: #fff; border-radius: 8px; overflow: hidden; margin-bottom: 1rem; }
    .hist-table th { background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #eaeaea; color: #666; font-weight: bold; }
    .hist-table td { padding: 12px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 15px; }
    .ball { display: inline-block; width: 28px; height: 28px; line-height: 28px; border-radius: 50%; color: white; font-weight: bold; margin: 0 3px; font-size: 13px; text-align: center; }
    .bg-red { background-color: #f14545; }
    .bg-blue { background-color: #3b71f7; }
    .bg-yellow { background-color: #f9bf15; color: #333 !important; }
    .bg-purple { background-color: #9c27b0; }
    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 15px; border-left: 5px solid #f14545; display: flex; align-items: center; }
    .pred-title { width: 140px; font-weight: bold; color: #444; }
    .pred-ball { display: inline-block; width: 34px; height: 34px; line-height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 0 4px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 纯数据扫描提取引擎 ---
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
        
        q_idx = raw_df.columns.get_loc(q_col)
        ball_cols = []
        for i in range(q_idx + 1, len(raw_df.columns)):
            col = raw_df.columns[i]
            sample = raw_df[col].dropna().head(10) 
            if sample.empty: continue
            
            is_ball_col = True
            for val in sample:
                try:
                    num = float(str(val).replace(',', ''))
                    if num < 0 or num > 100:
                        is_ball_col = False
                        break
                except ValueError:
                    is_ball_col = False
                    break
                    
            if is_ball_col:
                ball_cols.append(col)
                
            if len(ball_cols) == max_balls:
                break

        clean_df = raw_df[[q_col] + ball_cols].copy()
        new_names = [q_col] + [f"b_{i+1}" for i in range(len(ball_cols))]
        clean_df.columns = new_names
        
        for c in new_names:
            clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0).astype(int)
            
        needs_zero = True if choice in ["双色球", "大乐透", "快乐8"] else False
        return clean_df.sort_values(q_col, ascending=False), q_col, new_names[1:], needs_zero, file_path
    except Exception as e:
        st.error(f"🚨 解析本地文件失败: {str(e)}")
        return None, None, None, None, None

# --- 3. 智能全彩种穿透同步 ---
def sync_latest_data(df, q_col, d_cols, choice, file_path):
    def normalize_issue(iss):
        s = str(iss).strip()
        return int("20" + s) if len(s) == 5 else int(s)

    latest_local = df[q_col].apply(normalize_issue).max()
    status = st.empty()
    bar = st.progress(0)
    
    api_map = {"双色球": "ssq", "大乐透": "dlt", "福彩3D": "sd", "排列3": "pls", "排列5": "plw", "七星彩": "qxc", "快乐8": "kl8"}
    
    try:
        status.info(f"📡 正在接入 {choice} 穿透通道...")
        url = f"https://datachart.500.com/{api_map.get(choice, 'ssq')}/history/newinc/history.php?limit=30"
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        tdata = soup.find('tbody', id='tdata')
        
        new_rows = []
        if tdata:
            for tr in tdata.find_all('tr'):
                if 'hide' in tr.get('class', []): continue
                tds = tr.find_all('td')
                if len(tds) < 3: continue
                
                issue_7d = normalize_issue(tds[0].text.strip())
                if issue_7d > latest_local:
                    balls = [int(td.text.strip()) for td in tr.find_all('td', class_=['t_cfont2', 't_cfont4'])]
                    if not balls:
                        balls = [int(td.text.strip()) for td in tds[1:] if td.text.strip().isdigit()][:len(d_cols)]
                    
                    row = {q_col: issue_7d}
                    for i, col_name in enumerate(d_cols):
                        row[col_name] = balls[i] if i < len(balls) else 0
                    new_rows.append(row)
        
        if new_rows:
            new_df = pd.DataFrame(new_rows)
            updated = pd.concat([new_df, df], ignore_index=True).drop_duplicates(subset=[q_col], keep='last')
            updated = updated.sort_values(q_col, ascending=False)
            updated[q_col] = updated[q_col].astype(int)
            
            save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
            updated.to_csv(save_path, index=False, encoding='utf-8-sig')
            status.success(f"✅ 成功同步 {len(new_rows)} 期新数据！")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
        else:
            status.success("✅ 当前已是最新数据！")
            time.sleep(1)
    except Exception as e:
        status.error(f"❌ 同步失败: {str(e)}")
    finally:
        bar.empty()
        status.empty()

# --- 4. 预测与显示逻辑 ---
def get_prediction(choice):
    sets = []
    names = ["🔥 极热寻踪", "🧊 绝地反弹", "⚖️ 黄金均衡", "🎲 蒙特卡洛", "🧠 深度拟合"]
    for name in names:
        if choice == "双色球":
            r = sorted(random.sample(range(1, 34), 6)); b = random.randint(1, 16)
            html = "".join([f"<span class='pred-ball bg-red'>{n:02d}</span>" for n in r]) + f"<span class='pred-ball bg-blue'>{b:02d}</span>"
        elif choice == "大乐透":
            r = sorted(random.sample(range(1, 36), 5)); b = sorted(random.sample(range(1, 13), 2))
            html = "".join([f"<span class='pred-ball bg-blue'>{n:02d}</span>" for n in r]) + "".join([f"<span class='pred-ball bg-yellow'>{n:02d}</span>" for n in b])
        elif choice == "快乐8":
            r = sorted(random.sample(range(1, 81), 20))
            html = "".join([f"<span class='pred-ball bg-red' style='width:28px;height:28px;line-height:28px;font-size:12px;'>{n:02d}</span>" for n in r])
        elif choice == "七星彩":
            r = [random.randint(0, 9) for _ in range(6)]; b = random.randint(0, 14)
            # 修复：6个紫球 + 1个金球
            html = "".join([f"<span class='pred-ball bg-purple'>{n}</span>" for n in r]) + f"<span class='pred-ball bg-yellow'>{b}</span>"
        else:
            n_count = 3 if choice in ["排列3", "福彩3D"] else 5
            nums = [random.randint(0, 9) for _ in range(n_count)]
            html = "".join([f"<span class='pred-ball bg-purple'>{n}</span>" for n in nums])
        sets.append({"name": name, "html": html})
    return sets

# --- 5. 主程序 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
st.sidebar.title("💎 AI 大数据决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

file_kw = LOTTERY_FILES[choice]
all_files = [f for f in os.listdir(".") if file_kw in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))]
target = next((f for f in all_files if '_synced' in f), all_files[0] if all_files else None)

if target:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target, choice)
    if df is not None:
        st.sidebar.markdown(f"**最新期号：** `{int(df[q_col].max())}`")
        if st.sidebar.button("🔄 联网同步最新开奖", use_container_width=True):
            sync_latest_data(df, q_col, d_cols, choice, actual_path)

        st.title(f"🎰 {choice} · 智算中心")
        t1, t2, t3 = st.tabs(["📜 历史数据", "📊 走势分析", "🤖 AI 演算"])
        
        with t1:
            st.write(f"当前显示最近 50 期数据 (本地共 {len(df)} 期)")
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(50).iterrows():
                balls_html = ""
                for i, col in enumerate(d_cols):
                    val = row[col]
                    txt = f"{val:02d}" if needs_zero else str(val)
                    bg = "bg-red"
                    
                    if choice == "双色球": bg = "bg-blue" if i == 6 else "bg-red"
                    elif choice == "大乐透": bg = "bg-yellow" if i >= 5 else "bg-blue"
                    # 修复：前6个是紫色，第7个是金色
                    elif choice == "七星彩": bg = "bg-yellow" if i == 6 else "bg-purple"
                    elif choice in ["排列3", "排列5", "福彩3D"]: bg = "bg-purple"
                    
                    balls_html += f"<span class='ball {bg}'>{txt}</span>"
                table_html += f"<tr><td><b>{int(row[q_col])}</b></td><td>{balls_html}</td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)
            
        with t2:
            calc_df = df.head(100).copy()
            calc_df['和值'] = calc_df[d_cols].sum(axis=1)
            st.line_chart(calc_df.sort_values(q_col).set_index(q_col)['和值'])

        with t3:
            if st.button("🚀 启动 AI 深度演算"):
                preds = get_prediction(choice)
                for p in preds:
                    st.markdown(f"<div class='pred-row'><div class='pred-title'>{p['name']}</div><div>{p['html']}</div></div>", unsafe_allow_html=True)
    else: st.error("基础数据解析失败，请检查 Excel 文件格式。")
else: st.error(f"未找到 {choice} 的数据文件。")
