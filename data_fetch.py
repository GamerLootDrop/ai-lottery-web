import os
import re
import time
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

from lottery_rules import LOTTERY_FILES, WEB_GAME_CODES

FETCH_LOG_FILE = "fetch_log.csv"
FETCH_COOLDOWN_SECONDS = 1800


def find_lottery_file(choice, base_dir="."):
    file_kw = LOTTERY_FILES[choice]
    all_files = [
        f
        for f in os.listdir(base_dir)
        if file_kw in f.lower() and (f.endswith(".xls") or f.endswith(".xlsx") or f.endswith(".csv"))
    ]
    return next((f for f in all_files if "_synced" in f), all_files[0] if all_files else None)


def _read_fetch_log():
    if not os.path.exists(FETCH_LOG_FILE):
        return {}
    try:
        df = pd.read_csv(FETCH_LOG_FILE)
        return {str(row["choice"]): row.to_dict() for _, row in df.iterrows()}
    except Exception:
        return {}


def _write_fetch_log(log):
    rows = list(log.values())
    if rows:
        pd.DataFrame(rows).to_csv(FETCH_LOG_FILE, index=False, encoding="utf-8-sig")


def should_skip_fetch(choice, local_latest_issue):
    log = _read_fetch_log()
    row = log.get(choice)
    if not row:
        return False, ""
    try:
        last_ts = float(row.get("last_ts", 0))
        last_issue = str(row.get("latest_issue", ""))
        age = time.time() - last_ts
        if last_issue == str(local_latest_issue) and age < FETCH_COOLDOWN_SECONDS:
            remain_min = int((FETCH_COOLDOWN_SECONDS - age) / 60) + 1
            return True, f"已有用户刚检查过最新数据，当前期号 {local_latest_issue}，{remain_min} 分钟内不重复抓取。"
    except Exception:
        pass
    return False, ""


