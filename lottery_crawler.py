import requests
import pandas as pd
import time
import io

class LotteryCrawler:
    def __init__(self):
        self.session = requests.Session()
        # 使用更像真实人类的浏览器头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }

    def fetch_data(self, url, name):
        for i in range(3):  # 自动重试3次
            try:
                print(f"正在尝试抓取 {name} (第 {i+1} 次)...")
                # 增加超时到 60 秒，应对跨海网络延迟
                response = self.session.get(url, timeout=60, headers=self.headers)
                response.encoding = 'gb2312'
                
                # 暴力解析：直接把网页里的所有表格抠出来
                tables = pd.read_html(io.StringIO(response.text))
                for df in tables:
                    # 检查是否是目标开奖表格（通常列数较多）
                    if df.shape[1] >= 7:
                        results = []
                        # 遍历表格行
                        for _, row in df.iterrows():
                            # 提取期号（通常在第1或第2列）
                            issue = str(row.values[1]).strip()
                            if issue.isdigit() and len(issue) >= 5:
                                vals = [str(v).strip() for v in row.values]
                                if name == "大乐透":
                                    # 大乐透 5红 + 2蓝
                                    red = ' '.join(vals[2:7])
                                    blue = ' '.join(vals[7:9])
                                else:
                                    # 双色球 6红 + 1蓝
                                    red = ' '.join(vals[2:8])
                                    blue = vals[8]
                                results.append({'期号': issue, '红球': red, '蓝球': blue})
                        
                        if results:
                            print(f"🎉 {name} 抓取成功: {len(results)} 期")
                            return results[:100]
                time.sleep(5)
            except Exception as e:
                print(f"抓取出错: {e}")
        return []

    def run(self):
        # 两个源分别抓取
        dlt = self.fetch_data("http://datachart.500.com/dlt/history/new_history.shtml", "大乐透")
        if dlt:
            pd.DataFrame(dlt).to_csv('dlt_data.csv', index=False, encoding='utf-8')
        
        ssq = self.fetch_data("http://datachart.500.com/ssq/history/history.shtml", "双色球")
        if ssq:
            pd.DataFrame(ssq).to_csv('ssq_data.csv', index=False, encoding='utf-8')

if __name__ == "__main__":
    LotteryCrawler().run()
