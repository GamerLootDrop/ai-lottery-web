import math
import random
import re
import time
import itertools
from collections import Counter

import pandas as pd

from lottery_rules import format_number, get_lottery_rules, should_zero_pad


DRAW_WEEKDAYS = {
    "双色球": [1, 3, 6],
    "大乐透": [0, 2, 5],
    "七星彩": [1, 4, 6],
    "七乐彩": [0, 2, 4],
    "福彩3D": [0, 1, 2, 3, 4, 5, 6],
    "排列3": [0, 1, 2, 3, 4, 5, 6],
    "排列5": [0, 1, 2, 3, 4, 5, 6],
    "快乐8": [0, 1, 2, 3, 4, 5, 6],
}


def calculate_ac_value(nums):
    diffs = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    return max(0, len(diffs) - (len(nums) - 1))


def render_number_text(r_res, b_res, choice):
    text = " ".join([format_number(n, choice) for n in r_res])
    if b_res:
        text += " | " + " ".join([format_number(n, choice) for n in b_res])
    return text


def extract_real_stats(df_view, pool_r, count_r, pool_b, count_b, variation_seed=0):
    random.seed(int(time.time()) + variation_seed)
    hot_r, cold_r, hot_b, cold_b = [], [], [], []

    if df_view is None or df_view.empty:
        return sorted(random.sample(pool_r, count_r)), sorted(random.sample(pool_r, count_r)), [], []

    try:
        safe_df = df_view.apply(pd.to_numeric, errors="coerce").fillna(-1).astype(int)
        r_raw = safe_df.iloc[:, 1 : 1 + count_r].values.flatten().tolist()
        r_history = [x for x in r_raw if x in pool_r]
        r_counter = Counter(r_history)

        most_common = [x[0] for x in r_counter.most_common()]
        base_hot = most_common[: count_r + 3]
        hot_r = random.sample(base_hot, min(count_r, len(base_hot)))
        while len(hot_r) < count_r:
            cand = random.choice(pool_r)
            if cand not in hot_r:
                hot_r.append(cand)

        missing = [x for x in pool_r if x not in r_counter]
        least_common = missing + [x[0] for x in r_counter.most_common()[: -count_r - 4 : -1]]
        least_common = list(dict.fromkeys(least_common))
        cold_r = random.sample(least_common, min(count_r, len(least_common)))
        while len(cold_r) < count_r:
            cand = random.choice(pool_r)
            if cand not in cold_r:
                cold_r.append(cand)

        if count_b > 0:
            b_raw = safe_df.iloc[:, 1 + count_r : 1 + count_r + count_b].values.flatten().tolist()
            b_history = [x for x in b_raw if x in pool_b]
            b_counter = Counter(b_history)

            b_most = [x[0] for x in b_counter.most_common()]
            hot_b = random.sample(b_most[: count_b + 2], min(count_b, len(b_most[: count_b + 2])))
            while len(hot_b) < count_b:
                cand = random.choice(pool_b)
                if cand not in hot_b:
                    hot_b.append(cand)

            b_missing = [x for x in pool_b if x not in b_counter]
            b_least = list(dict.fromkeys(b_missing + [x[0] for x in b_counter.most_common()[: -count_b - 3 : -1]]))
            cold_b = random.sample(b_least[: count_b + 2], min(count_b, len(b_least[: count_b + 2])))
            while len(cold_b) < count_b:
                cand = random.choice(pool_b)
                if cand not in cold_b:
                    cold_b.append(cand)

        return sorted(hot_r), sorted(cold_r), sorted(hot_b), sorted(cold_b)
    except Exception:
        return sorted(random.sample(pool_r, count_r)), sorted(random.sample(pool_r, count_r)), [], []


