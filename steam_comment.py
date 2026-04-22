"""
爬取游戏真实评论
"""

import requests
import json
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------- 配置区（按需修改） ----------------------
APP_ID = 3764200                # 游戏appid，比如CS2是730，黑神话悟空是1593520
LANGUAGE = "schinese"        # 简体中文评论
PER_PAGE = 20               # 每页条数（Steam限制最大100）
TARGET_COUNT = 3513          # 想爬的评论总条数，改成需要的数量即可
MAX_RETRIES = 5             # 超时重试次数
TIMEOUT = 15                # 单次请求超时时间
PROXIES = {
    # "http": "http://127.0.0.1:7890",
    # "https": "http://127.0.0.1:7890"
}
# ---------------------------------------------------------------

# 带重试的请求会话
session = requests.Session()
retry_strategy = Retry(
    total=MAX_RETRIES,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

all_reviews = []
cursor = "*"  # Steam分页游标，初始为*
page = 1

while len(all_reviews) < TARGET_COUNT:
    print(f"正在爬取第 {page} 页，当前已爬 {len(all_reviews)}/{TARGET_COUNT} 条")

    url = f"https://store.steampowered.com/appreviews/{APP_ID}"
    params = {
        "json": 1,
        "filter": "all",
        "language": LANGUAGE,
        "cursor": cursor,
        "num_per_page": PER_PAGE,
        "purchase_type": "all",
    }

    try:
        resp = session.get(
            url,
            params=params,
            proxies=PROXIES if PROXIES else None,
            timeout=TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"请求失败：{e}")
        print("等待 3 秒后重试...")
        time.sleep(3)
        continue

    reviews_data = data.get("reviews", [])
    new_cursor = data.get("cursor", "*")

    # 没有更多评论时直接结束
    if not reviews_data:
        print("没有更多评论了，爬取提前结束")
        break

    # 处理当前页评论，控制不超过目标条数
    for rev in reviews_data:
        if len(all_reviews) >= TARGET_COUNT:
            break

        processed = {
            "content": rev.get("review", ""),
            "date": datetime.fromtimestamp(rev.get("timestamp_created", 0)).strftime("%Y-%m-%d"),
            "recommend": rev.get("voted_up", False)
        }
        all_reviews.append(processed)

    print(f"第 {page} 页完成，当前共 {len(all_reviews)}/{TARGET_COUNT} 条")

    # 游标未更新，说明已无下一页，结束爬取
    if new_cursor == cursor:
        print("游标未更新，已无下一页，爬取结束")
        break

    cursor = new_cursor
    page += 1
    time.sleep(1)  # 礼貌延迟，避免被限流

# 保存结果到当前目录的JSON文件
with open("resident_evil_requiem_reviews.json", "w", encoding="utf-8") as f:
    json.dump(all_reviews, f, ensure_ascii=False, indent=2)

print(f"爬取完成！共爬取 {len(all_reviews)} 条评论，已保存到 steam_reviews.json")
