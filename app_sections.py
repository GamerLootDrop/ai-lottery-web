import random
import re
import time
from collections import Counter

import pandas as pd
import streamlit as st

from components import render_bottom_nav, render_hero_card, render_metric_cards, render_prediction_card, render_unlock_panel
from data_fetch import build_synced_dataframe, load_cloud_or_local_data, save_synced_dataframe
from engagement import DRAW_SCHEDULES, WEEKDAY_NAMES, get_next_draw, get_usage_snapshot, load_comments, render_countdown_widget, submit_comment
from formula_engine import (
    build_probability_profile,
    build_cycle_filter_report,
    calculate_bets,
    calculate_frequencies,
    derive_seed_combinations,
    expert_compress_combinations,
    get_advanced_predictions,
    get_basic_predictions,
    get_012_route_stats,
    run_tactical_manual_analysis,
    scan_advanced_patterns,
)
from lottery_rules import format_number, get_lottery_rules


def render_dashboard(df, choice, view_limit):
    if df is None or df.empty:
        st.warning("当前没有可用数据。")
        return

    render_countdown_widget(choice)

    filter_mode = st.radio("分析维度", ["近期连贯", "历史同期", "星期走势"], horizontal=True)
    target_period = None
    weekday = None
    if filter_mode == "历史同期":
        latest_issue = str(int(df.iloc[0]["期号"]))
        default_target = int(latest_issue[-3:]) + 1 if len(latest_issue) >= 3 else 1
        target_period = st.number_input("目标同期尾号", min_value=1, max_value=160, value=default_target, step=1)
    elif filter_mode == "星期走势":
        schedule = DRAW_SCHEDULES.get(choice, {})
        weekday_options = [WEEKDAY_NAMES[i] for i in schedule.get("weekdays", list(range(7)))]
        weekday = st.selectbox("开奖星期", weekday_options)

    cycle_report = build_cycle_filter_report(
        df,
        choice,
        mode=filter_mode,
        view_limit=view_limit,
        target_period=f"{int(target_period):03d}" if target_period else None,
        weekday=weekday,
    )
    if cycle_report and not cycle_report.get("ok"):
        st.warning(cycle_report["message"])
        return

    if cycle_report and cycle_report.get("ok"):
        st.caption(f"当前模式：{cycle_report['label']} | 样本 {cycle_report['sample_size']} 期")
        if cycle_report.get("weekday_source"):
            st.caption(f"星期来源：{cycle_report['weekday_source']}")
        calc_source = cycle_report["rows"].copy()
    else:
        calc_source = df.head(view_limit).copy()

    d_cols = [c for c in calc_source.columns if str(c).startswith("b_")]
    if not d_cols:
        d_cols = [c for c in calc_source.columns if c not in ["期号", "日期", "日期_解析", "星期"] and pd.api.types.is_numeric_dtype(calc_source[c])]
    for col in d_cols:
        calc_source[col] = pd.to_numeric(calc_source[col], errors="coerce").fillna(0).astype(int)
    red_nums, blue_nums = [], []
    _, count_r, _, count_b = get_lottery_rules(choice)
    latest = calc_source.iloc[0]
    values = [int(latest[col]) for col in d_cols[: count_r + count_b]]
    red_nums = values[:count_r]
    blue_nums = values[count_r:]
    render_hero_card(choice, f"{choice} #{int(latest['期号'])}", "最新样本已载入", red_nums, blue_nums)

    calc_df = calc_source.head(view_limit).copy()
    calc_df["和值"] = calc_df[d_cols].sum(axis=1)
    calc_df["跨度"] = calc_df[d_cols].max(axis=1) - calc_df[d_cols].min(axis=1)

    repeat_count, consecutive_count = 0, 0
    detail_rows = []
    for idx, (_, row) in enumerate(calc_df.iterrows()):
        nums = sorted([int(row[col]) for col in d_cols])
        odd_count = sum(1 for n in nums if n % 2 == 1)
        even_count = len(nums) - odd_count
        consecutive = any(nums[i + 1] - nums[i] == 1 for i in range(len(nums) - 1))
        if consecutive:
            consecutive_count += 1

        repeat_status = "无重号"
        if idx + 1 < len(calc_df):
            prev_nums = set(int(calc_df.iloc[idx + 1][col]) for col in d_cols)
            intersects = sorted(set(nums).intersection(prev_nums))
            if intersects:
                repeat_count += 1
                repeat_status = "重号 " + " ".join(format_number(x, choice) for x in intersects)

        detail_rows.append(
            {
                "期号": f"第 {int(row['期号'])} 期",
                "和值": int(row["和值"]),
                "跨度": int(row["跨度"]),
                "奇偶比": f"{odd_count}:{even_count}",
                "连号": "有" if consecutive else "无",
                "重号": repeat_status,
            }
        )

    mean_value = int(calc_df["和值"].mean()) if not calc_df.empty else 0
    spread = int((calc_df["和值"].max() - calc_df["和值"].min()) / 2) if len(calc_df) > 1 else 0
    repeat_rate = f"{(repeat_count / len(calc_df) * 100):.0f}%" if len(calc_df) else "0%"
    consecutive_rate = f"{(consecutive_count / len(calc_df) * 100):.0f}%" if len(calc_df) else "0%"
    if cycle_report and cycle_report.get("ok"):
        mean_value = int(cycle_report["sum_mean"])
        spread = int(cycle_report["span_mean"])
        repeat_rate = f"{cycle_report['repeat_rate'] * 100:.0f}%"
        consecutive_rate = f"{cycle_report['consecutive_rate'] * 100:.0f}%"

    metrics = [
        {"label": "均值和值", "value": mean_value, "hint": f"取样窗口 {view_limit} 期", "color": "#81cfff"},
        {"label": "平均偏差", "value": spread, "hint": "波动宽度估算", "color": "#ff8a73"},
        {"label": "历史重号率", "value": repeat_rate, "hint": "与上一期重复占比", "color": "#7dffa2"},
        {"label": "历史连号率", "value": consecutive_rate, "hint": "连号出现频率", "color": "#ffb4a5"},
    ]
    render_metric_cards(metrics)

    if cycle_report and cycle_report.get("ok") and filter_mode == "星期走势":
        front_rank = cycle_report.get("front_rank", [])
        back_rank = cycle_report.get("back_rank", [])
        front_hot = [row["号码"] for row in front_rank[: max(1, min(count_r + 2, len(front_rank)))]]
        front_cold = [row["号码"] for row in sorted(front_rank, key=lambda x: (x["频次"], x["号码"]))[: max(1, min(count_r + 2, len(front_rank)))]]

        st.markdown('<div class="section-title">星期独立热区</div>', unsafe_allow_html=True)
        render_prediction_card(f"{weekday} 前区高频", f"仅统计当前 {weekday} 的近 {cycle_report['sample_size']} 个有效样本。", front_hot, [], choice)
        render_prediction_card(f"{weekday} 前区低频", "同一开奖星期内出现较少的号码，用于冷门观察。", front_cold, [], choice, tone="accent")

        if back_rank:
            back_hot = [row["号码"] for row in back_rank[: max(1, min(count_b + 3, len(back_rank)))]]
            render_prediction_card(f"{weekday} 后区高频", "后区仅按同星期窗口单独计数。", back_hot, [], choice, tone="accent")

        front_rank_df = pd.DataFrame(front_rank[:12]).copy()
        if not front_rank_df.empty:
            front_rank_df["号码"] = front_rank_df["号码"].map(lambda x: format_number(x, choice))
            st.dataframe(front_rank_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">和值走势</div>', unsafe_allow_html=True)
    chart_df = calc_df[["期号", "和值"]].sort_values(by="期号").set_index("期号")
    st.line_chart(chart_df, use_container_width=True)

    st.markdown('<div class="section-title">形态明细</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">历史样本</div>', unsafe_allow_html=True)
    show_df = calc_source.head(min(view_limit, 12)).copy()
    for col in d_cols:
        show_df[col] = show_df[col].map(lambda x: format_number(x, choice))
    st.dataframe(show_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">模拟开奖</div>', unsafe_allow_html=True)
    if st.button("生成模拟开奖", use_container_width=True, key=f"mock_draw_{choice}"):
        pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
        mock_red = sorted(random.sample(pool_r, count_r))
        mock_blue = sorted(random.sample(pool_b, count_b)) if count_b > 0 else []
        st.session_state[f"mock_draw_result_{choice}"] = (mock_red, mock_blue)
    mock_result = st.session_state.get(f"mock_draw_result_{choice}")
    if mock_result:
        mock_red, mock_blue = mock_result
        render_prediction_card("模拟开奖", "按当前彩种规则随机抽取，仅作沙盘演示。", mock_red, mock_blue, choice)
    render_bottom_nav("看板")


def render_formula_section(df, choice, view_limit):
    if df is None or df.empty:
        st.warning("当前没有可用开奖数据，请先上传或同步对应彩种数据文件。")
        render_bottom_nav("公式")
        return

    st.markdown('<div class="section-title">统计推演</div>', unsafe_allow_html=True)
    if st.button("启动统计推演", use_container_width=True, key=f"basic_{choice}"):
        st.session_state["basic_click_count"] = st.session_state.get("basic_click_count", 0) + 1

    if st.session_state.get("basic_click_count", 0) > 0:
        for item in get_basic_predictions(df.head(view_limit), choice, st.session_state["basic_click_count"]):
            render_prediction_card(item["name"], item["desc"], item["red"], item["blue"], choice)

    st.markdown('<div class="section-title">窗口概率画像</div>', unsafe_allow_html=True)
    bet_count = st.number_input("评估注数", min_value=1, max_value=500, value=10, step=1, key=f"bet_count_{choice}")
    profile = build_probability_profile(df.head(view_limit), choice, bet_count=bet_count)
    if profile:
        probability_metrics = [
            {"label": "理论组合数", "value": f"{profile['total_combinations']:,}", "hint": f"基于近 {profile['window_size']} 期窗口", "color": "#81cfff"},
            {"label": "和值期望", "value": f"{profile['expected_sum']:.1f}", "hint": "真实窗口均值", "color": "#7dffa2"},
            {"label": "和值方差", "value": f"{profile['variance']:.1f}", "hint": f"标准差 {profile['std_dev']:.1f}", "color": "#ff8a73"},
            {"label": "风险指数", "value": f"{profile['risk_index']:.3f}", "hint": "标准差 / 期望", "color": "#ffb4a5"},
        ]
        render_metric_cards(probability_metrics)

        st.markdown(
            f"""
            <div class="glass-card result-card">
              <div class="result-title">真实窗口概率说明</div>
              <div class="result-desc">以下结果严格基于当前期数窗口 {view_limit} 期历史样本，不读取更长样本，不做伪随机修饰。</div>
              <div class="code-line">单注命中概率：{profile['single_hit_probability']:.10f} | {bet_count} 注不重复命中概率：{profile['no_repeat_multi_probability']:.10f} | {bet_count} 注可重复命中概率：{profile['repeatable_multi_probability']:.10f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="glass-card result-card">
              <div class="result-title">结构分布</div>
              <div class="result-desc">奇偶与重号概率按当前彩种的真实组合空间计算。</div>
              <div class="code-line">主奇偶结构：{profile['common_odd_count']} 奇 | 概率 {profile['odd_probability']:.6f} | 常见重号数：{profile['common_repeat_count']} | 概率 {profile['repeat_probability']:.6f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-title">冷热修正排名</div>', unsafe_allow_html=True)
        hot_cold_df = pd.DataFrame(profile["corrected_rank"][:15]).copy()
        hot_cold_df["号码"] = hot_cold_df["号码"].map(lambda x: format_number(x, choice))
        hot_cold_df["修正概率"] = hot_cold_df["修正概率"].map(lambda x: f"{x:.6f}")
        st.dataframe(hot_cold_df, use_container_width=True, hide_index=True)

        if profile["back_summary"]:
            st.markdown('<div class="section-title">后区频次</div>', unsafe_allow_html=True)
            back_df = pd.DataFrame(profile["back_summary"][:8]).copy()
            back_df["号码"] = back_df["号码"].map(lambda x: format_number(x, choice))
            st.dataframe(back_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">种子号衍生</div>', unsafe_allow_html=True)
    seed_text = st.text_input("输入心水种子号", placeholder="例如：06 18 23", key=f"seed_text_{choice}")
    if st.button("执行种子衍生", use_container_width=True, key=f"seed_btn_{choice}"):
        st.session_state[f"seed_result_{choice}"] = derive_seed_combinations(df.head(view_limit), choice, seed_text)

    seed_result = st.session_state.get(f"seed_result_{choice}")
    if seed_result:
        if seed_result["valid_seeds"]:
            st.caption("有效种子：" + " ".join(format_number(n, choice) for n in seed_result["valid_seeds"]))
        else:
            st.caption("未检测到有效种子，将按当前窗口模型自动推导。")

        render_prediction_card("核心胆码", "种子权重、频次、遗漏与转移得分交叉后取 1 位。", seed_result["core"], [], choice)
        render_prediction_card("精简组合", "适合小范围试探的三位骨架。", seed_result["compact"], [], choice)
        render_prediction_card("标准组合", "按当前彩种前区数量输出。", seed_result["standard"], [], choice)
        render_prediction_card("扩容复式", "标准组基础上增加两个覆盖位。", seed_result["expanded"], [], choice, tone="accent")

        seed_df = pd.DataFrame(seed_result["score_rows"][:12]).copy()
        seed_df["号码"] = seed_df["号码"].map(lambda x: format_number(x, choice))
        seed_df["得分"] = seed_df["得分"].map(lambda x: f"{x:.4f}")
        st.dataframe(seed_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">高阶公式</div>', unsafe_allow_html=True)
    if not st.session_state.get("vip_unlocked"):
        render_unlock_panel("解锁完整公式模块", key_prefix="formula")
    else:
        st.info(f"已激活，剩余 {st.session_state.get('days_left', '未知')} 天")
        if st.button("生成高阶推演", use_container_width=True, key=f"adv_{choice}"):
            st.session_state["adv_click_count"] = st.session_state.get("adv_click_count", 0) + 1
        if st.session_state.get("adv_click_count", 0) > 0:
            for item in get_advanced_predictions(df.head(view_limit), choice, st.session_state["adv_click_count"]):
                render_prediction_card(item["name"], item["desc"], item["red"], item["blue"], choice, tone=item.get("tone", "primary"))

        st.markdown('<div class="section-title">自建数据沙盘</div>', unsafe_allow_html=True)
        sandbox_choice = st.selectbox("沙盘彩种", ["快乐8", "双色球", "大乐透", "七星彩", "排列5", "排列3", "福彩3D"], key="sandbox_choice")
        uploaded_file = st.file_uploader("上传历史数据表格", type=["csv", "xlsx", "xls"], key="sandbox_file")
        sandbox_text = st.text_area("或手动粘贴历史开奖号码", height=120, placeholder="每行一期，例如：01 02 03 04 05 06 07", key="sandbox_text")

        if st.button("启动沙盘推演", use_container_width=True, key="sandbox_run"):
            custom_df = None
            if uploaded_file is not None:
                try:
                    custom_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                    st.success(f"成功读取 {len(custom_df)} 行表格数据。")
                except Exception as exc:
                    st.error(f"表格解析失败：{exc}")
            elif sandbox_text.strip():
                lines = [line.strip() for line in sandbox_text.strip().splitlines() if line.strip()]
                parsed_rows = []
                for idx, line in enumerate(lines):
                    nums = [int(n) for n in re.findall(r"\d+", line)]
                    if nums:
                        parsed_rows.append([len(lines) - idx] + nums)
                if parsed_rows:
                    custom_df = pd.DataFrame(parsed_rows)
                    st.success(f"成功提取 {len(custom_df)} 期自定义样本。")
                else:
                    st.error("未识别到有效数字。")
            else:
                st.warning("请先上传表格或粘贴历史数据。")

            if custom_df is not None:
                seed = int(time.time()) + random.randint(1, 9999)
                results = get_advanced_predictions(custom_df, sandbox_choice, seed)
                st.session_state["sandbox_results"] = (sandbox_choice, results)

        if st.session_state.get("sandbox_results"):
            sandbox_result_choice, sandbox_results = st.session_state["sandbox_results"]
            for item in sandbox_results:
                render_prediction_card(item["name"], item["desc"], item["red"], item["blue"], sandbox_result_choice, tone=item.get("tone", "primary"))

        st.markdown('<div class="section-title">专家组合压缩</div>', unsafe_allow_html=True)
        compress_choice = st.selectbox("压缩彩种", ["双色球", "大乐透", "福彩3D", "排列3"], key="compress_choice")
        compress_cfg = {
            "双色球": {"r_max": 33, "r_need": 6, "b_max": 16, "b_need": 1},
            "大乐透": {"r_max": 35, "r_need": 5, "b_max": 12, "b_need": 2},
            "福彩3D": {"r_max": 9, "r_need": 3, "b_max": 0, "b_need": 0},
            "排列3": {"r_max": 9, "r_need": 3, "b_max": 0, "b_need": 0},
        }[compress_choice]
        r_range = list(range(1, compress_cfg["r_max"] + 1)) if compress_cfg["r_max"] > 10 else list(range(10))
        c1, c2 = st.columns(2)
        with c1:
            red_dan = st.multiselect("前区胆码", r_range, key=f"red_dan_{compress_choice}")
            red_tuo = st.multiselect("前区拖码", [n for n in r_range if n not in red_dan], key=f"red_tuo_{compress_choice}")
        with c2:
            if compress_cfg["b_max"] > 0:
                b_range = list(range(1, compress_cfg["b_max"] + 1))
                blue_dan = st.multiselect("后区胆码", b_range, key=f"blue_dan_{compress_choice}")
                blue_tuo = st.multiselect("后区拖码", [n for n in b_range if n not in blue_dan], key=f"blue_tuo_{compress_choice}")
            else:
                st.info("该彩种无后区。")
                blue_dan, blue_tuo = [], []

        all_012 = ["自适应"]
        if compress_cfg["r_need"] == 5:
            all_012 += ["2:2:1", "2:1:2", "1:2:2", "3:1:1", "1:3:1", "1:1:3", "4:1:0", "4:0:1", "0:4:1", "1:4:0"]
        elif compress_cfg["r_need"] == 6:
            all_012 += ["2:2:2", "3:2:1", "3:1:2", "1:2:3", "2:1:3", "2:3:1", "1:3:2", "4:1:1", "1:4:1"]
        target_012 = st.selectbox("012 路比例", all_012, key=f"target_012_{compress_choice}")

        route_stats = get_012_route_stats(df.head(view_limit), compress_choice) if compress_choice == choice else None
        if route_stats:
            route_rows = route_stats["rows"]
            selected_route = next((row for row in route_rows if row["route"] == target_012), None)
            if selected_route:
                route_metrics = [
                    {"label": "理论一等奖占比", "value": f"{selected_route['theoretical_ratio'] * 100:.2f}%", "hint": f"{selected_route['theoretical_count']:,} 个组合", "color": "#81cfff"},
                    {"label": f"近{view_limit}期实际占比", "value": f"{selected_route['actual_ratio'] * 100:.1f}%", "hint": f"出现 {selected_route['actual_count']} 次", "color": "#7dffa2"},
                ]
                render_metric_cards(route_metrics)
            top_route_df = pd.DataFrame(route_rows[:8]).copy()
            top_route_df["理论占比"] = top_route_df["theoretical_ratio"].map(lambda x: f"{x * 100:.2f}%")
            top_route_df["窗口占比"] = top_route_df["actual_ratio"].map(lambda x: f"{x * 100:.1f}%")
            top_route_df = top_route_df[["route", "理论占比", "actual_count", "窗口占比"]]
            top_route_df.columns = ["012结构", "理论占比", "窗口次数", "窗口占比"]
            st.dataframe(top_route_df, use_container_width=True, hide_index=True)
        elif compress_choice != choice:
            st.caption("012窗口占比需与顶部当前彩种一致；理论过滤仍可正常使用。")

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            use_012 = st.checkbox("启用012过滤", value=True, key=f"use_012_{compress_choice}")
        with fc2:
            kill_triple = st.checkbox("过滤3连号", value=True, key=f"kill_triple_{compress_choice}")
        with fc3:
            unique_tail = st.checkbox("过滤同尾", value=False, key=f"unique_tail_{compress_choice}")

        if st.button("启动组合压缩", use_container_width=True, key=f"compress_btn_{compress_choice}"):
            st.session_state[f"compress_result_{compress_choice}"] = expert_compress_combinations(
                compress_choice,
                red_dan,
                red_tuo,
                blue_dan,
                blue_tuo,
                target_012=target_012,
                use_012=use_012,
                kill_triple=kill_triple,
                unique_tail=unique_tail,
            )

        compress_result = st.session_state.get(f"compress_result_{compress_choice}")
        if compress_result:
            if not compress_result.get("ok"):
                st.error(compress_result["message"])
            else:
                st.success(f"压缩完成：前区 {compress_result['red_count']} 组，后区 {compress_result['blue_count']} 组，共 {compress_result['total_count']} 注，预算 {compress_result['budget']} 元。")
                for idx, item in enumerate(compress_result["samples"], start=1):
                    red_txt = " ".join(format_number(n, compress_choice) for n in item["red"])
                    blue_txt = " | " + " ".join(format_number(n, compress_choice) for n in item["blue"]) if item["blue"] else ""
                    st.code(f"精华 {idx:02d}: {red_txt}{blue_txt}", language="text")

    render_bottom_nav("公式")


def render_tactical_section(df_base, choice, view_limit):
    if not st.session_state.get("vip_unlocked"):
        render_unlock_panel("解锁手动样本反向分析", key_prefix="tactical")
        render_bottom_nav("录入")
        return

    if choice not in ["双色球", "大乐透"]:
        st.warning("手动样本录入当前仅支持双色球和大乐透。")
        render_bottom_nav("录入")
        return

    is_dlt = choice == "大乐透"

    st.markdown('<div class="section-title">手动样本录入</div>', unsafe_allow_html=True)
    raw_text = st.text_area(
        "粘贴样本号码",
        height=140,
        placeholder="例如：01 02 03 04 05 + 06 07\\n08 12 19 23 31 + 03 11",
    )

    if st.button("启动样本分析", use_container_width=True, key="tactical_run"):
        history_limit = str(view_limit)
        recent_red_pool = None
        recent_blue_pool = None
        history_tongqi_pool = None
        weekday_pool = None
        weekday_blue_pool = None

        if df_base is not None and not df_base.empty:
            front_counts, back_counts = calculate_frequencies(df_base.head(view_limit), is_dlt=is_dlt)
            recent_red_pool = [x[0] for x in front_counts.most_common(15)]
            recent_blue_pool = [x[0] for x in back_counts.most_common(6)]
            recent_red_counts = dict(front_counts)
            recent_blue_counts = dict(back_counts)
        else:
            recent_red_counts = {}
            recent_blue_counts = {}

        result = run_tactical_manual_analysis(
            raw_text,
            is_dlt=is_dlt,
            history_limit=history_limit,
            recent_red_pool=recent_red_pool,
            recent_blue_pool=recent_blue_pool,
            history_tongqi_pool=history_tongqi_pool,
            weekday_pool=weekday_pool,
            weekday_blue_pool=weekday_blue_pool,
            recent_red_counts=recent_red_counts,
            recent_blue_counts=recent_blue_counts,
        )
        st.session_state["tactical_result"] = {
            "choice": choice,
            "view_limit": view_limit,
            "raw_text": raw_text,
            "result": result,
        }

    tactical_state = st.session_state.get("tactical_result")
    result = tactical_state.get("result") if isinstance(tactical_state, dict) else tactical_state
    if isinstance(tactical_state, dict) and result:
        if tactical_state.get("choice") != choice or tactical_state.get("view_limit") != view_limit or tactical_state.get("raw_text") != raw_text:
            st.warning("当前显示的是上一次分析结果；彩种、期数或输入内容已变化，请重新点击“启动样本分析”。")
    if result and result.get("ok"):
        st.markdown('<div class="section-title">样本核对</div>', unsafe_allow_html=True)
        st.code(
            "红球: " + " ".join([f"{x:02d}" for x in result["red_nums"]]) +
            (("\n蓝球: " + " ".join([f"{x:02d}" for x in result["blue_nums"]])) if result["blue_nums"] else "")
        )

        heat_metrics = [
            {"label": "红球样本数", "value": len(result["red_nums"]), "hint": "当前录入前区样本量", "color": "#81cfff"},
            {"label": "蓝球样本数", "value": len(result["blue_nums"]), "hint": "当前录入后区样本量", "color": "#ff8a73"},
            {"label": "高热号数", "value": len(result["hot_nums"]), "hint": "高频撞车区", "color": "#ffb4a5"},
            {"label": "潜伏号数", "value": len(result["potential_nums"]), "hint": "冷区与单次样本", "color": "#7dffa2"},
        ]
        render_metric_cards(heat_metrics)

        def render_heat_matrix(max_num, counts_dict, is_blue=False):
            boxes = []
            max_freq = max(counts_dict.values()) if counts_dict else 1
            if max_freq <= 0:
                max_freq = 1
            for i in range(1, max_num + 1):
                freq = counts_dict.get(i, 0)
                ratio = freq / max_freq
                if is_blue:
                    bg = "#002266" if ratio > 0.7 else ("#0052D4" if ratio > 0.4 else ("#64B5F6" if freq > 0 else "#1e293b"))
                else:
                    bg = "#B31217" if ratio > 0.7 else ("#FF4B2B" if ratio > 0.4 else ("#FF8A75" if freq > 0 else "#1e293b"))
                boxes.append(f'<div class="heat-box" style="background:{bg};"><b>{i:02d}</b><span>{freq}次</span></div>')
            st.markdown(f'<div class="small-grid">{"".join(boxes)}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">反向结果</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">红球热力矩阵</div>', unsafe_allow_html=True)
        render_heat_matrix(35 if is_dlt else 33, result["counts_red"], is_blue=False)
        if result["counts_blue"]:
            st.markdown('<div class="section-title">蓝球热力矩阵</div>', unsafe_allow_html=True)
            render_heat_matrix(12 if is_dlt else 16, result["counts_blue"], is_blue=True)

        render_prediction_card("高热区域", "高频撞车样本，优先规避。", result["hot_nums"], [], choice, tone="accent")
        render_prediction_card("潜伏区域", "冷区与单次出现样本的并集。", result["potential_nums"][:6], [], choice)
        render_prediction_card("偏移阵地", "围绕高热样本做左右偏移。", result["offset_recommend"][:6], [], choice)
        render_prediction_card("主推单式", "多维交集后的主推参考。", result["final_math_reds"], result["final_math_blues"], choice)
        render_prediction_card("复式扩容", f"理论组合 {result['zhusu']} 注。", result["fushi_math_reds"], result["fushi_math_blues"], choice, tone="accent")

        st.markdown('<div class="section-title">胆拖全托预算</div>', unsafe_allow_html=True)
        if is_dlt:
            d4 = result["dan_primary"]
            d3 = result["dan_secondary"]
            d4_red_bets = calculate_bets(35 - len(d4), 5 - len(d4))
            d3_red_bets = calculate_bets(35 - len(d3), 5 - len(d3))
            blue_all = calculate_bets(12, 2)
            plans = [
                {
                    "title": "大乐透四胆全托",
                    "dan": d4,
                    "red_bets": d4_red_bets,
                    "fixed_blue_budget": d4_red_bets * 2,
                    "all_blue_bets": d4_red_bets * blue_all,
                    "all_blue_budget": d4_red_bets * blue_all * 2,
                    "desc": "前区锁定 4 个胆码，其余 31 个红球全托补 1 位。",
                },
                {
                    "title": "大乐透三胆全托",
                    "dan": d3,
                    "red_bets": d3_red_bets,
                    "fixed_blue_budget": d3_red_bets * 2,
                    "all_blue_bets": d3_red_bets * blue_all,
                    "all_blue_budget": d3_red_bets * blue_all * 2,
                    "desc": "前区锁定 3 个胆码，其余 32 个红球全托补 2 位。",
                },
            ]
        else:
            d5 = result["dan_primary"]
            d5_red_bets = calculate_bets(33 - len(d5), 6 - len(d5))
            plans = [
                {
                    "title": "双色球五胆全托",
                    "dan": d5,
                    "red_bets": d5_red_bets,
                    "fixed_blue_budget": d5_red_bets * 2,
                    "all_blue_bets": d5_red_bets * 16,
                    "all_blue_budget": d5_red_bets * 16 * 2,
                    "desc": "前区锁定 5 个胆码，其余 28 个红球全托补 1 位。",
                }
            ]

        for plan in plans:
            dan_txt = " ".join(format_number(n, choice) for n in plan["dan"])
            st.markdown(
                f"""
                <div class="glass-card result-card">
                  <div class="result-title">{plan["title"]}</div>
                  <div class="result-desc">{plan["desc"]}</div>
                  <div class="code-line">胆码：{dan_txt}</div>
                  <div class="result-desc" style="margin-top:10px;">前区组合：{plan["red_bets"]:,} 注 | 后区精选预算：{plan["fixed_blue_budget"]:,} 元 | 后区全托：{plan["all_blue_bets"]:,} 注 / {plan["all_blue_budget"]:,} 元</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    elif result and not result.get("ok"):
        st.error(result["message"])
    render_bottom_nav("录入")


def render_lobby(choice="双色球"):
    st.markdown('<div class="section-title">动态大厅</div>', unsafe_allow_html=True)
    usage = get_usage_snapshot(choice)
    lobby_metrics = [
        {"label": "今日访问", "value": usage["today_visits"], "hint": "当前实例统计", "color": "#81cfff"},
        {"label": "在线热度", "value": usage["online_estimate"], "hint": "实时波动估算", "color": "#7dffa2"},
    ]
    render_metric_cards(lobby_metrics)

    render_countdown_widget(choice)

    st.markdown('<div class="section-title">系统公告</div>', unsafe_allow_html=True)
    notices = [
        "窗口概率画像已接入期望、方差、风险指数。",
        "012 路支持理论一等奖占比与当前窗口实际占比。",
        "手动录入已接入热力矩阵与胆拖预算。",
    ]
    for notice in notices:
        st.markdown(f'<div class="glass-card result-card"><div class="muted">{notice}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">用户反馈</div>', unsafe_allow_html=True)
    comments = load_comments(limit=20)
    if comments:
        for item in comments:
            nickname = item.get("昵称") or item.get("nickname") or item.get("用户") or "游客"
            content = item.get("内容") or item.get("comment") or ""
            created_at = item.get("时间") or item.get("time") or ""
            st.markdown(
                f'<div class="glass-card result-card"><div class="result-title">{nickname}</div><div class="result-desc">{created_at}</div><div class="muted">{content}</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("暂无公开反馈。配置 Google 表格 Lotto_Comments 后可启用真实留言墙。")

    with st.expander("发布反馈", expanded=False):
        nickname = st.text_input("昵称（可选）", key="comment_nickname")
        content = st.text_area("内容", max_chars=120, key="comment_content")
        if st.button("提交反馈", use_container_width=True, key="submit_comment"):
            ok, message = submit_comment(nickname, content, choice)
            if ok:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    st.markdown('<div class="section-title">联络与说明</div>', unsafe_allow_html=True)
    render_unlock_panel("授权与服务", key_prefix="lobby")
    st.markdown(
        """
        <div class="glass-card">
          <div class="result-title">说明</div>
          <div class="muted">
            本系统展示的统计、路径、AC 约束、状态转移、过滤与压缩结果，仅作为样本分析参考。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_bottom_nav("大厅")