def record_fetch(choice, latest_issue):
    log = _read_fetch_log()
    log[choice] = {
        "choice": choice,
        "latest_issue": str(latest_issue),
        "last_ts": time.time(),
        "last_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _write_fetch_log(log)


@st.cache_data
def load_full_data(file_path, choice):
    try:
        raw_df = pd.read_excel(file_path) if file_path.endswith((".xls", ".xlsx")) else pd.read_csv(file_path)
        raw_df.columns = [str(c).strip() for c in raw_df.columns]
        q_col = next((c for c in raw_df.columns if "期" in c or "NO" in c.upper()), raw_df.columns[0])
        raw_df[q_col] = pd.to_numeric(raw_df[q_col], errors="coerce")
        raw_df = raw_df.dropna(subset=[q_col])
        date_col = next((c for c in raw_df.columns if "日期" in c or "date" in c.lower()), None)

        limits = {
            "双色球": 7,
            "大乐透": 7,
            "福彩3D": 3,
            "排列3": 3,
            "排列5": 5,
            "七星彩": 7,
            "快乐8": 20,
        }
        max_balls = limits.get(choice, 7)

        q_idx = list(raw_df.columns).index(q_col)
        ball_cols = []
        for i in range(q_idx + 1, len(raw_df.columns)):
            col = raw_df.columns[i]
            nums = pd.to_numeric(raw_df[col], errors="coerce").dropna()
            if not nums.empty and (nums <= 81).all():
                ball_cols.append(col)
            if len(ball_cols) == max_balls:
                break

        draw_names = [f"b_{i + 1}" for i in range(len(ball_cols))]
        draw_df = raw_df[[q_col] + ball_cols].copy()
        draw_df.columns = ["期号"] + draw_names
        for c in ["期号"] + draw_names:
            draw_df[c] = pd.to_numeric(draw_df[c], errors="coerce").fillna(0).astype(int)

        if date_col:
            draw_df["日期"] = raw_df[date_col].astype(str)
            draw_df["日期_解析"] = pd.to_datetime(draw_df["日期"], errors="coerce")
            draw_df["星期"] = draw_df["日期_解析"].dt.dayofweek

        needs_zero = choice in ["双色球", "大乐透", "快乐8"]
        ordered_cols = ["期号"] + draw_names + [c for c in ["日期", "日期_解析", "星期"] if c in draw_df.columns]
        clean_df = draw_df[ordered_cols].sort_values("期号", ascending=False)
        return clean_df, "期号", draw_names, needs_zero, file_path
    except Exception:
        return None, None, None, None, None


@st.cache_data(ttl=3600)
def fetch_from_web(game_code, choice, d_cols_len, limit=50):
    urls = [
        f"https://datachart.500.com/{game_code}/history/newinc/history.php?limit={limit}",
        f"https://datachart.500.com/{game_code}/history/inc/history.php?limit={limit}",
        f"https://datachart.500.com/{game_code}/history/history.shtml?limit={limit}",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Referer": f"https://datachart.500.com/{game_code}/history/history.shtml",
    }
    web_rows = []
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text, "html.parser")
            trs = soup.find_all("tr", class_=["t_tr1", "t_tr2", "t_tr"]) or soup.find_all("tr")
            for tr in trs:
                tds = tr.find_all("td")
                if len(tds) < d_cols_len + 1:
                    continue
                iss_str = re.sub(r"\D", "", tds[0].get_text(strip=True))
                if len(iss_str) < 3:
                    continue
                issue_val = int("20" + iss_str[:10]) if len(iss_str) == 5 else int(iss_str[:10])

                date_str = ""
                for td in reversed(tds):
                    txt = td.get_text(strip=True)
                    if re.search(r"\d{4}-\d{2}-\d{2}", txt):
                        date_str = re.search(r"\d{4}-\d{2}-\d{2}", txt).group(0)
                        break

                balls = []
                for span in tr.find_all(["span", "em", "i"], class_=re.compile(r"(ball|red|blue|chartBall|cfont|num)", re.I)):
                    txt = span.get_text(strip=True)
                    if txt.isdigit():
                        balls.append(int(txt))

                if len(balls) < d_cols_len:
                    td_numbers = []
                    for td in tds[1:]:
                        txt = td.get_text(" ", strip=True)
                        if re.search(r"\d{4}-\d{2}-\d{2}", txt):
                            continue
                        if txt.isdigit():
                            td_numbers.append(int(txt))
                        else:
                            single_nums = re.findall(r"(?<!\d)(\d{1,2})(?!\d)", txt)
                            if 1 <= len(single_nums) <= d_cols_len:
                                td_numbers.extend([int(n) for n in single_nums])
                    balls = td_numbers

                balls = [n for n in balls if 0 <= n <= 81][:d_cols_len]

                if len(balls) == d_cols_len:
                    web_rows.append({"issue": issue_val, "date": date_str, "balls": balls})
            if web_rows:
                break
        except Exception:
            continue
    return web_rows


def fetch_from_cwl(choice, d_cols_len, limit=50):
    cwl_names = {
        "双色球": "ssq",
        "福彩3D": "3d",
        "快乐8": "kl8",
    }
    name = cwl_names.get(choice)
    if not name:
        return []
    url = f"https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name={name}&issueCount={limit}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.cwl.gov.cn/",
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        rows = data.get("result") or data.get("data") or []
        web_rows = []
        for item in rows:
            issue_text = str(item.get("code") or item.get("issue") or "")
            iss_str = re.sub(r"\D", "", issue_text)
            if not iss_str:
                continue
            issue_val = int(iss_str)
            date_str = str(item.get("date") or item.get("openTime") or item.get("time") or "")
            red_text = str(item.get("red") or item.get("redCode") or item.get("frontWinningNum") or "")
            blue_text = str(item.get("blue") or item.get("blueCode") or item.get("backWinningNum") or "")
            balls = [int(n) for n in re.findall(r"\d+", red_text + " " + blue_text)]
            balls = [n for n in balls if 0 <= n <= 81][:d_cols_len]
            if len(balls) == d_cols_len:
                web_rows.append({"issue": issue_val, "date": date_str[:10], "balls": balls})
        return web_rows
    except Exception:
        return []


