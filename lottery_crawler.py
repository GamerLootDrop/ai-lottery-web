import requests
import pandas as pd

class LotteryCrawler:
    def __init__(self):
        # 使用专门的开源彩票数据 API，对海外 IP 友好
        self.apis = {
            "大乐透": "https://m.tool.cn/api/lottery/history?type=dlt",
            "双色球": "https://m.tool.cn/api/lottery/history?type=ssq"
        }
        self.headers = {'User-Agent': 'Mozilla/5.0'}

    def fetch_data(self, name):
        try:
            print(f"正在通过 API 接口获取 {name} 数据...")
            response = requests.get(self.apis[name], headers=self.headers, timeout=20)
            data = response.json()
            
            if data and 'data' in data:
                results = []
                for item in data['data']:
                    # 格式化期号和球号
                    issue = item.get('expect')
                    # API 返回通常是数组或逗号分隔
                    opencode = item.get('opencode', '').replace('+', ',').split(',')
                    
                    if name == "大乐透":
                        red = " ".join([x.zfill(2) for x in opencode[:5]])
                        blue = " ".join([x.zfill(2) for x in opencode[5:]])
                    else:
                        red = " ".join([x.zfill(2) for x in opencode[:6]])
                        blue = opencode[6].zfill(2)
                        
                    results.append({"期号": issue, "红球": red, "蓝球": blue})
                
                if results:
                    print(f"✅ {name} 获取成功！共 {len(results)} 期")
                    return results
        except Exception as e:
            print(f"❌ {name} API 调用失败: {e}")
        return []

    def run(self):
        # 大乐透处理
        dlt_results = self.fetch_data("大乐透")
        if dlt_results:
            pd.DataFrame(dlt_results).to_csv('dlt_data.csv', index=False, encoding='utf-8')
        
        # 双色球处理
        ssq_results = self.fetch_data("双色球")
        if ssq_results:
            pd.DataFrame(ssq_results).to_csv('ssq_data.csv', index=False, encoding='utf-8')

if __name__ == "__main__":
    LotteryCrawler().run()
