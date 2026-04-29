# ... 前面部分保持不变 ...

    def fetch_ssq(self):
        url = "https://datachart.500.com/ssq/history/history.shtml"
        all_data = []
        try:
            response = self.session.get(url, timeout=10)
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
                        # --- 核心改进：严格要求期号必须是5位及以上的纯数字，排除表头 ---
                        if issue.isdigit() and len(issue) >= 5:
                            red_balls = [tds[i].strip() for i in range(2, 8)]
                            blue_ball = tds[8].strip()
                            all_data.append({'期号': issue, '红球': ' '.join(red_balls), '蓝球': blue_ball})
                
                # 过滤后再取前 100 期，确保全是干净数据
                all_data = all_data[:100]
            print(f"[OK] SSQ fetched {len(all_data)} clean draws")
        except Exception as e:
            print(f"[ERROR] SSQ fetch error: {e}")
        return all_data

    def fetch_dlt(self):
        url = "http://datachart.500.com/dlt/history/history.shtml"
        all_data = []
        try:
            response = self.session.get(url, timeout=10)
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
                        # --- 核心改进：严格过滤，确保期号纯净 ---
                        if issue.isdigit() and len(issue) >= 5:
                            red_balls = [tds[i].strip() for i in range(2, 7)]
                            blue_balls = [tds[i].strip() for i in range(7, 9)]
                            all_data.append({'期号': issue, '红球': ' '.join(red_balls), '蓝球': ' '.join(blue_balls)})
                
                # 过滤后再取前 100 期
                all_data = all_data[:100]
            print(f"[OK] DLT fetched {len(all_data)} clean draws")
        except Exception as e:
            print(f"[ERROR] DLT fetch error: {e}")
        return all_data

    # ... 后面保存 CSV 的部分保持不变 ...
