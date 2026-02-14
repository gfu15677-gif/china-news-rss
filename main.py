from feed import get_new_feed_items, send_feishu_message

def main():
    items = get_new_feed_items()
    if items:
        for item in items:
            text = f"{item['title']}\n{item['link']}"
            send_feishu_message(text)
    else:
        print("没有新文章")

if __name__ == "__main__":
    main()
