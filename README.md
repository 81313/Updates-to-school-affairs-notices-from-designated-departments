# 下載之後請在同目錄下建立"public"資料夾，或是下載之後更改檔案目的地也可以
# 🟦 1. 匯入必要套件

```
import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime
import urllib3
from pathlib import Path
```
功能用途：
* requests：發送 HTTP 請求
* BeautifulSoup：解析 HTML
* os / Path：處理檔案路徑
* time：做網頁抓取之間的延遲
* datetime：可做日期處理
* urllib3：用來關閉 SSL 警告

# 🟦 2. 關閉 SSL 警告  
有些網站憑證不完整，requests 會跳警告，這行是避免畫面亂掉。   
```
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

# 🟦 3. `WEBSITE_CONFIGS` — 四個網站的爬取設定
```
WEBSITE_CONFIGS = [
    { ... 自動化系設定 ... },
    { ... 學務處設定 ... },
    { ... 總務處設定 ... },
    { ... 教務處設定 ... }
]
```
| Key                | 用途                              |
| ------------------ | ------------------------------- |
| `url`              | 要爬的網站首頁（公告頁面）                   |
| `domain_name`      | 會被用來命名 HTML 檔，如 `NFU_AUTO.html` |
| `parent_selector`  | 包住整個公告區的 HTML 父層                |
| `article_selector` | 代表一則公告的 HTML 元素                 |
| `title_selector`   | 標題所在位置                          |
| `date_selector`    | 日期所在位置                          |
| `max_items`        | 要最多抓幾筆公告                        |  

整個爬蟲之所以能統一格式，就是因為每個網站的 HTML 用不同 CSS 選擇器定位。

# 🟦 4. SSL 例外處理列表
```
SSL_BYPASS_DOMAINS = [
    'autoweb.nfu.edu.tw',
    'nfuosa.nfu.edu.tw',
    'gaw.nfu.edu.tw',
    'nfuacademic.nfu.edu.tw'
]
```
在這些網站上：
* SSL 驗證會被跳過（verify=False）
* 避免爬蟲因 SSL 錯誤失敗

# 🟦 5. 函式`scrape_website_to_html(config)`
主要的公告抓取＋儲存的邏輯都在這裡。
流程如下：
* 1. 讀取網站設定  
像：
  * URL
  * 父容器
  * 公告項目
  * 標題位置/日期位置  
全部從設定讀出來：
```
url = config['url']
domain_name = config['domain_name']
...
```
* 2. 準備輸出資料夾
輸出資料存放於`public/`
```
script_dir = Path(__file__).resolve().parent
output_dir = script_dir / "public"
output_dir.mkdir(parents=True, exist_ok=True)
```
命名輸出檔案規則為`{domain_name}.html`，例如： NFU_AUTO.html
* 3. 刪除舊檔案（保持資料最新）
避免同名檔案堆積：
```
for f in os.listdir(output_dir):
    if f.startswith(domain_name) and f.endswith(".html"):
        os.remove(...)
```
* 4. 對目標網站發送 HTTP 連線
```
verify_ssl = not any(d in url for d in SSL_BYPASS_DOMAINS)
response = requests.get(url, headers=headers, timeout=15, verify=verify_ssl)
```
作用是：
  * 自動判斷這個網站是否要跳過 SSL 驗證
  * timeout=15 秒避免卡住
  * 自訂 UA（避免被網站判定為爬蟲）
* 5. 用 BeautifulSoup 解析 HTML
```
soup = BeautifulSoup(response.text, 'html.parser')
```
* 6. 找父容器（公告外層）
```
start_element = soup.select_one(parent_selector)
```
若找不到，代表網站版面改過，直接結束，並顯示`⚠️ 找不到父容器`
* 7. 抓公告項目列表
```
announcement_items = start_element.select(article_selector)
```
每個項目代表一則公告。
* 8. 對每一則公告做解析
  * 標題
  * 連結
  * 日期
```
title_tag = item.select_one(title_selector)
date_tag = item.select_one(date_selector)\
```
***若沒標題 → 跳過***  
接著將內容組成統一HTML格式：
```
<div class="scraped-post-item">
  <div class="scraped-header">
    <span class="scraped-source">🏫 NFU_AUTO</span>
    <span class="scraped-date">📅 2024-01-01</span>
  </div>
  <div class="scraped-title">
    <a href="..." target="_blank">公告標題</a>
  </div>
</div>
<hr>
```
***這裡讓所有網站輸出的格式一致，方便前端排版***
* 9. 寫入 HTML 檔案
將所有公告一次寫入檔案：
```
with open(html_filename, 'w', encoding='utf-8-sig') as f:
    f.write(...)
```
並印出結果(舉例)：`✅ NFU_AUTO 完成！共 10 筆公告`
# 🟦 6.主程式執行區塊
```
if __name__ == '__main__':
```
程式運作流程：
* 1.印出「開始抓取」
* 2.逐一處理 WEBSITE_CONFIGS 的四個網站
* 3.每抓一個網站停 2 秒（避免攻擊網站）
* 4.全部完成後印出結束訊息
```
for config in WEBSITE_CONFIGS:
    scrape_website_to_html(config)
    time.sleep(2)
```
***🎉 程式最終作用總結***

這份程式的完成效果：  
✔ 批次從四個不同網站抓取最新公告  
✔ 每個網站抓固定數量的公告（例如 10 則）  
✔ 解析 HTML → 抓標題、日期、連結  
✔ 將公告轉換成統一 HTML 樣式  
✔ 分別輸出成不同名稱的 HTML  
✔ 可提供給前端直接 include 顯示（iframe / ajax / 模板）  
✔ 避免 SSL 問題、自動清除舊檔、格式高度統一  
