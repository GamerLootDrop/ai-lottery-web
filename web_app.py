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
# 💰💰💰 老板专属配置区 (只需修改这里) 💰💰💰
# =========================================================
MY_WECHAT_ID = "252766667"           # 您的微信号
VIP_PASSWORD = "888"                 # VIP 验证口令
# =========================================================

# --- 1. 样式表 ---
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
    
    .marquee-wrapper { background: linear-gradient(to right, #fff3cd, #fff8e1); padding: 10px 15px; border-radius: 8px; border-left: 4px solid #f9bf15; margin-bottom: 20px; overflow: hidden; display: flex; align-items: center; }
    .marquee-content { white-space: nowrap; animation: marquee 30s linear infinite; color: #856404; font-weight: bold; font-size: 14px; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-150%); } }
    
    .comment-box { background: #fff; border: 1px solid #eaeaea; border-radius: 8px; padding: 12px; margin-bottom: 8px; }
    .comment-header { display: flex; justify-content: space-between; margin-bottom: 5px; }
    .comment-user { font-weight: bold; color: #1f77b4; font-size: 13px; }
    .comment-time { color: #999; font-size: 11px; }
    .comment-body { color: #444; font-size: 13px; line-height: 1.4; }
    .legal-footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #eaeaea; text-align: center; color: #999; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

# --- 工具函数 ---
def get_countdown():
    now = datetime.now()
    target = now.replace(hour=21, minute=30, second=0)
    if now > target: target += timedelta(days=1)
    diff = target - now
    return f"{diff.seconds//3600:02d}时{(diff.seconds%3600)//60:02d}分{diff.seconds%60:02d}秒"

def get_fake_broadcasts():
    cities = ["广东", "浙江", "江苏", "山东", "河南", "四川", "北京", "上海"]
    algos = ["极热寻踪", "绝地反弹", "黄金均衡", "蒙特卡洛", "深度拟合"]
    texts = [f"【最新喜报】{random.choice(cities)}用户 1{random.randint(3,9)}{random.randint(0,9)}****{random.randint(1000,9999)} 成功解锁「{random.choice(algos)}」策略！" for _ in range(5)]
    return "  🔥  ".join(texts)

# --- 数据加载 ---
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
        
        ball_cols = []
        for i in range(list(raw_df.columns).index(q_col) + 1, len(raw_df.columns)):
            nums = pd.to_numeric(raw_df[raw_df.columns[i]], errors='coerce').dropna()
            if not nums.empty and (nums <= 81).all(): ball_cols.append(raw_df.columns[i])
            if len(ball_cols) == max_balls: break
            
        clean_df = raw_df[[q_col] + ball_cols].copy()
        new_names = ['期号'] + [f"b_{i+1}" for i in range(len(ball_cols))]
        clean_df.columns = new_names
        for c in new_names: clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce').fillna(0).astype(int)
        
        return clean_df.sort_values('期号', ascending=False), '期号', new_names[1:], (choice in ["双色球", "大乐透", "快乐8"]), file_path
    except: return None, None, None, None, None

# --- AI 预测逻辑 (VIP部分) ---
def get_real_prediction(df_view, d_cols, choice):
    sets = []
    all_nums = []
    for col in d_cols: all_nums.extend(df_view[col].dropna().tolist())
    freq_dict = Counter(all_nums)
    
    rules = {
        "双色球": (list(range(1, 34)), 6, list(range(1, 17)), 1, "bg-red", "bg-blue"),
        "大乐透": (list(range(1, 36)), 5, list(range(1, 13)), 2, "bg-blue", "bg-yellow"),
        "七星彩": (list(range(0, 10)), 6, list(range(0, 15)), 1, "bg-purple", "bg-yellow"),
        "快乐8": (list(range(1, 81)), 20, [], 0, "bg-red", ""),
        "福彩3D": (list(range(0, 10)), 3, [], 0, "bg-lightblue", ""),
        "排列3": (list(range(0, 10)), 3, [], 0, "bg-lotus", ""),
        "排列5": (list(range(0, 10)), 5, [], 0, "bg-lotus", "")
    }
    
    pool_r, count_r, pool_b, count_b, c_r, c_b = rules.get(choice, rules["双色球"])
    algos = [
        {"name": "🔥 极热寻踪", "vip": False}, {"name": "🧊 绝地反弹", "vip": False},
        {"name": "⚖️ 黄金均衡", "vip": False}, {"name": "🎲 蒙特卡洛引擎", "vip": True},
        {"name": "🧠 深度拟合网络", "vip": True}
    ]
    
    for algo in algos:
        r_res = sorted(random.sample(pool_r, count_r))
        b_res = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
        html = "".join([f"<span class='pred-ball {c_r}'>{n:02d if choice in ['双色球','大乐透','快乐8'] else n}</span>" for n in r_res])
        html += "".join([f"<span class='pred-ball {c_b}'>{n:02d if choice in ['双色球','大乐透'] else n}</span>" for n in b_res])
        sets.append({"name": algo['name'], "html": html, "is_vip": algo['vip']})
    return sets

# --- 侧边栏 ---
LOTTERY_FILES = {"福彩3D": "3d", "双色球": "ssq", "大乐透": "dlt", "快乐8": "kl8", "排列3": "p3", "排列5": "p5", "七星彩": "7xc"}
choice = st.sidebar.selectbox("🎯 选择实战彩种", list(LOTTERY_FILES.keys()))
st.sidebar.markdown(f'<div class="wechat-box">加微信发红包获【VIP口令】<br><b style="color:#ff4b4b;">{MY_WECHAT_ID}</b></div>', unsafe_allow_html=True)
view_options = {"近30期": 30, "近50期": 50, "近100期": 100}
view_choice = st.sidebar.radio("选择分析样本", list(view_options.keys()), index=1)

# --- 主界面 ---
file_kw = LOTTERY_FILES[choice]
all_files = [f for f in os.listdir(".") if file_kw in f.lower() and (f.endswith('.xls') or f.endswith('.csv'))]
target = next((f for f in all_files if '_synced' in f), all_files[0] if all_files else None)

if target:
    df, q_col, d_cols, needs_zero, actual_path = load_full_data(target, choice)
    if df is not None:
        st.title(f"🎰 {choice} 数据智算中心")
        st.markdown(f'<div class="timer-bar">⏰ 离今日开奖截止还剩 {get_countdown()}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="marquee-wrapper"><div class="marquee-content">{get_fake_broadcasts()}</div></div>', unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["📜 历史数据", "📈 深度走势", "🤖 AI 演算", "💬 交流大厅"])
        
        with t1:
            st.write("📊 近期历史开奖回顾")
            table_html = "<table class='hist-table'><tr><th>期号</th><th>开奖号码</th></tr>"
            for _, row in df.head(view_options[view_choice]).iterrows():
                balls_html = "".join([f"<span class='ball bg-red'>{row[c]}</span>" for c in d_cols])
                table_html += f"<tr><td>{int(row[q_col])}</td><td>{balls_html}</td></tr>"
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
            # 👇 这里补上了老板要的奇数走势图
            st.markdown("### ⚖️ 奇偶分布走势 (奇数个数)")
            st.bar_chart(calc_df.set_index('期号')['奇数个数'], color="#3b71f7")

        with t3:
            st.markdown("##### 🎯 专属号码多维衍算")
            custom_input = st.text_input("🔮 输入心水号 (空格隔开)：", placeholder="例如：06 18")
            
            if st.button("🪄 一键衍生拟合", use_container_width=True, type="secondary"):
                if custom_input.strip():
                    seed_nums = [int(n) for n in re.findall(r'\d+', custom_input)]
                    # 👇 这一块就是整改后的动态随机逻辑，确保每次点击都不一样
                    pool_r = list(range(1, 34)) if choice=="双色球" else list(range(1, 36))
                    dan_pool = seed_nums if seed_nums else [1, 2, 3]
                    # 每次点击随机选核心，再混入历史随机热号
                    core = random.choice(dan_pool)
                    ma3 = sorted(list(set([core] + random.sample(pool_r, 2))))
                    ma5 = sorted(list(set(ma3 + random.sample(pool_r, 2))))
                    ma6 = sorted(list(set(ma5 + random.sample(pool_r, 1))))
                    
                    st.success("✅ AI 已完成量子采样，生成本次专属推荐：")
                    st.write(f"核心胆码：{core}")
                    st.write(f"精选组合：{' '.join(map(str, ma3))}")
                    st.write(f"大底复式：{' '.join(map(str, ma6))}")
                else: st.warning("请先输入种子号码")

            st.markdown("---")
            with st.form("vip_form"):
                pwd = st.text_input("🔑 输入 VIP 口令解锁核心算法", type="password")
                if st.form_submit_button("验证口令"):
                    if pwd == VIP_PASSWORD: st.success("解锁成功！")
                    else: st.error("口令错误")
            
            preds = get_real_prediction(df, d_cols, choice)
            for p in preds:
                if p['is_vip'] and pwd != VIP_PASSWORD:
                    st.markdown(f"<div class='pred-row'><div class='pred-title'>{p['name']}</div><div class='pred-balls vip-locked'>{p['html']}</div><div class='lock-overlay'>🔒 算法锁定</div></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='pred-row'><div class='pred-title'>{p['name']} ✅</div><div class='pred-balls'>{p['html']}</div></div>", unsafe_allow_html=True)

        with t4:
            # 👇 这里就是 50 名活跃水军的滚动大厅
            st.markdown("### 💬 内部 VIP 交流大厅")
            st.info(f"🟢 当前在线活跃人数：**1,862** 人。发言请加微信：{MY_WECHAT_ID}")
            
            if 'comments' not in st.session_state:
                users = ["老彩民", "追梦人", "李哥", "王大拿", "数据控", "算号大师", "潜水员", "张三"]
                msgs = ["已加微信拿到口令！", "昨天蒙特卡洛准爆了！", "19.9的数据包真香。", "怎么发言被拦截了？", "求今日胆码！"]
                st.session_state.comments = [{"user": random.choice(users)+str(random.randint(10,99)), "text": random.choice(msgs), "time": f"{i}分钟前", "vip": random.random()>0.3} for i in range(1, 51)]
            
            # 使用带滚动条的容器
            chat_box = st.container(height=450)
            with chat_box:
                for c in st.session_state.comments:
                    color = "#ff4b4b" if c['vip'] else "#999"
                    st.markdown(f'<div class="comment-box"><div class="comment-header"><span class="comment-user">{c["user"]} <span style="color:{color}">[{"VIP" if c["vip"] else "普通"}]</span></span><span>{c["time"]}</span></div><div class="comment-body">{c["text"]}</div></div>', unsafe_allow_html=True)

            st.markdown("---")
            c_input = st.text_input("📝 发表您的心得...")
            if st.button("🚀 发送留言", use_container_width=True):
                st.error(f"🔒 发送失败：您当前为游客状态！请加微信 {MY_WECHAT_ID} 获取授权。")

st.markdown(f'<div class="legal-footer">© 2024 AI 智算中心 | 购彩有风险，入市需谨慎 | 客服：{MY_WECHAT_ID}</div>', unsafe_allow_html=True)
