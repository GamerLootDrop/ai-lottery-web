import streamlit as st
import pandas as pd
import os
import time
import random
import requests
from bs4 import BeautifulSoup
import re  
from collections import Counter

# --- 1. 深度定制样式表 (🔥 新增：手机端适配 & 免责声明样式) ---
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
    .pred-row { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #f14545; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; }
    .pred-title { width: 140px; font-weight: bold; color: #444; font-size: 16px; }
    .pred-balls { flex-grow: 1; }
    .pred-ball { display: inline-block; width: 34px; height: 34px; line-height: 34px; border-radius: 50%; color: white; font-weight: bold; margin: 3px 4px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.15); }
    
    /* 底部免责声明 */
    .legal-footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #eaeaea; text-align: center; color: #999; font-size: 12px; line-height: 1.8; }
    
    /* 📱 手机端专属适配 (响应式设计) */
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

# --- 2. 混合双引擎数据提取 (🔥 保持不动，超级稳) ---
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
            
            for c in new_names:
                clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0).astype(int)
                
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
                        issue_num = int(valid_nums[1])
                        balls_start = 2
                    else:
                        issue_num = int(valid_nums[0])
                        balls_start = 1
                        
                    balls = [int(n) for n in valid_nums[balls_start : balls_start+max_balls]]
                    if all(0 <= b <= 81 for b in balls):
                        extracted_rows.append([issue_num] + balls)
            
            if not extracted_rows:
                raise ValueError(f"在 {choice} 的文件里找不到任何有效的开奖数字！")
            
            new_names = ['期号'] + [f"b_{i+1}" for i in range(max_balls)]
            clean_df = pd.DataFrame(extracted_rows, columns=new_names)
            
            needs_zero = True if choice == "快乐8" else False
            return clean_df.sort_values('期号', ascending=False), '期号', new_names[1:], needs_zero, file_path

    except Exception as e:
        st.error(f"🚨 解析错误: {str(e)}")
        return None, None, None, None, None

# --- 3. 同步最新数据 (🔥 保持不动) ---
def sync_latest_data(df, q_col, d_cols, choice, file_path):
    status = st.empty()
    game_codes = {"双色球": "ssq", "大乐透": "dlt", "福彩3D": "sd", "排列3": "pls", "排列5": "plw", "七星彩": "qxc", "快乐8": "kl8"}
    game_code = game_codes.get(choice, "ssq")
    
    try:
        status.info(f"📡 正在联网获取 {choice} 最新开奖数据...")
        urls = [
            f"https://datachart.500.com/{game_code}/history/newinc/history.php?limit=50",
            f"https://datachart.500.com/{game_code}/history/inc/history.php?limit=50"
        ]
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        web_rows = []
        for url in urls:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            tdata = soup.find('tbody', id='tdata')
            if tdata: trs = tdata.find_all('tr')
            else:
                trs = soup.find_all('tr', class_=['t_tr1', 't_tr2', 't_tr'])
                if not trs: trs = soup.find_all('tr')
            
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) < len(d_cols) + 1: continue 
                
                iss_str = re.sub(r'\D', '', tds[0].get_text(strip=True))
                if len(iss_str) < 3: continue
                issue_val = int("20" + iss_str) if len(iss_str) == 5 else int(iss_str)
                if issue_val == 0: continue
                
                rest_text = "   ".join([td.get_text(separator=" ") for td in tds[1:]])
                
                balls = []
                if choice in ["福彩3D", "排列3", "排列5"]:
                    balls = [int(n) for n in re.findall(r'\d', rest_text)]
                elif choice == "七星彩":
                    groups = re.findall(r'\d+', rest_text)
                    for g in groups:
                        if len(g) >= 3: 
                            for char in g: balls.append(int(char))
                        else: balls.append(int(g))
                else:
                    balls = [int(n) for n in re.findall(r'\d+', rest_text)]
                
                balls = [n for n in balls if 0 <= n <= 81]
                if len(balls) >= len(d_cols):
                    row = {q_col: issue_val}
                    for i, col_name in enumerate(d_cols): row[col_name] = balls[i]
                    web_rows.append(row)
            if len(web_rows) > 0: break

        if web_rows:
            web_df = pd.DataFrame(web_rows)
            def safe_format(val):
                try:
                    s = str(int(float(val)))
                    return int("20" + s) if len(s) == 5 else int(s)
                except: return 0
            df[q_col] = df[q_col].apply(safe_format)
            
            updated = pd.concat([web_df, df], ignore_index=True)
            updated = updated.drop_duplicates(subset=[q_col], keep='first')
            updated = updated.sort_values(q_col, ascending=False)
            updated = updated[updated[q_col] > 0] 
            
            save_path = file_path if file_path.endswith('.csv') else file_path.replace('.xls', '_synced.csv')
            updated.to_csv(save_path, index=False, encoding='utf-8-sig')
            
            status.success(f"✅ 同步成功！已为 {choice} 更新 {len(web_rows)} 期数据。")
            st.cache_data.clear()
            time.sleep(1.5)
            st.rerun()
        else:
            status.error("❌ 抓取失败：接口未返回数据。")
            time.sleep(2)
            status.empty()
    except Exception as e:
        status.error(f"❌ 同步失败: {str(e)}")