def get_basic_predictions(df_view, choice, click_count):
    sets = []
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    hot_r, cold_r, hot_b, cold_b = extract_real_stats(df_view, pool_r, count_r, pool_b, count_b, click_count)

    sets.append(
        {
            "name": "极热寻踪",
            "desc": f"统计学排查，分析近 {len(df_view)} 期高频热点。",
            "red": hot_r,
            "blue": hot_b,
            "text": render_number_text(hot_r, hot_b, choice),
        }
    )
    sets.append(
        {
            "name": "绝地反弹",
            "desc": "均值回归，追踪近期遗漏偏大的冷门样本。",
            "red": cold_r,
            "blue": cold_b,
            "text": render_number_text(cold_r, cold_b, choice),
        }
    )

    mix_r = sorted(list(set(hot_r[: max(1, count_r // 2)] + cold_r[: max(1, count_r // 3)])))
    while len(mix_r) < count_r:
        cand = random.choice(pool_r)
        if cand not in mix_r:
            mix_r.append(cand)
    mix_r = sorted(mix_r[:count_r])

    mix_b = []
    if count_b > 0:
        mix_b = sorted(list(set(hot_b[: max(1, count_b // 2)] + cold_b[: max(1, count_b // 2)])))
        while len(mix_b) < count_b:
            cand = random.choice(pool_b)
            if cand not in mix_b:
                mix_b.append(cand)
        mix_b = sorted(mix_b[:count_b])

    sets.append(
        {
            "name": "黄金均衡",
            "desc": "自然分布下的冷热混合配比。",
            "red": mix_r,
            "blue": mix_b,
            "text": render_number_text(mix_r, mix_b, choice),
        }
    )
    return sets


def real_markov_core(history_rows, pool, count, rng, order=1):
    transition_matrix = {n: Counter() for n in pool}
    for i in range(len(history_rows) - order):
        current_state = history_rows[i]
        future_state = history_rows[i + order]
        for cb in current_state:
            if cb in pool:
                for fb in future_state:
                    if fb in pool:
                        transition_matrix[cb][fb] += 1

    if not history_rows:
        return sorted(rng.sample(pool, count))

    latest_state = [b for b in history_rows[-1] if b in pool]
    next_probs = Counter()
    for lb in latest_state:
        for nb, freq in transition_matrix[lb].items():
            next_probs[nb] += freq

    candidates = [x[0] for x in next_probs.most_common()]
    top_k_pool = candidates[: count + 5]
    if len(top_k_pool) < count:
        missing = [x for x in pool if x not in top_k_pool]
        top_k_pool.extend(rng.sample(missing, min(count - len(top_k_pool), len(missing))))

    return sorted(rng.sample(top_k_pool, count))


def get_advanced_predictions(df_view, choice, click_count):
    sets = []
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    rng = random.Random(int(time.time()) + click_count)

    safe_df = df_view.apply(pd.to_numeric, errors="coerce").fillna(-1).astype(int)
    r_history = safe_df.iloc[:, 1 : 1 + count_r].values.tolist()
    r_history.reverse()

    b_history = []
    if count_b > 0:
        b_history = safe_df.iloc[:, 1 + count_r : 1 + count_r + count_b].values.tolist()
        b_history.reverse()

    for idx in range(3):
        r_res = real_markov_core(r_history, pool_r, count_r, rng, order=1)
        b_res = real_markov_core(b_history, pool_b, count_b, rng, order=1) if count_b > 0 else []
        sets.append(
            {
                "name": f"马尔科夫链 {idx + 1}",
                "desc": f"状态转移建模 | AC 值 {calculate_ac_value(r_res)}",
                "red": r_res,
                "blue": b_res,
                "text": render_number_text(r_res, b_res, choice),
                "tone": "primary",
            }
        )

    for idx in range(3):
        actual_order = 12 if len(r_history) > 15 else 1
        r_res = real_markov_core(r_history, pool_r, count_r, rng, order=actual_order)
        b_res = real_markov_core(b_history, pool_b, count_b, rng, order=actual_order) if count_b > 0 else []
        sets.append(
            {
                "name": f"AC12 高阶 {idx + 1}",
                "desc": f"高阶跨度 {actual_order} 期 | 样本 {len(r_history)}",
                "red": r_res,
                "blue": b_res,
                "text": render_number_text(r_res, b_res, choice),
                "tone": "accent",
            }
        )

    return sets


def parse_red_blue_from_text(text, is_dlt=True):
    red_balls = []
    blue_balls = []
    text_clean = text.replace("：", ":").replace("，", ",").replace("；", ";").replace("—", "-")
    lines = re.split(r"[\n\r;,\t]", text_clean)

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if any(sep in line for sep in ["+", "-", "|", "蓝", "后"]):
            parts = re.split(r"[\+\-\|蓝后]", line, maxsplit=1)
            r_part = re.findall(r"\b(0?[1-9]|[1-2][0-9]|3[0-5])\b", parts[0])
            if len(parts) > 1:
                if is_dlt:
                    b_part = re.findall(r"\b(0?[1-9]|1[0-2])\b", parts[1])
                else:
                    b_part = re.findall(r"\b(0?[1-9]|1[0-6])\b", parts[1])
            else:
                b_part = []

            red_balls.extend([int(x) for x in r_part if (is_dlt and int(x) <= 35) or (not is_dlt and int(x) <= 33)])
            blue_balls.extend([int(x) for x in b_part])
        else:
            all_nums = re.findall(r"\b([0-3]?[0-9])\b", line)
            all_nums = [int(x) for x in all_nums if 1 <= int(x) <= 35]
            if not all_nums:
                continue

            if is_dlt and len(all_nums) >= 7:
                if all_nums[-1] <= 12 and all_nums[-2] <= 12:
                    red_balls.extend([x for x in all_nums[:-2] if x <= 35])
                    blue_balls.extend(all_nums[-2:])
                else:
                    red_balls.extend([x for x in all_nums if x <= 35])
            elif (not is_dlt) and len(all_nums) >= 7:
                if all_nums[-1] <= 16:
                    red_balls.extend([x for x in all_nums[:-1] if x <= 33])
                    blue_balls.extend([all_nums[-1]])
                else:
                    red_balls.extend([x for x in all_nums if x <= 33])
            else:
                if is_dlt:
                    red_balls.extend([x for x in all_nums if x <= 35])
                else:
                    red_balls.extend([x for x in all_nums if x <= 33])

    if not blue_balls:
        all_matches = re.findall(r"\b(0?[1-9]|[1-2][0-9]|3[0-5])\b", text)
        red_balls = [int(x) for x in all_matches if (is_dlt and int(x) <= 35) or (not is_dlt and int(x) <= 33)]

    return red_balls, blue_balls


def calculate_frequencies(df, is_dlt=True):
    if df is None or df.empty:
        return Counter(), Counter()

    if is_dlt:
        default_front_cols = ["前1", "前2", "前3", "前4", "前5"]
        default_back_cols = ["后1", "后2"]
        front_max, back_max = 35, 12
    else:
        default_front_cols = ["前1", "前2", "前3", "前4", "前5", "前6"]
        default_back_cols = ["后1"]
        front_max, back_max = 33, 16

    if all(col in df.columns for col in default_front_cols):
        front_cols = default_front_cols
        back_cols = [col for col in default_back_cols if col in df.columns]
    else:
        count_r = 5 if is_dlt else 6
        count_b = 2 if is_dlt else 1
        front_cols, back_cols = _draw_columns(df, count_r, count_b)

    if not front_cols:
        return Counter(), Counter()

    front_df = df[front_cols].apply(pd.to_numeric, errors="coerce").fillna(-1).astype(int)
    front_nums = front_df.values.flatten()
    if back_cols:
        back_df = df[back_cols].apply(pd.to_numeric, errors="coerce").fillna(-1).astype(int)
        back_nums = back_df.values.flatten()
    else:
        back_nums = []

    front_nums = [int(n) for n in front_nums if 1 <= int(n) <= front_max]
    back_nums = [int(n) for n in back_nums if 1 <= int(n) <= back_max]
    front_counts, back_counts = Counter(front_nums), Counter(back_nums)
    for i in range(1, front_max + 1):
        front_counts.setdefault(i, 0)
    for i in range(1, back_max + 1):
        back_counts.setdefault(i, 0)
    return front_counts, back_counts


def calculate_bets(n, r):
    return math.comb(n, r) if r <= n and r >= 0 else 0


def _safe_div(numerator, denominator, default=0):
    return numerator / denominator if denominator else default


def _draw_columns(df, count_r, count_b=0):
    ball_cols = [c for c in df.columns if str(c).startswith("b_")]
    if len(ball_cols) >= count_r + count_b:
        return ball_cols[:count_r], ball_cols[count_r : count_r + count_b]
    numeric_cols = [
        c
        for c in df.columns
        if c not in ["期号", "日期", "日期_解析", "星期"] and pd.api.types.is_numeric_dtype(df[c])
    ]
    return numeric_cols[:count_r], numeric_cols[count_r : count_r + count_b]


def _odd_even_distribution_probability(pool, draw_count, observed_odd_count):
    odd_total = sum(1 for n in pool if n % 2 == 1)
    even_total = len(pool) - odd_total
    total = calculate_bets(len(pool), draw_count)
    hit = calculate_bets(odd_total, observed_odd_count) * calculate_bets(even_total, draw_count - observed_odd_count)
    return _safe_div(hit, total)


def _repeat_distribution_probability(pool_size, draw_count, repeat_count):
    total = calculate_bets(pool_size, draw_count)
    hit = calculate_bets(draw_count, repeat_count) * calculate_bets(pool_size - draw_count, draw_count - repeat_count)
    return _safe_div(hit, total)


def build_probability_profile(df_view, choice, bet_count=1):
    """Build a real window-based probability profile from the selected historical period."""
    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    if df_view is None or df_view.empty:
        return None

    safe_df = df_view.apply(pd.to_numeric, errors="coerce").fillna(-1).astype(int)
    front_cols, back_cols = _draw_columns(safe_df, count_r, count_b)
    draw_cols = front_cols + back_cols
    window_size = len(safe_df)

    sums = safe_df[draw_cols].sum(axis=1)
    expected_sum = float(sums.mean())
    variance = float(((sums - expected_sum) ** 2).mean())
    std_dev = math.sqrt(variance)
    risk_index = _safe_div(std_dev, expected_sum)

    total_combinations = calculate_bets(len(pool_r), count_r)
    if count_b > 0:
        total_combinations *= calculate_bets(len(pool_b), count_b)
    single_hit_probability = _safe_div(1, total_combinations)
    no_repeat_multi_probability = min(_safe_div(bet_count, total_combinations), 1)
    repeatable_multi_probability = 1 - ((1 - single_hit_probability) ** bet_count)

    front_values = safe_df[front_cols].values.flatten().tolist()
    front_values = [n for n in front_values if n in pool_r]
    front_counter = Counter(front_values)
    average_frequency = _safe_div(sum(front_counter.values()), len(pool_r))
    max_frequency = max(front_counter.values()) if front_counter else 0

    scored_numbers = []
    for num in pool_r:
        freq = front_counter.get(num, 0)
        omission = 0
        for _, row in safe_df.iterrows():
            row_nums = [int(row[col]) for col in front_cols]
            if num in row_nums:
                break
            omission += 1

        base_p = _safe_div(count_r, len(pool_r))
        if freq <= average_frequency:
            corrected = base_p * (1 + _safe_div(omission, max(window_size, 1)))
            zone = "冷修正"
        else:
            corrected = base_p * (1 - 0.45 * _safe_div(freq - average_frequency, max(max_frequency, 1)))
            zone = "热降权"

        corrected = max(corrected, 0)
        scored_numbers.append(
            {
                "号码": num,
                "频次": freq,
                "遗漏": omission,
                "修正概率": corrected,
                "状态": zone,
            }
        )

    corrected_rank = sorted(scored_numbers, key=lambda x: (x["修正概率"], x["遗漏"], -x["频次"]), reverse=True)

    odd_counts = []
    repeat_counts = []
    for idx, (_, row) in enumerate(safe_df.iterrows()):
        nums = [int(row[col]) for col in front_cols]
        odd_counts.append(sum(1 for n in nums if n % 2 == 1))
        if idx + 1 < len(safe_df):
            prev_nums = set(int(safe_df.iloc[idx + 1][col]) for col in front_cols)
            repeat_counts.append(len(set(nums).intersection(prev_nums)))

    common_odd_count = Counter(odd_counts).most_common(1)[0][0] if odd_counts else 0
    common_repeat_count = Counter(repeat_counts).most_common(1)[0][0] if repeat_counts else 0
    odd_probability = _odd_even_distribution_probability(pool_r, count_r, common_odd_count)
    repeat_probability = _repeat_distribution_probability(len(pool_r), count_r, common_repeat_count)

    back_summary = []
    if count_b > 0 and back_cols:
        back_values = safe_df[back_cols].values.flatten().tolist()
        back_values = [n for n in back_values if n in pool_b]
        back_counter = Counter(back_values)
        back_summary = [
            {"号码": num, "频次": back_counter.get(num, 0)}
            for num in pool_b
        ]
        back_summary = sorted(back_summary, key=lambda x: x["频次"], reverse=True)

    return {
        "window_size": window_size,
        "total_combinations": total_combinations,
        "single_hit_probability": single_hit_probability,
        "no_repeat_multi_probability": no_repeat_multi_probability,
        "repeatable_multi_probability": repeatable_multi_probability,
        "expected_sum": expected_sum,
        "variance": variance,
        "std_dev": std_dev,
        "risk_index": risk_index,
        "common_odd_count": common_odd_count,
        "odd_probability": odd_probability,
        "common_repeat_count": common_repeat_count,
        "repeat_probability": repeat_probability,
        "corrected_rank": corrected_rank,
        "back_summary": back_summary,
    }


def derive_seed_combinations(df_view, choice, seed_text):
    """Derive deterministic seed combinations from the selected real data window."""
    pool_r, count_r, _, _ = get_lottery_rules(choice)
    if df_view is None or df_view.empty:
        return None

    safe_df = df_view.apply(pd.to_numeric, errors="coerce").fillna(-1).astype(int)
    front_cols, _ = _draw_columns(safe_df, count_r, 0)
    window_size = len(safe_df)

    seed_nums = [int(n) for n in re.findall(r"\d+", seed_text or "")]
    valid_seeds = list(dict.fromkeys([n for n in seed_nums if n in pool_r]))

    flat_values = safe_df[front_cols].values.flatten().tolist()
    flat_values = [n for n in flat_values if n in pool_r]
    freq_counter = Counter(flat_values)

    history_rows = safe_df[front_cols].values.tolist()
    history_rows.reverse()
    latest_state = [n for n in history_rows[-1] if n in pool_r] if history_rows else []
    transition_counter = Counter()
    for i in range(len(history_rows) - 1):
        current_state = history_rows[i]
        future_state = history_rows[i + 1]
        for cb in current_state:
            if cb in pool_r:
                for fb in future_state:
                    if fb in pool_r:
                        transition_counter[fb] += 1 if cb in latest_state else 0

    max_freq = max(freq_counter.values()) if freq_counter else 1
    max_transition = max(transition_counter.values()) if transition_counter and max(transition_counter.values()) > 0 else 1

    score_rows = []
    for num in pool_r:
        freq = freq_counter.get(num, 0)
        omission = 0
        for _, row in safe_df.iterrows():
            if num in [int(row[col]) for col in front_cols]:
                break
            omission += 1

        freq_score = freq / max_freq
        omission_score = omission / max(window_size, 1)
        transition_score = transition_counter.get(num, 0) / max_transition
        seed_bonus = 1.2 if num in valid_seeds else 0
        score = freq_score * 2.4 + omission_score * 0.8 + transition_score * 1.4 + seed_bonus

        score_rows.append(
            {
                "号码": num,
                "频次": freq,
                "遗漏": omission,
                "转移": transition_counter.get(num, 0),
                "种子": "是" if num in valid_seeds else "否",
                "得分": score,
            }
        )

    ranked = sorted(score_rows, key=lambda x: (x["得分"], x["转移"], x["频次"], x["遗漏"]), reverse=True)

    def pick(count):
        selected = []
        for n in valid_seeds:
            if n not in selected and n in pool_r:
                selected.append(n)
            if len(selected) >= count:
                return sorted(selected)
        for row in ranked:
            if row["号码"] not in selected:
                selected.append(row["号码"])
            if len(selected) >= count:
                return sorted(selected)
        return sorted(selected)

    core_count = 1
    compact_count = min(3, count_r)
    standard_count = count_r
    expanded_count = min(len(pool_r), count_r + 2)

    core = pick(core_count)
    compact = pick(compact_count)
    standard = pick(standard_count)
    expanded = pick(expanded_count)

    return {
        "valid_seeds": valid_seeds,
        "core": core,
        "compact": compact,
        "standard": standard,
        "expanded": expanded,
        "score_rows": ranked,
        "window_size": window_size,
    }


def expert_compress_combinations(choice, red_dan, red_tuo, blue_dan=None, blue_tuo=None, target_012="自适应", use_012=True, kill_triple=True, unique_tail=False, max_checks=150000, max_results=50):
    configs = {
        "双色球": {"r_max": 33, "r_need": 6, "b_max": 16, "b_need": 1},
        "大乐透": {"r_max": 35, "r_need": 5, "b_max": 12, "b_need": 2},
        "福彩3D": {"r_max": 9, "r_need": 3, "b_max": 0, "b_need": 0},
        "排列3": {"r_max": 9, "r_need": 3, "b_max": 0, "b_need": 0},
    }
    if choice not in configs:
        return {"ok": False, "message": "当前彩种暂未接入组合压缩。"}

    cfg = configs[choice]
    blue_dan = blue_dan or []
    blue_tuo = blue_tuo or []
    red_dan = sorted(list(dict.fromkeys([int(x) for x in red_dan])))
    red_tuo = sorted(list(dict.fromkeys([int(x) for x in red_tuo if int(x) not in red_dan])))
    blue_dan = sorted(list(dict.fromkeys([int(x) for x in blue_dan])))
    blue_tuo = sorted(list(dict.fromkeys([int(x) for x in blue_tuo if int(x) not in blue_dan])))

    def check_012_logic(comb, target):
        if target == "自适应" or ":" not in str(target):
            return True
        try:
            target_counts = [int(i) for i in str(target).split(":")]
        except Exception:
            return True
        actual_counts = [0, 0, 0]
        for x in comb:
            actual_counts[x % 3] += 1
        return actual_counts == target_counts

    def has_triple_consecutive(nums):
        nums = sorted(nums)
        return any(nums[i] == nums[i - 1] + 1 and nums[i + 1] == nums[i] + 1 for i in range(1, len(nums) - 1))

    r_ok = len(red_dan) + len(red_tuo) >= cfg["r_need"]
    b_ok = (len(blue_dan) + len(blue_tuo) >= cfg["b_need"]) if cfg["b_max"] > 0 else True
    if not r_ok or not b_ok:
        return {
            "ok": False,
            "message": f"选号素材不足：前区至少 {cfg['r_need']} 个，后区至少 {cfg['b_need']} 个。",
        }

    red_needed_from_tuo = cfg["r_need"] - len(red_dan)
    valid_reds = []
    checked_count = 0

    if red_needed_from_tuo < 0:
        valid_reds = [sorted(red_dan[: cfg["r_need"]])]
    elif red_needed_from_tuo == 0:
        current_red = sorted(red_dan)
        if (not use_012 or check_012_logic(current_red, target_012)) and (not kill_triple or not has_triple_consecutive(current_red)) and (not unique_tail or len(set(x % 10 for x in current_red)) == len(current_red)):
            valid_reds = [current_red]
    else:
        for rt in itertools.combinations(red_tuo, red_needed_from_tuo):
            checked_count += 1
            if checked_count > max_checks:
                return {"ok": False, "message": "计算量过大，请增加胆码或减少拖码。"}

            current_red = sorted(list(red_dan) + list(rt))
            if use_012 and not check_012_logic(current_red, target_012):
                continue
            if kill_triple and has_triple_consecutive(current_red):
                continue
            if unique_tail and len(set(x % 10 for x in current_red)) != len(current_red):
                continue
            valid_reds.append(current_red)

    if cfg["b_max"] > 0:
        blue_needed_from_tuo = cfg["b_need"] - len(blue_dan)
        if blue_needed_from_tuo <= 0:
            valid_blues = [sorted(blue_dan[: cfg["b_need"]])]
        elif len(blue_tuo) < blue_needed_from_tuo:
            return {"ok": False, "message": "后区拖码不足。"}
        else:
            valid_blues = [sorted(list(blue_dan) + list(bt)) for bt in itertools.combinations(blue_tuo, blue_needed_from_tuo)]
    else:
        valid_blues = [[]]

    total_count = len(valid_reds) * len(valid_blues)
    samples = []
    for red in valid_reds:
        for blue in valid_blues:
            samples.append({"red": red, "blue": blue})
            if len(samples) >= max_results:
                break
        if len(samples) >= max_results:
            break

    return {
        "ok": True,
        "config": cfg,
        "checked_count": checked_count,
        "red_count": len(valid_reds),
        "blue_count": len(valid_blues),
        "total_count": total_count,
        "budget": total_count * 2,
        "samples": samples,
    }


def get_012_route_stats(df_view, choice):
    pool_r, count_r, _, _ = get_lottery_rules(choice)
    if df_view is None or df_view.empty:
        return None

    safe_df = df_view.apply(pd.to_numeric, errors="coerce").fillna(-1).astype(int)
    front_cols, _ = _draw_columns(safe_df, count_r, 0)

    actual_counter = Counter()
    for _, row in safe_df.iterrows():
        counts = [0, 0, 0]
        nums = [int(row[col]) for col in front_cols]
        for num in nums:
            counts[num % 3] += 1
        actual_counter[tuple(counts)] += 1

    route_bucket_sizes = [sum(1 for n in pool_r if n % 3 == mod) for mod in [0, 1, 2]]
    total_combinations = calculate_bets(len(pool_r), count_r)
    theoretical_rows = []
    for a in range(count_r + 1):
        for b in range(count_r - a + 1):
            c = count_r - a - b
            ways = (
                calculate_bets(route_bucket_sizes[0], a)
                * calculate_bets(route_bucket_sizes[1], b)
                * calculate_bets(route_bucket_sizes[2], c)
            )
            if ways <= 0:
                continue
            key = (a, b, c)
            actual_count = actual_counter.get(key, 0)
            actual_ratio = actual_count / len(safe_df) if len(safe_df) else 0
            theoretical_ratio = ways / total_combinations if total_combinations else 0
            theoretical_rows.append(
                {
                    "route": f"{a}:{b}:{c}",
                    "counts": key,
                    "theoretical_count": ways,
                    "theoretical_ratio": theoretical_ratio,
                    "actual_count": actual_count,
                    "actual_ratio": actual_ratio,
                }
            )

    theoretical_rows.sort(key=lambda x: (x["theoretical_ratio"], x["actual_ratio"]), reverse=True)
    return {
        "window_size": len(safe_df),
        "route_bucket_sizes": route_bucket_sizes,
        "rows": theoretical_rows,
    }


def build_cycle_filter_report(df_full, choice, mode, view_limit, target_period=None, weekday=None):
    """Build same-period / weekday / recent reports from real historical rows."""
    if df_full is None or df_full.empty:
        return None

    pool_r, count_r, pool_b, count_b = get_lottery_rules(choice)
    safe_df = df_full.copy()
    if "期号" not in safe_df.columns:
        return None

    if mode == "历史同期":
        latest_issue = str(int(safe_df.iloc[0]["期号"]))
        if target_period is None:
            current_suffix = latest_issue[-3:] if len(latest_issue) >= 3 else latest_issue
            try:
                target_period = f"{int(current_suffix) + 1:03d}"
            except Exception:
                target_period = current_suffix
        target_period = str(target_period).zfill(3)
        filtered = safe_df[safe_df["期号"].astype(str).str.endswith(target_period)].copy()
        label = f"历史同期尾号 {target_period}"
    elif mode == "星期走势":
        weekday_source = "真实日期"
        if "星期" not in safe_df.columns or safe_df["星期"].isna().all():
            draw_weekdays = DRAW_WEEKDAYS.get(choice, list(range(7)))
            sorted_issues = safe_df["期号"].astype(int).sort_values().drop_duplicates().tolist()
            issue_week_map = {issue: draw_weekdays[idx % len(draw_weekdays)] for idx, issue in enumerate(sorted_issues)}
            safe_df["星期"] = safe_df["期号"].astype(int).map(issue_week_map)
            weekday_source = "期号序列推算"
        week_map = {"周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4, "周六": 5, "周日": 6}
        target_week = week_map.get(weekday, weekday if weekday is not None else 0)
        safe_df["星期"] = pd.to_numeric(safe_df["星期"], errors="coerce")
        filtered = safe_df[safe_df["星期"] == target_week].copy()
        label = f"{weekday} 独立走势"
    else:
        filtered = safe_df.head(view_limit).copy()
        label = f"近期连贯 {view_limit} 期"

    if filtered.empty:
        return {"ok": False, "message": f"{label} 没有可用数据。"}

    filtered = filtered.head(view_limit)
    numeric_cols = [c for c in filtered.columns if str(c).startswith("b_")]
    if not numeric_cols:
        numeric_cols = [
            c
            for c in filtered.columns
            if c not in ["期号", "日期", "日期_解析", "星期"]
            and pd.api.types.is_numeric_dtype(filtered[c])
        ]
    front_cols = numeric_cols[:count_r]
    back_cols = numeric_cols[count_r : count_r + count_b]

    if len(front_cols) < count_r:
        return {"ok": False, "message": "当前数据列不足，无法计算周期过滤。"}

    front_values = filtered[front_cols].apply(pd.to_numeric, errors="coerce").fillna(-1).astype(int).values.flatten().tolist()
    front_values = [n for n in front_values if n in pool_r]
    front_counter = Counter(front_values)
    front_rank = [{"号码": n, "频次": front_counter.get(n, 0)} for n in pool_r]
    front_rank.sort(key=lambda x: (x["频次"], -x["号码"]), reverse=True)

    back_rank = []
    if count_b > 0 and len(back_cols) >= count_b:
        back_values = filtered[back_cols].apply(pd.to_numeric, errors="coerce").fillna(-1).astype(int).values.flatten().tolist()
        back_values = [n for n in back_values if n in pool_b]
        back_counter = Counter(back_values)
        back_rank = [{"号码": n, "频次": back_counter.get(n, 0)} for n in pool_b]
        back_rank.sort(key=lambda x: (x["频次"], -x["号码"]), reverse=True)

    sums = filtered[front_cols].sum(axis=1)
    spans = filtered[front_cols].max(axis=1) - filtered[front_cols].min(axis=1)
    consecutive_count = 0
    repeat_count = 0
    for idx, (_, row) in enumerate(filtered.iterrows()):
        nums = sorted([int(row[col]) for col in front_cols])
        if any(nums[i + 1] - nums[i] == 1 for i in range(len(nums) - 1)):
            consecutive_count += 1
        if idx + 1 < len(filtered):
            prev_nums = set(int(filtered.iloc[idx + 1][col]) for col in front_cols)
            if set(nums).intersection(prev_nums):
                repeat_count += 1

    return {
        "ok": True,
        "label": label,
        "rows": filtered,
        "sample_size": len(filtered),
        "front_rank": front_rank,
        "back_rank": back_rank,
        "weekday_source": locals().get("weekday_source", ""),
        "sum_mean": float(sums.mean()) if len(sums) else 0,
        "span_mean": float(spans.mean()) if len(spans) else 0,
        "repeat_rate": repeat_count / len(filtered) if len(filtered) else 0,
        "consecutive_rate": consecutive_count / len(filtered) if len(filtered) else 0,
    }


def scan_advanced_patterns(df_slice, df_full, is_dlt):
    front_cols = ["前1", "前2", "前3", "前4", "前5"] if is_dlt else ["前1", "前2", "前3", "前4", "前5", "前6"]
    repeat_count = 0
    consecutive_count = 0
    for _, row in df_slice.iterrows():
        nums = sorted([row[c] for c in front_cols])
        if any(nums[i + 1] - nums[i] == 1 for i in range(len(nums) - 1)):
            consecutive_count += 1
        full_idx = df_full.index[df_full["期号"] == row["期号"]].tolist()
        if full_idx and full_idx[0] + 1 < len(df_full):
            prev_nums = set([df_full.iloc[full_idx[0] + 1][c] for c in front_cols])
            if len(set(nums).intersection(prev_nums)) > 0:
                repeat_count += 1
    return repeat_count, consecutive_count


def run_tactical_manual_analysis(raw_text, is_dlt, history_limit, recent_red_pool=None, recent_blue_pool=None, history_tongqi_pool=None, weekday_pool=None, weekday_blue_pool=None, recent_red_counts=None, recent_blue_counts=None):
    red_nums, blue_nums = parse_red_blue_from_text(raw_text, is_dlt=is_dlt)
    if not red_nums:
        return {"ok": False, "message": "未检测到有效号码，请检查输入格式。"}

    counts_red = Counter(red_nums)
    counts_blue = Counter(blue_nums)
    sorted_red = counts_red.most_common()
    hot_nums = [x[0] for x in sorted_red[:6]]

    max_n = 35 if is_dlt else 33
    all_possible = set(range(1, max_n + 1))
    appeared_nums = set(red_nums)
    cold_nums = list(all_possible - appeared_nums)
    low_freq_nums = [x[0] for x in sorted_red if x[1] == 1]
    potential_nums = sorted(list(set(cold_nums + low_freq_nums)))

    offset_recommend = set()
    for h in hot_nums:
        for offset in [-2, -1, 1, 2]:
            target = h + offset
            if 1 <= target <= max_n and target not in hot_nums:
                offset_recommend.add(target)
    offset_recommend = sorted(list(offset_recommend))

    max_b = 12 if is_dlt else 16
    req_r = 5 if is_dlt else 6
    req_b = 2 if is_dlt else 1
    recent_red_pool = recent_red_pool or list(range(1, max_n + 1))
    history_tongqi_pool = history_tongqi_pool or list(range(1, max_n + 1))
    weekday_pool = weekday_pool or list(range(1, max_n + 1))
    recent_blue_pool = recent_blue_pool or list(range(1, max_b + 1))
    weekday_blue_pool = weekday_blue_pool or list(range(1, max_b + 1))
    recent_red_counts = recent_red_counts or {}
    recent_blue_counts = recent_blue_counts or {}
    max_recent_red = max(recent_red_counts.values()) if recent_red_counts else 1
    max_recent_blue = max(recent_blue_counts.values()) if recent_blue_counts else 1

    red_scores = {}
    for num in range(1, max_n + 1):
        score = 0
        if num in recent_red_pool:
            score += 3
        score += 4 * (recent_red_counts.get(num, 0) / max_recent_red)
        if num in history_tongqi_pool:
            score += 2
        if num in weekday_pool:
            score += 2
        if num in hot_nums:
            score = 0
        red_scores[num] = score

    blue_scores = {}
    for num in range(1, max_b + 1):
        score = 0
        if num in recent_blue_pool:
            score += 3
        score += 4 * (recent_blue_counts.get(num, 0) / max_recent_blue)
        if num in weekday_blue_pool:
            score += 2
        score = score - (counts_blue.get(num, 0) * 2)
        blue_scores[num] = score

    sorted_math_reds = [num for num, score in sorted(red_scores.items(), key=lambda x: (x[1], -x[0]), reverse=True) if score > 0]
    sorted_math_blues = [num for num, score in sorted(blue_scores.items(), key=lambda x: (x[1], -x[0]), reverse=True)]
    if len(sorted_math_reds) < req_r + 2:
        sorted_math_reds = [x for x in range(1, max_n + 1) if x not in hot_nums]
    if len(sorted_math_blues) < req_b + 2:
        sorted_math_blues = [x for x in range(1, max_b + 1)]

    final_math_reds = sorted(sorted_math_reds[:req_r])
    final_math_blues = sorted(sorted_math_blues[:req_b])
    fushi_math_reds = sorted(sorted_math_reds[: req_r + 2])
    fushi_blue_count = req_b + 2 if is_dlt else req_b + 1
    fushi_math_blues = sorted(sorted_math_blues[:fushi_blue_count])
    zhusu = math.comb(len(fushi_math_reds), req_r) * math.comb(len(fushi_math_blues), req_b)

    dan_source = potential_nums if potential_nums else offset_recommend
    if is_dlt:
        dan_primary = (dan_source + [1, 2, 3, 4])[:4]
        dan_secondary = (dan_source + [1, 2, 3])[:3]
    else:
        dan_primary = (dan_source + [1, 2, 3, 4, 5])[:5]
        dan_secondary = []

    return {
        "ok": True,
        "red_nums": red_nums,
        "blue_nums": blue_nums,
        "counts_red": counts_red,
        "counts_blue": counts_blue,
        "hot_nums": hot_nums,
        "potential_nums": potential_nums,
        "offset_recommend": offset_recommend,
        "final_math_reds": final_math_reds,
        "final_math_blues": final_math_blues,
        "fushi_math_reds": fushi_math_reds,
        "fushi_math_blues": fushi_math_blues,
        "zhusu": zhusu,
        "dan_primary": dan_primary,
        "dan_secondary": dan_secondary,
        "history_limit": history_limit,
        "is_dlt": is_dlt,
    }
