import requests
import pandas as pd
import time

class LotteryCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def fetch_data(self, game_name):
        # 换用网易彩票镜像源，对海外服务器非常友好
        urls = {
            "大乐透": "https://piao.163.com/lottery/history.html?lotteryType=dlt",
            "双色球": "https://piao.163.com/lottery/history.html?lotteryType=ssq"
        }
        
        try:
            print(f"正在从网易源抓取 {game_name}...")
            # 使用 pandas 的 read_html 直接暴力扫描网页上的所有表格
            # 这种方法即便 IP 限制也能穿透大部分简单的 HTML 结构
            response = self.session.get(urls[game_name], timeout=60, headers=self.headers)
            response.encoding = 'utf-8'
            
            tables = pd.read_html(response.text)
            for df in tables:
                # 识别包含开奖数据的表格
                if df.shape[1] > 8:
                    results = []
                    for _, row in df.iterrows():
                        issue = str(row.iloc[0]).strip()
                        # 只要前几位是数字，通常就是期号
                        if issue.isdigit() and len(issue) >= 5:
                            cells = [str(x).strip().zfill(2) for x in row.values]
                            if game_name == "大乐透":
                                red = ' '.join(cells[1:6])
                                blue = ' '.join(cells[6:8])
                            else: # 双色球
                                red = ' '.join(cells[1:7])
                                blue = cells[7]
                            results.append({'期号': issue, '红球': red, '蓝球': blue})
                    
                    if results:
                        print(f"✅ {game_name} 抓取成功: {len(results)} 期")
                        return results[:100]
        except Exception as e:
            print(f"❌ {game_name} 抓取失败: {e}")
        return []

    def run(self):
        # 抓取并立即保存
        for name, filename in [("大乐透", "dlt_data.csv"), ("双色球", "ssq_data.csv")]:
            data = self.fetch_data(name)
            if data:
                pd.DataFrame(data).to_csv(filename, index=False, encoding='utf-8')
            else:
                # 保底机制：如果抓不到，也要写个表头，防止 Streamlit 网页报错
                pd.DataFrame(columns=['期号', '红球', '蓝球']).to_csv(filename, index=False, encoding='utf-8')

if __name__ == "__main__":
    LotteryCrawler().run()