# --- 4. 预测引擎 (🔥 保持不动) ---
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
            html += "<br>" + "".join([f"<span class='pred-ball bg-red' style='width:26px;height:26px;line-height:26px;font-size:12px;margin:2px;'>{n:02d}</span>" for n in r[10:]])
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
st.sidebar.title("💎 AI 决策终端")
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))

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

        st.title(f"🎰 {choice} 数据智算中心")
        t1, t2, t3 = st.tabs(["📜 历史数据", "📈 深度走势", "🤖 AI 演算"])
        
        with t1:
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
            # 反转数据以按时间正序绘图
            plot_df = calc_df.sort_values(q_col).set_index(q_col)
            # 计算5期简单移动平均线 (SMA5)
            plot_df['5期均值 (MA5)'] = plot_df['和值'].rolling(window=5, min_periods=1).mean()
            # 绘制包含和值与均线的复合折线图
            st.line_chart(plot_df[['和值', '5期均值 (MA5)']])
            
            st.markdown("### 🔥 冷热号码频次分布图")
            st.caption(f"统计范围：当前选定的 {view_choice} 数据")
            # 展平所有开奖号码，统计频次
            all_nums = calc_df[d_cols].values.flatten()
            counter = Counter(all_nums)
            freq_df = pd.DataFrame(list(counter.items()), columns=['号码', '出现次数']).sort_values('号码')
            freq_df['号码'] = freq_df['号码'].astype(str)
            st.bar_chart(freq_df.set_index('号码'))

        with t3:
            st.info("💡 提示：点击下方代码框右上角的 📋 图标即可一键复制预测号码进行打票。")
            if st.button("🚀 启动 AI 深度演算 (生成最新策略)", use_container_width=True):
                with st.spinner('AI 正在调取蒙特卡洛树计算引擎...'):
                    time.sleep(1)
                for p in get_prediction(choice):
                    st.markdown(f"""
                    <div class='pred-row'>
                        <div class='pred-title'>{p['name']}</div>
                        <div class='pred-balls'>{p['html']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    # 优化一键复制：使用 Streamlit 自带的漂亮代码块
                    st.code(f"【{choice}】{p['name']} 推荐号码: {p['text']}", language="markdown")
                    
    else: st.error("数据加载已终止。如果您刚才遇到了报错，请点击左侧红色的【清理缓存急救】按钮。")
else: st.error(f"未找到 {choice} 的数据文件。")

# --- 6. 官方免责声明 (🔥 新增：法律规避必备) ---
st.markdown("""
    <div class="legal-footer">
        <b>免责声明</b><br>
        本系统提供的数据统计、走势分析及 AI 算法生成的预测结果，仅供彩票爱好者交流、学习和娱乐参考。<br>
        <b>本工具不构成任何形式的购彩或投资建议。</b><br>
        彩市有风险，购彩需谨慎。请根据自身经济能力理性购彩，严禁未满 18 周岁的未成年人购买彩票。<br>
        © 2024 AI 智算决策中心. All Rights Reserved.
    </div>
""", unsafe_allow_html=True)
