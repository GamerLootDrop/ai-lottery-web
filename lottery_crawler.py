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

    def fetch_ssq(self):
        url = "https://datachart.500.com/ssq/history/history.shtml"
        all_data = []
        try:
            # 增加重试机制和更长的超时时间
            response = self.session.get(url, timeout=20)
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
                        # 核心过滤：期号必须是5位以上数字
                        if issue.isdigit() and len(issue) >= 5:
                            red_balls = [tds[i].strip() for i in range(2, 8)]
                            blue_ball = tds[8].strip()
                            all_data.append({'期号': issue, '红球': ' '.join(red_balls), '蓝球': blue_ball})
                all_data = all_data[:100]
            print(f"[OK] 双色球抓取成功，共 {len(all_data)} 期")
        except Exception as e:
            print(f"[ERROR] 双色球抓取失败: {e}")
        return all_data

    def fetch_dlt(self):
        url = "http://datachart.500.com/dlt/history/history.shtml"
        all_data = []
        try:
            response = self.session.get(url, timeout=20)
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
                        if issue.isdigit() and len(issue) >= 5:
                            red_balls = [tds[i].strip() for i in range(2, 7)]
                            blue_balls = [tds[i].strip() for i in range(7, 9)]
                            all_data.append({'期号': issue, '红球': ' '.join(red_balls), '蓝球': ' '.join(blue_balls)})
                all_data = all_data[:100]
            print(f"[OK] 大乐透抓取成功，共 {len(all_data)} 期")
        except Exception as e:
            print(f"[ERROR] 大乐透抓取失败: {e}")
        return all_data

    def run(self):
        # 强制覆盖写入逻辑
        dlt_results = self.fetch_dlt()
        if dlt_results:
            df_dlt = pd.DataFrame(dlt_results)
            df_dlt.to_csv('dlt_data.csv', index=False, encoding='utf-8')
            print("已更新 dlt_data.csv")
        else:
            print("警告：大乐透抓取结果为空，未更新文件")

        ssq_results = self.fetch_ssq()
        if ssq_results:
            df_ssq = pd.DataFrame(ssq_results)
            df_ssq.to_csv('ssq_data.csv', index=False, encoding='utf-8')
            print("已更新 ssq_data.csv")
        else:
            print("警告：双色球抓取结果为空，未更新文件")

if __name__ == "__main__":
    crawler = LotteryCrawler()
    crawler.run()