def build_synced_dataframe(df, q_col, d_cols, choice):
    local_latest_issue = str(df.iloc[0][q_col])
    has_usable_date = "日期" in df.columns and df["日期"].notna().any() and df["日期"].astype(str).str.contains(r"\d{4}-\d{2}-\d{2}", regex=True).any()
    if has_usable_date:
        skip, skip_message = should_skip_fetch(choice, local_latest_issue)
        if skip:
            return df, skip_message

    web_data = fetch_from_web(WEB_GAME_CODES.get(choice, "ssq"), choice, len(d_cols))
    if not web_data:
        web_data = fetch_from_cwl(choice, len(d_cols))
    if not web_data:
        return None, "抓取失败，请检查网络或稍后再试。"

    latest_web_issue = str(web_data[0]["issue"])
    if latest_web_issue == local_latest_issue and has_usable_date:
        record_fetch(choice, local_latest_issue)
        return df, f"当前已是全网最新数据，期号 {local_latest_issue}。"

    clean_web_rows = []
    for item in web_data:
        row_dict = {"期号": item["issue"]}
        if item.get("date"):
            row_dict["日期"] = item["date"]
        for i, col in enumerate(d_cols):
            if i < len(item["balls"]):
                row_dict[col] = item["balls"][i]
        clean_web_rows.append(row_dict)

    web_df = pd.DataFrame(clean_web_rows)
    for col in ["期号"] + d_cols:
        if col in web_df.columns:
            web_df[col] = pd.to_numeric(web_df[col], errors="coerce").fillna(0).astype("int64")
    updated = (
        pd.concat([web_df, df], ignore_index=True)
        .drop_duplicates(subset=[q_col], keep="first")
        .sort_values(q_col, ascending=False)
        .head(2000)
    )
    if "日期" in updated.columns:
        updated["日期_解析"] = pd.to_datetime(updated["日期"], errors="coerce")
        updated["星期"] = updated["日期_解析"].dt.dayofweek
    record_fetch(choice, latest_web_issue)
    return updated, f"同步成功，已抓取 {len(clean_web_rows)} 条网页数据。"


def save_synced_dataframe(updated, file_path):
    save_path = file_path if file_path.endswith(".csv") else file_path.replace(".xls", "_synced.csv")
    save_path = save_path.replace(".xlsx", "_synced.csv")
    export_df = updated.copy()
    keep_cols = ["期号"] + [c for c in export_df.columns if c.startswith("b_")] + [c for c in ["日期"] if c in export_df.columns]
    export_df = export_df[keep_cols]
    export_df.to_csv(save_path, index=False, encoding="utf-8-sig")
    st.cache_data.clear()
    return save_path


