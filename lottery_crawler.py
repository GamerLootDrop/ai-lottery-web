import requests
import pandas as pd
import time

class LotteryCrawler:
    def __init__(self):
        self.session = requests.Session()
        # 模拟更真实的浏览器，防止被屏蔽
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.google.com/'
        }

    def fetch_ssq(self):
        # 换用网易彩票或类似的轻量源，对海外IP更友好
        url = "http://kaijiang.zhcw.com/zhcw/html/ssq/list_1.html"
        try:
            print("尝试抓取双色球...")
            # 增加超时到 60 秒，跨海网络延迟大
            response = self.session.get(url, timeout=60, headers=self.headers)
            # 强制用 Pandas 尝试解析所有表格
            tables = pd.read_html(response.text)
            for df in tables:
                if '开奖日期' in df.columns or '期号' in df.columns:
                    # 网易/中彩网结构的清洗
                    df = df.dropna(subset=[df.columns[1]]) # 去掉空行
                    results = []
                    for _, row in df.iterrows():
                        issue = str(row.iloc[1]).strip()
                        if issue.isdigit() and len(issue) >= 5:
                            # 提取红球（通常在第3列）
                            balls = str(row.iloc[2]).split()
                            if len(balls) >= 7:
                                results.append({
                                    '期号': issue, 
                                    '红球': ' '.join(balls[:6]), 
                                    '蓝球': balls[6]
                                })
                    if results:
                        return results[:100]
        except Exception as e:
            print(f"SSQ 抓取失败: {e}")
        return []

    def fetch_dlt(self):
        # 大乐透使用 500.com 的新版 API 路径，通常比历史页面更稳定
        url = "http://datachart.500.com/dlt/history/new_history.shtml"
        try:
            print("尝试抓取大乐透...")
            response = self.session.get(url, timeout=60, headers=self.headers)
            response.encoding = 'utf-8'
            tables = pd.read_html(response.text)
            for df in tables:
                # 寻找包含数据的表格
                if df.shape[1] > 10:
                    results = []
                    # 500.com 的表格通常第一行是标题，需要跳过
                    for i in range(len(df)):
                        row = df.iloc[i]
                        issue = str(row[1]).strip()
                        if issue.isdigit() and len(issue) >= 5:
                            red = ' '.join([str(row[j]) for j in range(2, 7)])
                            blue = ' '.join([str(row[j]) for j in range(7, 9)])
                            results.append({'期号': issue, '红球': red, '蓝球': blue})
                    if results:
                        return results[:100]
        except Exception as e:
            print(f"DLT 抓取失败: {e}")
        return []

    def run(self):
        # 强制重写文件，确保只要抓到一点就同步
        for name, func, filename in [("大乐透", self.fetch_dlt, 'dlt_data.csv'), ("双色球", self.fetch_ssq, 'ssq_data.csv')]:
            data = func()
            if data:
                pd.DataFrame(data).to_csv(filename, index=False, encoding='utf-8')
                print(f"🎉 {name} 成功同步 {len(data)} 期")
            else:
                # 如果没抓到，至少写个表头保命，别让网页崩了
                pd.DataFrame(columns=['期号', '红球', '蓝球']).to_csv(filename, index=False, encoding='utf-8')
                print(f"❌ {name} 抓取完全失败，已写空表头")

if __name__ == "__main__":
    LotteryCrawler().run()
