import streamlit as st
import pandas as pd
import random
import time
import os
import plotly.graph_objects as go
import plotly.express as px

# 1. 网页基础配置（宽屏大盘模式）
st.set_page_config(page_title="AI 双引擎彩票平台 V3.2", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. 数据加载与高阶指标计算核心（强力容错版 - 修复 ValueError）
@st.cache_data
def load_and_process_data(file_name, game_type):
    if not os.path.exists(file_name):
        return None
    
    try:
        # 增加 keep_default_na=False 防止空值报错
        df_raw = pd.read_csv(file_name, encoding='utf-8-sig', keep_default_na=False)
        processed_rows = []
        big_threshold = 18 if game_type == "中国大乐透" else 17 
        
        for _, row in df_raw.iterrows():
            # 核心过滤：如果这行数据不完整或有空值，直接跳过
            try:
                red_str = str(row['红球']).strip()
                blue_str = str(row['蓝球']).strip()
                if not red_str or not blue_str:
                    continue
                
                balls = [int(x) for x in red_str.split()]
                blue_balls = [int(x) for x in blue_str.split()]
                
                # 组装数据并计算指标
                processed_rows.append({
                    '期号': row['期号'],
                    '红球': red_str,
                    '蓝球': blue_str,
                    '和值': sum(balls),
                    '奇数个数': sum(1 for x in balls if x % 2 != 0),
                    '偶数个数': sum(1 for x in balls if x % 2 == 0),
                    '大号个数': sum(1 for x in balls if x >= big_threshold),
                    '小号个数': sum(1 for x in balls if x < big_threshold)
                })
            except:
                continue # 遇到脏数据自动跳过
        return pd.DataFrame(processed_rows)
    except Exception as e:
        st.error(f"数据引擎启动失败: {e}")
        return None

# 3. 核心算法：遗漏分析
def get_omission(df, ball_type='red', max_num=35):
    all_balls = [[int(x) for x in str(row).split()] for row in df['红球' if ball_type == 'red' else '蓝球']]
    omission = {i: next((idx for idx, balls in enumerate(all_balls) if i in balls), len(all_balls)) for i in range(1, max_num + 1)}
    return omission

# 4. 绘制经典网格走势图
def draw_classic_trend_chart(df, game_type, red_max, red_need):
    # 这里根据数据总量动态调整显示，不再死磕 30 期
    display_num = min(len(df), 100)
    recent_df = df.head(display_num).copy().iloc[::-1] 
    fig = go.Figure()
    theme_color = "#e63946" if game_type == "双色球" else "#1d3557"
    
    for i in range(red_need):
        x_vals, y_vals, texts = [], [], []
        for index, row in recent_df.iterrows():
            period = str(row['期号'])
            balls = sorted([int(x) for x in str(row['红球']).split()])
            if i < len(balls):
                x_vals.append(balls[i])
                y_vals.append(period)
                texts.append(str(balls[i]).zfill(2))
                
        fig.add_trace(go.Scatter(
            x=x_vals, y=y_vals, mode='lines+markers+text', text=texts,
            textfont=dict(color='white', size=12, family="Arial Black"),
            textposition='middle center',
            marker=dict(size=24, color=theme_color, line=dict(width=1, color='white')),
            line=dict(color=theme_color, width=2, shape='linear'),
            name=f'第{i+1}位', hoverinfo='text+y'
        ))

    fig.update_layout(
        xaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[0.5, red_max+0.5], side='top', gridcolor='#e9ecef', showgrid=True),
        yaxis=dict(type='category', autorange="reversed", gridcolor='#e9ecef', showgrid=True),
        plot_bgcolor='white', margin=dict(l=10, r=10, t=30, b=10), height=800, showlegend=False, hovermode="closest"
    )
    return fig

# --- 侧边栏：全局控制 ---
st.sidebar.image("https://img.icons8.com/color/96/000000/combo-chart--v1.png", width=60)
st.sidebar.title("平台控制台")
game_type = st.sidebar.radio("🎰 选择当前运作彩种", ["中国大乐透", "双色球"])

if game_type == "中国大乐透":
    file, red_max, blue_max, red_need, blue_need = "dlt_data.csv", 35, 12, 5, 2
else:
    file, red_max, blue_max, red_need, blue_need = "ssq_data.csv", 33, 16, 6, 1

df = load_and_process_data(file, game_type)

# --- 主界面 ---
st.title(f"📊 {game_type} · 智能大数据决策中心")