def fetch_latest_window(lottery_code, local_latest_issue=0, custom_limit=100):
    now_time = time.time()
    urls = [
        f"https://datachart.500.com/{lottery_code}/history/newinc/history.php?limit={custom_limit}&_t={int(now_time)}",
        f"https://datachart.500.com/{lottery_code}/history/inc/history.php?limit={custom_limit}&_t={int(now_time)}",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Referer": f"https://datachart.500.com/{lottery_code}/history/history.shtml",
    }

    new_rows = []
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code != 200:
                continue
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text, "html.parser")
            trs = soup.find_all("tr", class_=["t_tr1", "t_tr2", "t_tr"]) or soup.find_all("tr")

            for tr in trs:
                tds = tr.find_all("td")
                if len(tds) < 8:
                    continue

                iss_str = re.sub(r"\D", "", tds[0].get_text(strip=True))
                if len(iss_str) < 3:
                    continue
                issue_val = int("20" + iss_str[:10]) if len(iss_str) == 5 else int(iss_str[:10])
                if custom_limit == 50 and issue_val <= local_latest_issue:
                    continue

                balls = []
                for td in tds[1:]:
                    text = td.get_text(strip=True)
                    if text.isdigit():
                        balls.append(int(text))

                date_str = tds[-1].get_text(strip=True)
                if not re.search(r"\d{4}-\d{2}-\d{2}", date_str):
                    date_str = time.strftime("%Y-%m-%d", time.localtime())

                if len(balls) >= 7:
                    core_balls = balls[:7]
                    new_rows.append(
                        [
                            issue_val,
                            date_str,
                            core_balls[0],
                            core_balls[1],
                            core_balls[2],
                            core_balls[3],
                            core_balls[4],
                            core_balls[5],
                            core_balls[6],
                        ]
                    )
            if new_rows:
                break
        except Exception:
            continue

    if new_rows:
        cols = (
            ["期号", "日期", "前1", "前2", "前3", "前4", "前5", "后1", "后2"]
            if lottery_code == "dlt"
            else ["期号", "日期", "前1", "前2", "前3", "前4", "前5", "前6", "后1"]
        )
        return pd.DataFrame(new_rows, columns=cols).sort_values(by="期号", ascending=False).reset_index(drop=True)
    return pd.DataFrame()


@st.cache_data(ttl=5)
def load_cloud_or_local_data(lottery_code, uploaded_file=None, target_mode="默认"):
    df_local = pd.DataFrame()
    source = uploaded_file if uploaded_file else (
        f"{lottery_code}.csv"
        if os.path.exists(f"{lottery_code}.csv")
        else (f"{lottery_code}.xls" if os.path.exists(f"{lottery_code}.xls") else None)
    )

    if source:
        try:
            if hasattr(source, "seek"):
                source.seek(0)
            if str(source).endswith(("xls", "xlsx")):
                df_raw = pd.read_excel(source, header=None, dtype=str)
            else:
                df_raw = pd.read_csv(source, encoding_errors="ignore", header=None, dtype=str)

            cols_use = [0, 1, 2, 3, 4, 5, 6, 7, 8]
            c_names = (
                ["期号", "日期", "前1", "前2", "前3", "前4", "前5", "后1", "后2"]
                if lottery_code == "dlt"
                else ["期号", "日期", "前1", "前2", "前3", "前4", "前5", "前6", "后1"]
            )

            df_raw = df_raw.iloc[:, cols_use]
            df_raw.columns = c_names
            df_raw["前1"] = pd.to_numeric(df_raw["前1"], errors="coerce")
            df_raw = df_raw.dropna(subset=["前1"])
            df_raw["期号"] = df_raw["期号"].astype(str).str.replace(r"\D", "", regex=True)
            df_raw["期号"] = pd.to_numeric(df_raw["期号"], errors="coerce").fillna(0).astype(int)

            for c in c_names[2:]:
                df_raw[c] = pd.to_numeric(df_raw[c], errors="coerce").fillna(0).astype(int)
            df_local = df_raw[(df_raw["前1"] > 0) & (df_raw["前1"] <= 35)].sort_values(by="期号", ascending=False).reset_index(drop=True)
        except Exception:
            pass

    local_latest = int(df_local.iloc[0]["期号"]) if not df_local.empty else 0
    limit = 3000 if target_mode == "历史同期对比" and df_local.empty else 100
    df_new = fetch_latest_window(lottery_code, local_latest, custom_limit=limit)
    new_count = len(df_new)

    df_final = pd.concat([df_new, df_local], ignore_index=True) if not df_new.empty else df_local
    if not df_final.empty:
        df_final = df_final.drop_duplicates(subset=["期号"], keep="first")
        df_final = df_final.sort_values(by="期号", ascending=False).reset_index(drop=True)
        df_final["日期_解析"] = pd.to_datetime(df_final["日期"], errors="coerce")
        df_final["星期"] = df_final["日期_解析"].dt.dayofweek

    return df_final, new_count
