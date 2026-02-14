import feedparser
import os
import time
import requests
from dotenv import load_dotenv
from helpers import time_difference

load_dotenv()

# 你可以根据需要调整抓取时间窗口，这里设为24小时（86400秒）
RUN_FREQUENCY = int(os.getenv("RUN_FREQUENCY", "86400"))

# ===== 国内热门资讯 RSS 源（持续更新）=====
RSS_URLS = [
    "https://36kr.com/feed",                          # 36氪
    "https://www.guokr.com/rss/",                     # 果壳
    "https://feeds.feedburner.com/zhihu-daily",       # 知乎每日精选
    "https://www.thepaper.cn/rss/news.xml",           # 澎湃新闻
    "https://www.guancha.cn/feed/news.xml",           # 观察者网
    "https://www.huxiu.com/rss/",                     # 虎嗅
    "https://rss.sina.com.cn/tech/rollnews.xml",      # 新浪科技
    "https://rss.qq.com/tech/rollnews.xml",           # 腾讯科技
    "http://www.people.com.cn/rss/politics.xml",      # 人民网
    "https://news.163.com/special/00011K6L/rss_news.xml", # 网易新闻
]

def _parse_struct_time_to_timestamp(st):
    if st:
        return time.mktime(st)
    return 0

def send_feishu_message(text):
    webhook_url = os.getenv("FEISHU_WEBHOOK")
    if not webhook_url:
        print("❌ 环境变量 FEISHU_WEBHOOK 未设置")
        return
    payload = {
        "msg_type": "text",
        "content": {"text": text}
    }
    try:
        resp = requests.post(webhook_url, json=payload)
        if resp.status_code == 200:
            print("✅ 飞书消息发送成功")
        else:
            print(f"❌ 飞书消息发送失败: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ 飞书请求异常: {e}")

def get_new_feed_items_from(feed_url):
    print(f"正在抓取 RSS: {feed_url}")
    try:
        rss = feedparser.parse(feed_url)
        print(f"RSS 解析成功，条目总数: {len(rss.entries)}")
    except Exception as e:
        print(f"Error parsing feed {feed_url}: {e}")
        return []

    current_time_struct = rss.get("updated_parsed") or rss.get("published_parsed")
    current_time = _parse_struct_time_to_timestamp(current_time_struct) if current_time_struct else time.time()

    new_items = []
    for item in rss.entries:
        pub_date = item.get("published_parsed") or item.get("updated_parsed")
        if pub_date:
            blog_published_time = _parse_struct_time_to_timestamp(pub_date)
        else:
            continue

        diff = time_difference(current_time, blog_published_time)
        if diff["diffInSeconds"] < RUN_FREQUENCY:
            new_items.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "content": item.get("content", [{}])[0].get("value", item.get("summary", "")),
                "published_parsed": pub_date
            })

    print(f"本次抓取到 {len(new_items)} 条新文章")
    return new_items

def get_new_feed_items():
    all_new_feed_items = []
    for feed_url in RSS_URLS:
        feed_items = get_new_feed_items_from(feed_url)
        all_new_feed_items.extend(feed_items)

    all_new_feed_items.sort(
        key=lambda x: _parse_struct_time_to_timestamp(x.get("published_parsed"))
    )
    print(f"总共 {len(all_new_feed_items)} 条新文章待推送")
    return all_new_feed_items
