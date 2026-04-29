import requests
import re
import pandas as pd
import os

class LotteryCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_ssq(self):
        url = "https://datachart.500.com/ssq/history/history.shtml"
        all_data = []
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'gb2312'
            if response.status_code == 200:
                html = response.text
                pattern = r'<tr[^>]*class=["\']t_tr1["\'][^>]*>(.*?)</tr>'
                rows = re.findall(pattern, html, re.DOTALL)
                for row in rows:
                    td_pattern = r'<td[^>]*>([^<]*)</td>'
                    tds = re.findall(td_pattern, row)
                    if len(tds) >= 9:
                        issue = tds[1].strip()
                        # 严格过滤：期号必须是5位及以上数字，彻底排除“注数/奖金”等垃圾行
                        if issue.isdigit() and len(issue) >= 5:
                            red_balls = [tds[i].strip() for i in range(2, 8)]
                            blue_ball = tds[8].strip()
                            all_data.append({'期号': issue, '红球': ' '.join(red_balls), '蓝球': blue_ball})
                all_data = all_data[:100]
            print(f"[OK] SSQ 抓取成功: {len(all_data)} 期")
        except Exception as e:
            print(f"[ERROR] SSQ 错误: {e}")
        return all_data

    def fetch_dlt(self):
        url = "http://datachart.500.com/dlt/history/history.shtml"
        all_data = []
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'gb2312'
            if response.status_code == 200:
                html = response.text
                pattern = r'<tr[^>]*class=["\']t_tr1["\'][^>]*>(.*?)</tr>'
                rows = re.findall(pattern, html, re.DOTALL)
                for row in rows:
                    td_pattern = r'<td[^>]*>([^<]*)</td>'
                    tds = re.findall(td_pattern, row)
                    if len(tds) >= 9:
                        issue = tds[1].strip()
                        # 严格过滤垃圾数据，确保 CSV 只有干净的数字
                        if issue.isdigit() and len(issue) >= 5:
                            red_balls = [tds[i].strip() for i in range(2, 7)]
                            blue_balls = [tds[i].strip() for i in range(7, 9)]
                            all_data.append({'期号': issue, '红球': ' '.join(red_balls), '蓝球': ' '.join(blue_balls)})
                all_data = all_data[:100]
            print(f"[OK] DLT 抓取成功: {len(all_data)} 期")
        except Exception as e:
            print(f"[ERROR] DLT 错误: {e}")
        return all_data

    def run(self):
        # 核心改进：直接 to_csv 覆盖，不读取旧文件，彻底避开空文件报错
        dlt_results = self.fetch_dlt()
        if dlt_results:
            pd.DataFrame(dlt_results).to_csv('dlt_data.csv', index=False, encoding='utf-8')
            print("DLT 数据已强制重写 [dlt_data.csv]")
        
        ssq_results = self.fetch_ssq()
        if ssq_results:
            pd.DataFrame(ssq_results).to_csv('ssq_data.csv', index=False, encoding='utf-8')
            print("SSQ 数据已强制重写 [ssq_data.csv]")

if __name__ == "__main__":
    crawler = LotteryCrawler()
    crawler.run()
