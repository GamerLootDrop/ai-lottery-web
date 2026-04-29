import requests
import pandas as pd
import time

class LotteryCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'
        }

    def fetch_from_500(self, url, name):
        try:
            print(f"📡 正在尝试通过移动端接口抓取 {name}...")
            # 增加 verify=False 防止海外服务器 SSL 证书握手失败
            res = requests.get(url, headers=self.headers, timeout=30, verify=True)
            res.encoding = 'gb2312'
            
            # 使用最简单的 html 解析
            tables = pd.read_html(res.text)
            for df in tables:
                if df.shape[1] >= 7:
                    data_list = []
                    for _, row in df.iterrows():
                        # 转换每一行为字符串并清洗
                        vals = [str(x).strip() for x in row.values]
                        issue = vals[1]
                        if issue.isdigit() and len(issue) >= 5:
                            if "dlt" in url:
                                red = " ".join(vals[2:7])
                                blue = " ".join(vals[7:9])
                            else:
                                red = " ".join(vals[2:8])
                                blue = vals[8]
                            data_list.append({"期号": issue, "红球": red, "蓝球": blue})
                    
                    if data_list:
                        print(f"✅ {name} 成功拿到 {len(data_list)} 期数据！")
                        return data_list
            return []
        except Exception as e:
            print(f"❌ {name} 抓取异常: {e}")
            return []

    def run(self):
        # 接口 1: 大乐透 (500网)
        dlt_data = self.fetch_from_500("http://datachart.500.com/dlt/history/new_history.shtml", "大乐透")
        if dlt_data:
            pd.DataFrame(dlt_data).to_csv('dlt_data.csv', index=False, encoding='utf-8')
        else:
            print("⚠️ 大乐透没拿到数据，保持原文件不动，不进行覆盖。")

        # 接口 2: 双色球 (500网)
        ssq_data = self.fetch_from_500("http://datachart.500.com/ssq/history/history.shtml", "双色球")
        if ssq_data:
            pd.DataFrame(ssq_data).to_csv('ssq_data.csv', index=False, encoding='utf-8')
        else:
            print("⚠️ 双色球没拿到数据，保持原文件不动。")

if __name__ == "__main__":
    LotteryCrawler().run()
