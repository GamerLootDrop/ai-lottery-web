import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. 网页基础配置
st.set_page_config(page_title="AI 全彩种决策中心", layout="wide")

# 2. 精准匹配你上传的文件名
# 注意：这里的列索引是根据你提供的 xls 转 csv 后的真实结构设置的
LOTTERY_CONFIG = {
    "双色球": {
        "file": "ssq.xls - 双色球-历史开奖数据.csv", 
        "r_cols": range(2, 8), 
        "b_cols": [8]
    },
    "中国大乐透": {
        "file": "dlt.xls - data.csv", 
        "r_cols": range(2, 7), 
        "b_cols": range(7, 9)
    },
    "福彩3D": {
        "file": "3d.xls - data.csv", 
        "r_cols": range(2, 5), 
        "b_cols": []
    },
    "快乐8": {
        "file": "kl8.xls - data.csv", 
        "r_cols": range(2, 22), 
        "b_cols": []
    },
    "七星彩": {
        "file": "7xc.xls - 七星彩-历史开奖数据.csv", 
        "r_cols": range(2, 8), 
        "b_cols": [8]
    },
    "排列3": {
        "file": "p3.xls - 排列3-历史开奖数据.csv", 
        "r_cols": range(2, 5), 
        "b_cols": []
    },
    "排列5": {
        "file": "p5.xls - 排列五-历史开奖数据.csv", 
        "r_cols": range(2, 7), 
        "b_cols": []
    }
}

@st.cache_data
def load_historical_data(conf):
    if not os.path.exists(conf['file']):
        return None
    try:
        # 跳过文件开头的标题行（skiprows=1），确保读取到真实的列名
        df = pd.read_csv(conf['file'], skiprows=1, dtype=str)
        # 去除列名的空格
        df.columns = [c.strip() for c in df.columns]
        
        res = []
        for _, row in df.iterrows():
            # 只有期号不为空时才处理
            if pd.isna(row.get('开奖期号')): continue
            
            # 提取号码：将 1.0 这种浮点数转为 01 这种格式
            def format_ball(val):
                if pd.isna(val): return ""
                return str(val).split('.')[0].zfill(2)

            r_list = [format_ball(row.iloc[i]) for i in conf['r_cols'] if i < len(row)]
            b_list = [format_ball(row.iloc[i]) for i in conf['b_cols'] if i < len(row)]
            
            res.append({
                "期号": str(row['开奖期号']).split('.')[0],
                "红球/前区": " ".join([x for x in r_list if x]),
                "蓝球/后区": " ".join([x for x in b_list if x])
            })
        return pd.DataFrame(res)
    except Exception as e:
        st.sidebar.error(f"数据解析失败: {e}")
        return None

# --- 侧边栏：决策控制台 ---
st.sidebar.title("💎 AI 大数据决策系统")
st.sidebar.markdown("---")
choice = st.sidebar.selectbox("🎯 选择彩种", list(LOTTERY_CONFIG.keys()))

# 大数据跨度选择器
num_periods = st.sidebar.select_slider(
    "🧠 AI 分析跨度", 
    options=[50, 100, 500, 1000, 2000, 5000], 
    value=100
)

# 加载数据
data = load_historical_data(LOTTERY_CONFIG[choice])

if data is not None and not data.empty:
    st.title(f"📊 {choice} · 20年历史大数据分析")
    st.info(f"✅ 成功调阅历史记录：{len(data)} 期 | 当前正透视最近：{min(num_periods, len(data))} 期")

    # 1. 核心走势看板
    st.subheader("📈 历史波动走势")
    analysis_df = data.head(num_periods).copy()
    # 取出第一位球号做简单趋势展示
    analysis_df['首号'] = analysis_df['红球/前区'].str.split().str[0].astype(float)
    
    fig = px.line(
        analysis_df[::-1], 
        x='期号', 
        y='首号', 
        markers=True,
        title=f"{choice} 历史首位球震荡趋势 (最近 {num_periods} 期)"
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    # 2. 数据透视明细
    st.subheader("📑 历史开奖明细")
    st.dataframe(data, use_container_width=True)
    
else:
    st.error(f"🚨 找不到数据文件：{LOTTERY_CONFIG[choice]['file']}")
    st.warning("请确认 GitHub 仓库里是否存在该文件，且文件名必须完全一致。")
