import streamlit as st

from app_sections import render_dashboard, render_formula_section, render_lobby, render_tactical_section
from auth import init_auth_state, restore_auth_from_query
from components import render_access_banner, render_topbar
from data_fetch import build_synced_dataframe, find_lottery_file, load_full_data, save_synced_dataframe
from lottery_rules import commercial_choice_enabled
from ui_styles import inject_styles


def render_disclaimer():
    st.markdown(
        """
        <div class="disclaimer-card">
          <div class="result-title">免责声明</div>
          <div class="muted">
            本工具仅基于历史公开开奖数据、统计模型和结构公式进行样本分析展示，不承诺、保证或暗示任何中奖结果，
            不构成投注建议、投资建议或收益承诺。彩票具有随机性和不确定性，请理性参与，独立判断，风险自担。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="量化星图", page_icon="🎯", layout="wide")
inject_styles()
init_auth_state()
restore_auth_from_query()

render_topbar("量化星图")
render_access_banner()

if "page" not in st.session_state:
    st.session_state["page"] = "数据看板"

with st.container():
    col1, col2, col3 = st.columns([1.2, 1, 0.8])
    with col1:
        choice = st.selectbox("选择彩种", ["双色球", "大乐透", "福彩3D", "排列3", "排列5", "七星彩", "快乐8"])
    with col2:
        view_choice = st.selectbox("战术期数", [5, 10, 29, 30, 50, 100], index=3)
    with col3:
        page_options = ["数据看板", "手动录入", "公式中心", "交流大厅"]
        current_page = st.session_state.get("page", "数据看板")
        if current_page not in page_options:
            current_page = "数据看板"
        page = st.selectbox("页面", page_options, index=page_options.index(current_page))
        st.session_state["page"] = page

view_limit = int(view_choice)

if not commercial_choice_enabled(choice):
    st.warning("该彩种暂不开放主流程，可后续接入自定义样本或单独规则。")
    if page == "交流大厅":
        render_lobby(choice)
    else:
        st.stop()

target = find_lottery_file(choice)
df = None
q_col = None
d_cols = None
actual_path = None
if target:
    df, q_col, d_cols, _, actual_path = load_full_data(target, choice)

if df is not None and not df.empty:
    if st.button("同步最新开奖", use_container_width=True, key="sync_latest"):
        updated, message = build_synced_dataframe(df, q_col, d_cols, choice)
        if updated is not None:
            save_path = save_synced_dataframe(updated, actual_path)
            st.success(f"{message} 已保存到 {save_path}")
            st.rerun()
        else:
            st.error(message)

if page == "数据看板":
    render_dashboard(df, choice, view_limit)
elif page == "手动录入":
    render_tactical_section(df, choice, view_limit)
elif page == "公式中心":
    render_formula_section(df, choice, view_limit)
else:
    render_lobby(choice)

render_disclaimer()
