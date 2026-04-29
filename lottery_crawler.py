import requests
import re
import pandas as pd
import time

class LotteryCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_data(self, url, name):
        for i in range(3):  # 失败自动重试3次
            try:
                print(f"正在抓取 {name}, 第 {i+1} 次尝试...")
                response = self.session.get(url, timeout=30)
                response.encoding = 'gb2312'
                if response.status_code == 200:
                    html = response.text
                    pattern = r'<tr[^>]*class=["\']t_tr1["\'][^>]*>(.*?)</tr>'
                    rows = re.findall(pattern, html, re.DOTALL)
                    results = []
                    for row in rows:
                        tds = re.findall(r'<td[^>]*>([^<]*)</td>', row)
                        if len(tds) >= 9:
                            issue = tds[1].strip()
                            if issue.isdigit() and len(issue) >= 5:
                                if name == "大乐透":
                                    red = ' '.join([tds[j].strip() for j in range(2, 7)])
                                    blue = ' '.join([tds[j].strip() for j in range(7, 9)])
                                else: # 双色球
                                    red = ' '.join([tds[j].strip() for j in range(2, 8)])
                                    blue = tds[8].strip()
                                results.append({'期号': issue, '红球': red, '蓝球': blue})
                    if results:
                        print(f"成功抓取 {name} {len(results)} 期")
                        return results[:100]
            except Exception as e:
                print(f"{name} 尝试失败: {e}")
                time.sleep(5)
        return []

    def run(self):
        # 强制写入，不管抓到多少，先写进去看看
        dlt = self.fetch_data("http://datachart.500.com/dlt/history/history.shtml", "大乐透")
        if dlt:
            pd.DataFrame(dlt).to_csv('dlt_data.csv', index=False, encoding='utf-8')
        
        ssq = self.fetch_data("https://datachart.500.com/ssq/history/history.shtml", "双色球")
        if ssq:
            pd.DataFrame(ssq).to_csv('ssq_data.csv', index=False, encoding='utf-8')

if __name__ == "__main__":
    LotteryCrawler().run()
