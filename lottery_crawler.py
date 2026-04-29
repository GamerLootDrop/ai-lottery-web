import requests
import pandas as pd
import time
from datetime import datetime

class LotteryCrawler:
    def __init__(self):
        self.session = requests.Session()
        # 模拟真实的海外浏览器请求
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.google.com/'
        }

    def fetch_data_from_500(self, url, name):
        """尝试从500彩票网抓取，增加了更强的容错"""
        try:
            print(f"正在尝试从 500.com 抓取 {name}...")
            # 增加超时到 60 秒
            response = self.session.get(url, timeout=60, headers=self.headers)
            response.encoding = 'gb2312'
            
            # 使用 pandas 的 read_html 直接暴力解析网页所有表格
            tables = pd.read_html(response.text)
            for df in tables:
                # 寻找列数较多的表格（开奖表通常列数很多）
                if df.shape[1] >= 9:
                    results = []
                    for _, row in df.iterrows():
                        # 期号通常在第1列或第2列
                        issue = str(row.iloc[1]).strip()
                        if issue.isdigit() and len(issue) >= 5:
                            if name == "大乐透":
                                # 5红 + 2蓝
                                red = ' '.join([str(row.iloc[j]).zfill(2) for j in range(2, 7)])
                                blue = ' '.join([str(row.iloc[j]).zfill(2) for j in range(7, 9)])
                            else:
                                # 6红 + 1蓝
                                red = ' '.join([str(row.iloc[j]).zfill(2) for j in range(2, 8)])
                                blue = str(row.iloc[8]).zfill(2)
                            results.append({'期号': issue, '红球': red, '蓝球': blue})
                    
                    if results:
                        print(f"✅ {name} 抓取成功，获取到 {len(results)} 期数据")
                        return results[:100]
        except Exception as e:
            print(f"❌ {name} 抓取出错: {e}")
        return []

    def run(self):
        # 抓取大乐透
        dlt_url = "http://datachart.500.com/dlt/history/new_history.shtml"
        dlt_data = self.fetch_data_from_500(dlt_url, "大乐透")
        
        # 抓取双色球
        ssq_url = "http://datachart.500.com/ssq/history/history.shtml"
        ssq_data = self.fetch_data_from_500(ssq_url, "双色球")

        # 只要抓到数据就写入，没抓到就保持原样
        if dlt_data:
            pd.DataFrame(dlt_data).to_csv('dlt_data.csv', index=False, encoding='utf-8')
        if ssq_data:
            pd.DataFrame(ssq_data).to_csv('ssq_data.csv', index=False, encoding='utf-8')

if __name__ == "__main__":
    LotteryCrawler().run()