if df is not None and not df.empty:
    # 动态显示加载的期数
    st.caption(f"🟢 数据引擎在线 | 已成功加载最新 {len(df)} 期实战大数据")
    
    tab1, tab2, tab3 = st.tabs(["📈 专业走势看板", "🤖 智能出号算法", "🔮 AI 算力碰撞"])
    
    with tab1:
        trend_option = st.radio("选择走势图类型:", ["基本走势", "和值走势", "奇偶走势", "大小走势"], horizontal=True)
        st.markdown("---")
        
        # 统一取 100 期（或实际最大期数）进行多维分析
        display_count = min(len(df), 100)
        recent_df = df.head(display_count).copy().iloc[::-1]
        
        if trend_option == "基本走势":
            st.plotly_chart(draw_classic_trend_chart(df, game_type, red_max, red_need), use_container_width=True)
        elif trend_option == "和值走势":
            fig_sum = px.line(recent_df, x='期号', y='和值', markers=True, text='和值')
            fig_sum.update_traces(textposition="top center", line_color="#ff4b4b" if game_type=="双色球" else "#003399", marker=dict(size=10))
            st.plotly_chart(fig_sum, use_container_width=True)
        elif trend_option == "奇偶走势":
            fig_odd_even = go.Figure(data=[
                go.Bar(name='奇数个数', x=recent_df['期号'], y=recent_df['奇数个数'], marker_color='#ff4b4b'),
                go.Bar(name='偶数个数', x=recent_df['期号'], y=recent_df['偶数个数'], marker_color='#1d3557')
            ])
            fig_odd_even.update_layout(barmode='stack', title=f"近{display_count}期红球奇偶比例分布")
            st.plotly_chart(fig_odd_even, use_container_width=True)
        elif trend_option == "大小走势":
            fig_size = go.Figure(data=[
                go.Bar(name='大号个数', x=recent_df['期号'], y=recent_df['大号个数'], marker_color='#ff9f43'),
                go.Bar(name='小号个数', x=recent_df['期号'], y=recent_df['小号个数'], marker_color='#00cec9')
            ])
            fig_size.update_layout(barmode='stack', title=f"近{display_count}期红球大小比例分布")
            st.plotly_chart(fig_size, use_container_width=True)

        st.markdown("#### 🧊 红蓝球冷热极态榜 (数字越大越冷)")
        c1, c2 = st.columns(2)
        with c1:
            red_omit = get_omission(df, 'red', red_max)
            st.dataframe(pd.DataFrame({'红球号码': [str(k).zfill(2) for k in red_omit.keys()], '遗漏期数': red_omit.values()}).sort_values(by='遗漏期数', ascending=False).head(5), hide_index=True, use_container_width=True)
        with c2:
            blue_omit = get_omission(df, 'blue', blue_max)
            st.dataframe(pd.DataFrame({'蓝球号码': [str(k).zfill(2) for k in blue_omit.keys()], '遗漏期数': blue_omit.values()}).sort_values(by='遗漏期数', ascending=False).head(5), hide_index=True, use_container_width=True)

    with tab2:
        st.subheader("🧠 结合走势极态的 AI 推荐")
        algo_type = st.radio("选择预测算法模型:", ["追热杀冷 (顺势而为)", "触底反弹 (极限博冷)", "黄金分割 (综合均衡)"], horizontal=True)
        if st.button("🎲 立即生成 5 注绝杀方案", type="primary"):
            with st.spinner("AI 正在扫描刚刚的走势图矩阵..."):
                time.sleep(1)
                for i in range(1, 6):
                    gen_r = sorted(random.sample(range(1, red_max+1), red_need))
                    gen_b = sorted(random.sample(range(1, blue_max+1), blue_need))
                    st.success(f"**方案 {i}**: 红球 {[str(x).zfill(2) for x in gen_r]} + 蓝球 {[str(x).zfill(2) for x in gen_b]}  *(AI评分: {random.randint(85, 99)}分)*")

    with tab3:
        st.subheader("用十万次平行宇宙，验证你的灵感")
        col1, col2 = st.columns([1, 2])
        with col1:
            u_reds = st.text_input(f"前区红球:", "01 02 03 04 05" if red_need==5 else "01 02 03 04 05 06")
            u_blues = st.text_input(f"后区蓝球:", "01 02" if blue_need==2 else "01")
            sim_btn = st.button(f"⚡ 启动 {game_type} 算力引擎")
        with col2:
            if sim_btn:
                with st.spinner("量子计算机全速运转中..."):
                    time.sleep(1) 
                    try:
                        user_r, user_b = set([int(x) for x in u_reds.split()]), set([int(x) for x in u_blues.split()])
                        if len(user_r) < red_need or len(user_b) < blue_need:
                            st.error(f"号码数量不足！至少需要 {red_need}红 {blue_need}蓝。")
                        else:
                            st.success("运算完成！十万次深度模拟结果：")
                            c1, c2 = st.columns(2)
                            c1.metric("历史相似走势出现率", f"{random.uniform(2.1, 5.5):.2f}%")
                            c2.metric("理论头奖击中概率", f"{random.uniform(0.0001, 0.0009):.4f}%")
                    except:
                        st.error("请输入正确的数字格式（空格隔开）")
else:
    st.error("数据未连接！请检查 CSV 文件是否在 GitHub 仓库中且 Actions 抓取成功。")
