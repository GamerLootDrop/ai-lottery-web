import streamlit as st
import pandas as pd
import plotly.express as px

# 页面配置
st.set_page_config(page_title="AI 彩票决策中心", layout="wide")

# 读取数据的函数（增加容错逻辑）
def load_data(file_path):
    try:
        # 直接读取本地 GitHub 仓库中的 CSV
        df = pd.read_csv(file_path, dtype={'期号': str})
        if df.empty or len(df.columns) < 3:
            return None
        return df
    except:
        return None

# 侧边栏
st.sidebar.header("平台控制台")
lottery_type = st.sidebar.radio("选择彩种", ["中国大乐透", "双色球"])

# 映射文件名
file_map = {"中国大乐透": "dlt_data.csv", "双色球": "ssq_data.csv"}
target_file = file_map[lottery_type]

# 加载数据
df = load_data(target_file)

st.title(f"📊 {lottery_type} 决策中心")

if df is not None:
    # --- 这里是你的 AI 大数据核心逻辑 ---
    
    # 1. 选择计算范围
    num_periods = st.sidebar.select_slider(
        "选择参与 AI 计算的历史数据量", 
        options=[30, 50, 100, 200, 500, 1000, 2000],
        value=100
    )
    
    # 截取选定的期数
    analysis_df = df.head(num_periods).copy()
    
    st.success(f"✅ 成功连接数据库！已加载 {len(df)} 期历史记录，当前 AI 正在基于近 {num_periods} 期进行推演。")

    # 2. 展示走势图（示例：红球首号分布）
    analysis_df['红1'] = analysis_df['红球'].str.split().str[0].astype(int)
    fig = px.line(analysis_df, x='期号', y='红1', title="红球首号趋势走势")
    st.plotly_chart(fig, use_container_width=True)

    # 3. 数据预览
    st.subheader("历史数据明细")
    st.dataframe(df, use_container_width=True)

else:
    # 如果还是没数据，显示引导提示
    st.error("🚨 数据未连接！原因可能是：dlt_data.csv 尚未生成，或文件格式不正确。")
    st.info("💡 请确保您已在 GitHub Actions 中成功运行过一次 'update_data' 任务。")
    st.image("https://via.placeholder.com/800x200.png?text=Waiting+for+Data+Source...")
