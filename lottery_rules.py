LOTTERY_FILES = {
    "福彩3D": "3d",
    "双色球": "ssq",
    "大乐透": "dlt",
    "快乐8": "kl8",
    "排列3": "p3",
    "排列5": "p5",
    "七星彩": "7xc",
}

WEB_GAME_CODES = {
    "双色球": "ssq",
    "大乐透": "dlt",
    "福彩3D": "sd",
    "排列3": "pls",
    "排列5": "plw",
    "七星彩": "qxc",
    "快乐8": "kl8",
}


def get_lottery_rules(choice):
    rules = {
        "双色球": (list(range(1, 34)), 6, list(range(1, 17)), 1),
        "大乐透": (list(range(1, 36)), 5, list(range(1, 13)), 2),
        "七星彩": (list(range(0, 10)), 6, list(range(0, 15)), 1),
        "快乐8": (list(range(1, 81)), 20, [], 0),
        "福彩3D": (list(range(0, 10)), 3, [], 0),
        "排列3": (list(range(0, 10)), 3, [], 0),
        "排列5": (list(range(0, 10)), 5, [], 0),
    }
    return rules.get(choice, rules["双色球"])


def should_zero_pad(choice):
    return choice in ["双色球", "大乐透", "快乐8"]


def format_number(num, choice):
    return f"{int(num):02d}" if should_zero_pad(choice) else str(int(num))


def split_draw_numbers(row, d_cols, choice):
    _, count_r, _, count_b = get_lottery_rules(choice)
    values = [int(row[col]) for col in d_cols if col in row]
    return values[:count_r], values[count_r : count_r + count_b]


def commercial_choice_enabled(choice):
    return choice in LOTTERY_FILES


def is_dual_area(choice):
    return choice in ["双色球", "大乐透"]
