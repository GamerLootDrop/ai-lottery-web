#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票历史开奖数据爬虫
支持：双色球 (SSQ)、大乐透 (DLT)
数据源：500 彩票网
"""

import requests
import csv
import re
from datetime import datetime


class LotteryCrawler:
    """彩票数据爬虫类"""
    
    # 保存路径 - 桌面彩民服务文件夹
    SAVE_DIR = r"C:\Users\86131\Desktop\彩民服务"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def fetch_ssq(self):
        """
        抓取双色球历史数据（最近 100 期）
        
        Returns:
            list: 双色球数据列表
        """
        url = "https://datachart.500.com/ssq/history/history.shtml"
        all_data = []
        
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'gb2312'
            
            if response.status_code != 200:
                print(f"[ERROR] SSQ request failed: {response.status_code}")
                return all_data
            
            html = response.text
            
            # 查找表格中的数据行 (class="t_tr1")
            pattern = r'<tr[^>]*class=["\']t_tr1["\'][^>]*>(.*?)</tr>'
            rows = re.findall(pattern, html, re.DOTALL)
            
            for row in rows[:100]:
                # 提取所有 TD 内容
                td_pattern = r'<td[^>]*>([^<]*)</td>'
                tds = re.findall(td_pattern, row)
                
                # 双色球表格结构:
                # TD[0]: 序号 (注释中)
                # TD[1]: 期号
                # TD[2-7]: 红球 6 个
                # TD[8]: 蓝球
                if len(tds) >= 9:
                    issue = tds[1].strip()
                    red_balls = [tds[i].strip() for i in range(2, 8)]
                    blue_ball = tds[8].strip()
                    
                    # 验证期号是数字
                    if issue.isdigit() and len(issue) == 5:
                        all_data.append({
                            '期号': issue,
                            '红球': ' '.join(red_balls),
                            '蓝球': blue_ball
                        })
            
            print(f"[OK] SSQ fetched {len(all_data)} draws")
            
        except Exception as e:
            print(f"[ERROR] SSQ fetch error: {e}")
        
        return all_data
    
    def fetch_dlt(self):
        """
        抓取大乐透历史数据（最近 100 期）
        
        Returns:
            list: 大乐透数据列表
        """
        url = "http://datachart.500.com/dlt/history/history.shtml"
        all_data = []
        
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'gb2312'
            
            if response.status_code != 200:
                print(f"[ERROR] DLT request failed: {response.status_code}")
                return all_data
            
            html = response.text
            
            # 查找表格中的数据行 (class="t_tr1")
            pattern = r'<tr[^>]*class=["\']t_tr1["\'][^>]*>(.*?)</tr>'
            rows = re.findall(pattern, html, re.DOTALL)
            
            for row in rows[:100]:
                # 提取所有 TD 内容
                td_pattern = r'<td[^>]*>([^<]*)</td>'
                tds = re.findall(td_pattern, row)
                
                # 大乐透表格结构:
                # TD[1]: 期号
                # TD[2-6]: 前区（红球）5 个
                # TD[7-8]: 后区（蓝球）2 个
                if len(tds) >= 9:
                    issue = tds[1].strip()
                    red_balls = [tds[i].strip() for i in range(2, 7)]
                    blue_balls = [tds[i].strip() for i in range(7, 9)]
                    
                    # 验证期号是数字
                    if issue.isdigit() and len(issue) == 5:
                        all_data.append({
                            '期号': issue,
                            '红球': ' '.join(red_balls),
                            '蓝球': ' '.join(blue_balls)
                        })
            
            print(f"[OK] DLT fetched {len(all_data)} draws")
            
        except Exception as e:
            print(f"[ERROR] DLT fetch error: {e}")
        
        return all_data
    
    def save_to_csv(self, data, filename, fieldnames):
        """
        保存数据到 CSV 文件
        
        Args:
            data: 数据列表
            filename: 文件名
            fieldnames: 表头字段
        """
        if not data:
            print(f"[WARN] No data to save: {filename}")
            return
        
        # 使用绝对路径保存到桌面文件夹
        import os
        filepath = os.path.join(self.SAVE_DIR, filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            print(f"[OK] Saved: {filepath}")
        except Exception as e:
            print(f"[ERROR] Save failed: {e}")
    
    def run(self):
        """执行完整抓取流程"""
        print("=" * 50)
        print("Lottery Data Crawler")
        print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # 抓取双色球
        print("\nFetching SSQ (Double Color Ball)...")
        ssq_data = self.fetch_ssq()
        if ssq_data:
            self.save_to_csv(
                ssq_data, 
                'ssq_data.csv', 
                ['期号', '红球', '蓝球']
            )
        
        # 抓取大乐透
        print("\nFetching DLT (Da Le Tou)...")
        dlt_data = self.fetch_dlt()
        if dlt_data:
            self.save_to_csv(
                dlt_data, 
                'dlt_data.csv', 
                ['期号', '红球', '蓝球']
            )
        
        print("\n" + "=" * 50)
        print("Complete!")
        print("=" * 50)
        
        return ssq_data, dlt_data


def main():
    """主函数"""
    crawler = LotteryCrawler()
    ssq_data, dlt_data = crawler.run()
    
    # 显示部分数据预览
    if ssq_data:
        print("\nSSQ Latest 5 Draws:")
        for item in ssq_data[:5]:
            print(f"  Issue: {item['期号']} | Red: {item['红球']} | Blue: {item['蓝球']}")
    
    if dlt_data:
        print("\nDLT Latest 5 Draws:")
        for item in dlt_data[:5]:
            print(f"  Issue: {item['期号']} | Red: {item['红球']} | Blue: {item['蓝球']}")


if __name__ == "__main__":
    main()
