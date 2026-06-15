from datetime import datetime

import streamlit as st


def _secret_value(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


MY_WECHAT_ID = _secret_value("MY_WECHAT_ID", "252766667")


def verify_card_from_sheets(user_input_code):
    user_input_code = str(user_input_code or "").strip()
    backdoors = set(_secret_value("VIP_BACKDOORS", ["ygq6662", "vip6662"]))
    if user_input_code in backdoors:
        return True, 9999

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(st.secrets["google"], scopes=scopes)
        client = gspread.authorize(creds)

        sh = client.open("Lotto_Cards").get_worksheet(0)
        all_rows = sh.get_all_values()
        now = datetime.now()

        for i, row in enumerate(all_rows[1:]):
            db_code = str(row[0]).strip()
            db_days = row[1]
            db_status = str(row[2]).strip() if len(row) > 2 else ""
            db_use_time = str(row[4]).strip() if len(row) > 4 else ""

            if db_code != user_input_code:
                continue

            if not db_use_time:
                current_row_index = i + 2
                start_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
                try:
                    sh.update_cell(current_row_index, 3, "已激活")
                    sh.update_cell(current_row_index, 5, start_time_str)
                except Exception:
                    pass
                return True, int(db_days)

            if db_status == "封禁":
                return False, "该卡密已被封禁"

            try:
                start_dt = datetime.strptime(db_use_time, "%Y-%m-%d %H:%M:%S")
                used_days = (now - start_dt).total_seconds() / 86400
                remaining_days = float(db_days) - used_days
                if remaining_days <= 0:
                    return False, "授权已到期，请联系续费"
                return True, round(remaining_days, 1)
            except Exception:
                return True, int(db_days)

        return False, "授权码不存在"
    except Exception as exc:
        return False, f"连接故障: {exc}"


def init_auth_state():
    if "vip_unlocked" not in st.session_state:
        st.session_state["vip_unlocked"] = False
    if "days_left" not in st.session_state:
        st.session_state["days_left"] = None
    if "last_valid_key" not in st.session_state:
        st.session_state["last_valid_key"] = None


def restore_auth_from_query():
    url_key = st.query_params.get("auth_key")
    if url_key and not st.session_state.get("vip_unlocked"):
        ok, days_or_msg = verify_card_from_sheets(url_key)
        if ok:
            st.session_state["vip_unlocked"] = True
            st.session_state["last_valid_key"] = url_key
            st.session_state["days_left"] = days_or_msg


def unlock_with_code(code):
    ok, days_or_msg = verify_card_from_sheets(code)
    if ok:
        st.session_state["vip_unlocked"] = True
        st.session_state["last_valid_key"] = code
        st.session_state["days_left"] = days_or_msg
        st.query_params["auth_key"] = code
    return ok, days_or_msg


def logout():
    st.session_state["vip_unlocked"] = False
    st.session_state["last_valid_key"] = None
    st.session_state["days_left"] = None
    st.query_params.clear()

