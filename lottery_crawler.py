import requests
import pandas as pd
import os

class LotteryCrawler:
    def __init__(self):
        self.api_url = "https://m.tool.cn/api/lottery/history?type=dlt"
        self.headers = {'User-Agent': 'Mozilla/5.0'}

    def update_database(self, filename, name):
        # 1. 加载现有数据库
        if os.path.exists(filename):
            try:
                df_old = pd.read_csv(filename, dtype={'期号': str})
            except:
                df_old = pd.DataFrame(columns=['期号', '红球', '蓝球'])
        else:
            df_old = pd.DataFrame(columns=['期号', '红球', '蓝球'])

        # 2. 抓取最新数据
        new_results = []
        try:
            res = requests.get(self.api_url, headers=self.headers, timeout=20)
            items = res.json().get('data', [])
            for it in items:
                code = it.get('opencode', '').replace('+', ',').split(',')
                issue = str(it.get('expect'))
                if name == "大乐透":
                    r, b = " ".join([x.zfill(2) for x in code[:5]]), " ".join([x.zfill(2) for x in code[5:]])
                else:
                    r, b = " ".join([x.zfill(2) for x in code[:6]]), code[6].zfill(2)
                new_results.append({"期号": issue, "红球": r, "蓝球": b})
        except Exception as e:
            print(f"📡 抓取失败: {e}")

        # 3. 合并并去重（核心步骤）
        df_new = pd.DataFrame(new_results)
        # 将新老数据合并，并根据“期号”去重，保留最新的
        df_total = pd.concat([df_new, df_old]).drop_duplicates(subset=['期号'], keep='first')
        # 按期号从大到小排序
        df_total = df_total.sort_values(by='期号', ascending=False)

        # 4. 保存回去
        df_total.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ {name} 数据库已更新。当前总记录数：{len(df_total)}")

    def run(self):
        self.update_database('dlt_data.csv', "大乐透")
        # 如果需要双色球，可以添加对应的 API 逻辑
