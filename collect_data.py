#!/usr/bin/env python3
"""
数据收集脚本 - 收集论文和新闻数据并保存到本地
"""
import json
import os
import sys
import subprocess
from datetime import datetime

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
PAPERS_FILE = os.path.join(DATA_DIR, 'papers.json')
NEWS_FILE = os.path.join(DATA_DIR, 'news.json')

def ensure_data_dir():
    """确保数据目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)

def collect_papers():
    """收集论文数据"""
    print("📚 收集论文数据...", file=sys.stderr)
    
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'monitor_radiotherapy_ai.py')
    
    try:
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            papers = json.loads(result.stdout)
            print(f"  ✅ 收集到 {len(papers)} 篇论文", file=sys.stderr)
            return papers
        else:
            print(f"  ❌ 论文收集失败: {result.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"  ❌ 论文收集错误: {e}", file=sys.stderr)
    
    return []

def collect_news():
    """收集新闻数据"""
    print("📰 收集新闻数据...", file=sys.stderr)
    
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'fetch_radiotherapy_news.py')
    
    try:
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            news = json.loads(result.stdout)
            print(f"  ✅ 收集到 {len(news)} 条新闻", file=sys.stderr)
            return news
        else:
            print(f"  ❌ 新闻收集失败: {result.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"  ❌ 新闻收集错误: {e}", file=sys.stderr)
    
    return []

def save_data(papers, news):
    """保存数据到文件"""
    ensure_data_dir()
    
    with open(PAPERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    print(f"  💾 论文数据已保存到 {PAPERS_FILE}", file=sys.stderr)
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=2)
    print(f"  💾 新闻数据已保存到 {NEWS_FILE}", file=sys.stderr)

def main():
    print(f"🔄 开始收集数据...", file=sys.stderr)
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)
    
    papers = collect_papers()
    news = collect_news()
    
    save_data(papers, news)
    
    print(f"\n📊 数据收集完成:", file=sys.stderr)
    print(f"  - 论文: {len(papers)} 篇", file=sys.stderr)
    print(f"  - 新闻: {len(news)} 条", file=sys.stderr)
    print(f"  - 总计: {len(papers) + len(news)} 条", file=sys.stderr)
    
    stats = {
        'timestamp': datetime.now().isoformat(),
        'papers_count': len(papers),
        'news_count': len(news),
        'total_count': len(papers) + len(news),
    }
    print(json.dumps(stats, ensure_ascii=False))

if __name__ == "__main__":
    main()
