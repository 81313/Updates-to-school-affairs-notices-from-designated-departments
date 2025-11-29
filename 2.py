import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime
import urllib3
from pathlib import Path

# 關閉 SSL 警告顯示（允許略過 SSL 驗證）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 網站設定 ---
WEBSITE_CONFIGS = [
    {
        # 自動化系
        'url': 'https://autoweb.nfu.edu.tw/',
        'domain_name': 'NFU_AUTO',
        'parent_selector': 'div.fusion-recent-posts-2',
        'article_selector': 'article.post',
        'title_selector': 'div.recent-posts-content h4 a',
        'date_selector': 'div.recent-posts-content p.meta span:first-child',
        'max_items': 10
    },
    {
        # 學務處
        'url': 'https://nfuosa.nfu.edu.tw/life.html',
        'domain_name': 'NFU_OSA',
        'parent_selector': 'table.category.table',
        'article_selector': 'tbody tr[class*="cat-list-row"]',
        'title_selector': 'a',
        'date_selector': 'td:nth-child(2)',
        'max_items': 10
    },
    {
        # 總務處
        'url': 
        'https://gaw.nfu.edu.tw/category/%e6%9c%80%e6%96%b0%e6%b6%88%e6%81%af/',
        'domain_name': 'NFU_GAW',
        'parent_selector': 
        'div.col.mainSection.mainSection-col-two.mainSection-pos-right#main',
        'article_selector': 'article.media',
        'title_selector': 'h1.media-heading.entry-title a',
        'date_selector': 'span.published.entry-meta_items',
        'max_items': 10
    },
    {
        # 教務處
        'url': 'https://nfuacademic.nfu.edu.tw/',
        'domain_name': 'NFU_ACADEMIC',
        'parent_selector': 'div.wp-block-gutena-tab.active',
        'article_selector': 'li.wp-block-post.post',
        'title_selector': 'h3.wp-block-post-title a, h3.wp-block-post-title',
        'date_selector': 'time[datetime]',
        'max_items': 10
    }
]

# 需略過 SSL 憑證驗證的網域
SSL_BYPASS_DOMAINS = [
    'autoweb.nfu.edu.tw',
    'nfuosa.nfu.edu.tw',
    'gaw.nfu.edu.tw',
    'nfuacademic.nfu.edu.tw'
]

def scrape_website_to_html(config):
    """
    統一公告格式並輸出至指定地點
    每次執行自動覆蓋舊檔
    """
    url = config['url']
    domain_name = config['domain_name']
    parent_selector = config['parent_selector']
    article_selector = config['article_selector']
    title_selector = config['title_selector']
    date_selector = config['date_selector']
    max_items = config['max_items']

    # 輸出目錄與檔案設定
    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir / "public"
    output_dir.mkdir(parents=True, exist_ok=True)
    html_filename = output_dir / f"{domain_name}.html"

    # 刪除舊檔案（保持最新）
    for f in os.listdir(output_dir):
        if f.startswith(domain_name) and f.endswith(".html"):
            try:
                os.remove(os.path.join(output_dir, f))
            except Exception:
                pass

    print(f"\n--- 🌐 開始處理網站: {domain_name} ({url}) ---")

    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        'AppleWebKit/537.36 (KHTML, like Gecko)'
        'Chrome/100.0.4896.60'
        'Safari/537.36'
    }

    # SSL 驗證控制
    verify_ssl = not any(d in url for d in SSL_BYPASS_DOMAINS)

    try:
        response = requests.get(url, headers=headers, timeout=15, verify=verify_ssl)
        response.raise_for_status()
        response.encoding = 'utf-8'
    except requests.exceptions.RequestException as e:
        print(f"❌ 網站請求失敗: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # 找父容器
    start_element = soup.select_one(parent_selector)
    if not start_element:
        print(f"⚠️ 找不到父容器: {parent_selector}")
        return

    # 找公告項目
    announcement_items = start_element.select(article_selector)
    if not announcement_items:
        print(f"⚠️ 找不到公告項目: {article_selector}")
        return

    formatted_posts = []

    # 處理公告項目
    for i, item in enumerate(announcement_items[:max_items]):
        title_tag = item.select_one(title_selector)
        date_tag = item.select_one(date_selector)

        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = title_tag.get('href', '#')
        date = date_tag.get_text(strip=True) if date_tag else "未提供日期"

        formatted_html = f"""
        <div class="scraped-post-item" style="border-buttom: 2px solid black; padding: 6px; margin-bottom: 5px; font-family: 'DFKai-sb','Times New Roman';">
          <div class="scraped-header">
            <span class="scraped-source">🏫 {domain_name}</span>
            <span class="scraped-date">📅 {date}</span>
          </div>
          <div class="scraped-title">
            <a href="{link}" target="_blank">{title}</a>
          </div>
        </div>
        <hr class="announcement-separator">
        """
        formatted_posts.append(formatted_html)

    # 輸出 HTML
    if formatted_posts:
        try:
            with open(html_filename, 'w', encoding='utf-8-sig') as f:
                f.write(f'<div class="scraped-list-container unified-announcements">\n')
                for post in formatted_posts:
                    f.write(post)
                f.write('</div>\n')

            print(f"✅ {domain_name} 完成！共 {len(formatted_posts)} 筆公告，輸出至：{os.path.abspath(html_filename)}")
        except Exception as e:
            print(f"❌ 寫入 HTML 發生錯誤: {e}")
    else:
        print(f"ℹ️ {domain_name} 未抓取到任何公告。")


# --- 主程式 ---
if __name__ == '__main__':
    print("📢 開始批次抓取公告（統一格式）...\n")
    for config in WEBSITE_CONFIGS:
        scrape_website_to_html(config)
        time.sleep(2)
    print("\n🎉 全部網站處理完成！統一公告輸出於 ./output 目錄。")
