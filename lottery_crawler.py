#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票历史开奖数据爬虫 - 自动更新版
支持：双色球 (SSQ)、大乐透 (DLT)
"""

import requests
import csv
import re
import os
from datetime import datetime

class LotteryCrawler:
    """彩票数据爬虫类"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def fetch_ssq(self):
        """抓取双色球历史数据（最近 100 期）"""
        url = "https://datachart.500.com/ssq/history/history.shtml"
        all_data = []
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'gb2312'
            if response.status_code == 200:
                html = response.text
                pattern = r'<tr[^>]*class=["\']t_tr1["\'][^>]*>(.*?)</tr>'
                rows = re.findall(pattern, html, re.DOTALL)
                # 这里的 [:100] 确保抓取 100 期
                for row in rows[:100]:
                    td_pattern = r'<td[^>]*>([^<]*)</td>'
                    tds = re.findall(td_pattern, row)
                    if len(tds) >= 9:
                        issue = tds[1].strip()
                        red_balls = [tds[i].strip() for i in range(2, 8)]
                        blue_ball = tds[8].strip()
                        if issue.isdigit():
                            all_data.append({'期号': issue, '红球': ' '.join(red_balls), '蓝球': blue_ball})
            print(f"[OK] SSQ fetched {len(all_data)} draws")
        except Exception as e:
            print(f"[ERROR] SSQ fetch error: {e}")
        return all_data
    
    def fetch_dlt(self):
        """抓取大乐透历史数据（最近 100 期）"""
        url = "http://datachart.500.com/dlt/history/history.shtml"
        all_data = []
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'gb2312'
            if response.status_code == 200:
                html = response.text
                pattern = r'<tr[^>]*class=["\']t_tr1["\'][^>]*>(.*?)</tr>'
                rows = re.findall(pattern, html, re.DOTALL)
                # 这里的 [:100] 确保抓取 100 期
                for row in rows[:100]:
                    td_pattern = r'<td[^>]*>([^<]*)</td>'
                    tds = re.findall(td_pattern, row)
                    if len(tds) >= 9:
                        issue = tds[1].strip()
                        red_balls = [tds[i].strip() for i in range(2, 7)]
                        blue_balls = [tds[i].strip() for i in range(7, 9)]
                        if issue.isdigit():
                            all_data.append({'期号': issue, '红球': ' '.join(red_balls), '蓝球': ' '.join(blue_balls)})
            print(f"[OK] DLT fetched {len(all_data)} draws")
        except Exception as e:
            print(f"[ERROR] DLT fetch error: {e}")
        return all_data
    
    def save_to_csv(self, data, filename, fieldnames):
        """保存数据到当前目录"""
        if not data: return
        # 删掉了原本写死的 C 盘路径，改用当前程序运行的路径
        filepath = os.path.join(os.getcwd(), filename)
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            print(f"[OK] Saved: {filepath}")
        except Exception as e:
            print(f"[ERROR] Save failed: {e}")

    def run(self):
        ssq_data = self.fetch_ssq()
        if ssq_data: self.save_to_csv(ssq_data, 'ssq_data.csv', ['期号', '红球', '蓝球'])
        dlt_data = self.fetch_dlt()
        if dlt_data: self.save_to_csv(dlt_data, 'dlt_data.csv', ['期号', '红球', '蓝球'])

if __name__ == "__main__":
    crawler = LotteryCrawler()
    crawler.run()
