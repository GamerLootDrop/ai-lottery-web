import streamlit as st
from urllib.parse import urlencode

from auth import MY_WECHAT_ID, logout, unlock_with_code
from lottery_rules import format_number


def render_topbar(title):
    if st.query_params.get("settings") == "1":
        st.session_state["show_settings"] = True
    params = {key: value for key, value in st.query_params.items()}
    params["settings"] = "1"
    settings_href = "?" + urlencode(params, doseq=True)
    st.markdown(
        f"""
        <div class="topbar">
          <div class="muted">数据中枢</div>
          <div class="topbar-title">{title}</div>
          <a class="topbar-link" href="{settings_href}" target="_self">设置</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_settings_dialog()


def render_settings_dialog():
    if not st.session_state.get("show_settings"):
        return

    dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)

    def _settings_content():
        days_left = st.session_state.get("days_left", "未知")
        if st.session_state.get("vip_unlocked"):
            st.success(f"当前权限：高阶版，剩余 {days_left} 天。")
        else:
            st.info("当前权限：基础版。高阶公式、手动样本和组合压缩需授权。")
        st.markdown("服务微信：")
        st.code(MY_WECHAT_ID, language="text")
        with st.expander("免责声明", expanded=True):
            st.write(
                "本工具仅基于历史公开开奖数据、统计模型和结构公式进行样本分析展示，"
                "不承诺、保证或暗示任何中奖结果，不构成投注建议、投资建议或收益承诺。"
                "彩票具有随机性和不确定性，请理性参与，独立判断，风险自担。"
            )
        if st.session_state.get("vip_unlocked") and st.button("退出授权", use_container_width=True, key="settings_logout"):
            logout()
            st.session_state["show_settings"] = False
            st.rerun()
        if st.button("关闭", use_container_width=True, key="settings_close"):
            st.session_state["show_settings"] = False
            if "settings" in st.query_params:
                del st.query_params["settings"]
            st.rerun()

    if dialog:
        @dialog("设置")
        def _settings_dialog():
            _settings_content()

        _settings_dialog()
    else:
        with st.expander("设置", expanded=True):
            _settings_content()


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


def render_hero_card(choice, issue_text, date_text, red_nums, blue_nums):
    red_html = "".join([f'<div class="number-orb orb-primary">{format_number(n, choice)}</div>' for n in red_nums])
    blue_html = "".join([f'<div class="number-orb orb-accent">{format_number(n, choice)}</div>' for n in blue_nums])
    sep_html = '<div class="number-separator">|</div>' if blue_nums else ""
    st.markdown(
        f'<section class="glass-card"><div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;"><div><div class="section-title" style="margin-top:0;border-left:none;padding-left:0;">最新截获</div><div class="hero-issue">{issue_text}</div><div class="hero-date">{date_text}</div></div><div class="status-pill"><span class="status-dot"></span>已核实</div></div><div style="height:12px;"></div><div class="number-row">{red_html}{sep_html}{blue_html}</div></section>',
        unsafe_allow_html=True,
    )


def render_metric_cards(metrics):
    cards = []
    for item in metrics:
        cards.append(
            f'<div class="glass-card metric-card"><div class="metric-label">{item["label"]}</div><div class="metric-value" style="color:{item.get("color", "#81cfff")};">{item["value"]}</div><div class="metric-hint">{item["hint"]}</div></div>'
        )
    st.markdown(f'<div class="metric-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_prediction_card(title, desc, red_nums, blue_nums, choice, tone="primary"):
    primary_class = "accent" if tone == "accent" else "primary"
    balls = "".join([f'<span class="ball-mini {primary_class}">{format_number(n, choice)}</span>' for n in red_nums])
    if blue_nums:
        balls += "".join([f'<span class="ball-mini accent">{format_number(n, choice)}</span>' for n in blue_nums])
    number_text = " ".join([format_number(n, choice) for n in red_nums])
    if blue_nums:
        number_text += " | " + " ".join([format_number(n, choice) for n in blue_nums])
    st.markdown(
        f'<div class="glass-card result-card"><div class="result-title">{title}</div><div class="result-desc">{desc}</div><div class="ball-strip">{balls}</div><div class="code-line">{number_text}</div></div>',
        unsafe_allow_html=True,
    )
    st.code(number_text, language="text")


def render_access_banner():
    if st.session_state.get("vip_unlocked"):
        days_left = st.session_state.get("days_left", "未知")
        st.markdown(
            f"""
            <div class="access-strip access-compact">
              <div>
                <div class="result-title">高阶版已解锁 · 剩余 {days_left} 天</div>
              </div>
              <div class="access-badge">已解锁</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        """
        <div class="access-strip locked">
          <div>
            <div class="result-title">当前权限：基础版</div>
            <div class="result-desc">数据看板可直接使用；高阶公式、手动样本和组合压缩需授权。</div>
          </div>
          <div class="access-badge">待解锁</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("解锁高阶功能", use_container_width=True, key="top_unlock_go"):
        st.session_state["show_top_unlock"] = True
        st.session_state["page"] = "公式中心"
    render_top_unlock_dialog()


def render_top_unlock_dialog():
    if not st.session_state.get("show_top_unlock"):
        return

    dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
    if dialog:
        @dialog("快速解锁高阶功能")
        def _unlock_dialog():
            render_unlock_panel("快速解锁高阶功能", key_prefix="top")
            if st.button("暂不解锁", use_container_width=True, key="close_top_unlock"):
                st.session_state["show_top_unlock"] = False
                st.rerun()

        _unlock_dialog()
        return

    if st.session_state.get("show_top_unlock"):
        render_unlock_panel("快速解锁高阶功能", key_prefix="top")


def render_unlock_panel(title="高阶权限未解锁", key_prefix="vip"):
    if st.session_state.get("vip_unlocked"):
        days_left = st.session_state.get("days_left", "未知")
        st.markdown(
            f"""
            <div class="glass-card unlock-panel">
              <div class="result-title">高阶权限已生效</div>
              <div class="result-desc">当前剩余 {days_left} 天。需要续费、换设备或开通新授权，可添加微信处理。</div>
              <div class="code-line">微信：{MY_WECHAT_ID}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.code(MY_WECHAT_ID, language="text")
        return True

    benefits = [
        "AC12 高阶约束",
        "马尔科夫链转移",
        "手动样本反向分析",
        "专家组合压缩",
        "自建数据沙盘",
    ]
    benefit_html = "".join(f'<span class="access-chip">{item}</span>' for item in benefits)
    st.markdown(
        f"""
        <div class="glass-card unlock-panel">
          <div class="result-title">{title}</div>
          <div class="result-desc">输入授权码后开放完整公式模块。没有授权码可以添加微信办理，备注“高阶公式”。</div>
          <div class="access-chip-row">{benefit_html}</div>
          <div class="code-line">微信：{MY_WECHAT_ID}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(MY_WECHAT_ID, language="text")

    code = st.text_input("授权码", type="password", key=f"{key_prefix}_code", placeholder="输入后点击激活")
    if st.button("激活高阶权限", use_container_width=True, key=f"{key_prefix}_unlock_btn"):
        ok, message = unlock_with_code(code)
        if ok:
            st.session_state[f"{key_prefix}_auth_message"] = ("success", f"激活成功，剩余 {message} 天。")
            st.session_state["show_top_unlock"] = False
            st.rerun()
        else:
            st.session_state[f"{key_prefix}_auth_message"] = ("error", f"{message}。如需开通或续费，请添加微信 {MY_WECHAT_ID}。")

    auth_message = st.session_state.get(f"{key_prefix}_auth_message")
    if auth_message:
        level, text = auth_message
        if level == "success":
            st.success(text)
        else:
            st.error(text)
    return st.session_state.get("vip_unlocked", False)


def render_bottom_nav(active_label):
    labels = [("看板", "数据看板"), ("录入", "手动录入"), ("公式", "公式中心"), ("大厅", "交流大厅")]
    cols = st.columns(4)
    for col, (label, page_name) in zip(cols, labels):
        button_label = f"● {label}" if label == active_label else label
        with col:
            if st.button(button_label, use_container_width=True, key=f"nav_{label}"):
                st.session_state["page"] = page_name
                st.rerun()
