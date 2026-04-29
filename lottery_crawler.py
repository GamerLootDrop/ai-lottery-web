import requests
import pandas as pd
import time

class LotteryCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_data(self, url, name):
        # 尝试国内备用源
        for i in range(3):
            try:
                print(f"正在尝试第 {i+1} 次抓取 {name}...")
                # 调大超时时间到 40 秒，应对跨境网络延迟
                response = self.session.get(url, timeout=40, headers=self.headers)
                response.encoding = 'utf-8' # 备用源通常用 utf-8
                
                if response.status_code == 200:
                    # 使用 pandas 直接解析网页表格（最暴力有效的方法）
                    tables = pd.read_html(response.text)
                    for df in tables:
                        # 寻找包含“期号”的表格
                        if '期号' in df.columns or df.iloc[0].astype(str).str.contains('期号').any():
                            # 简单清洗
                            df.columns = df.iloc[0] # 把第一行设为表头
                            df = df.drop(0)
                            
                            results = []
                            for _, row in df.iterrows():
                                issue = str(row.get('期号', '')).strip()
                                if issue.isdigit() and len(issue) >= 5:
                                    # 提取红球和蓝球（根据列位置适配）
                                    # 这里做了通用处理，防止不同网站列名不一
                                    cells = row.values.tolist()
                                    if name == "大乐透":
                                        red = ' '.join([str(cells[j]) for j in range(2, 7)])
                                        blue = ' '.join([str(cells[j]) for j in range(7, 9)])
                                    else:
                                        red = ' '.join([str(cells[j]) for j in range(2, 8)])
                                        blue = str(cells[8])
                                    results.append({'期号': issue, '红球': red, '蓝球': blue})
                            
                            if results:
                                print(f"成功！抓取到 {len(results)} 期 {name}")
                                return results[:100]
                time.sleep(5)
            except Exception as e:
                print(f"抓取出错: {e}")
        return []

    def run(self):
        # 使用更稳定的备用路径
        dlt = self.fetch_data("https://datachart.500.com/dlt/history/new_history.shtml", "大乐透")
        if dlt:
            pd.DataFrame(dlt).to_csv('dlt_data.csv', index=False, encoding='utf-8')
        
        ssq = self.fetch_data("https://datachart.500.com/ssq/history/new_history.shtml", "双色球")
        if ssq:
            pd.DataFrame(ssq).to_csv('ssq_data.csv', index=False, encoding='utf-8')

if __name__ == "__main__":
    LotteryCrawler().run()
