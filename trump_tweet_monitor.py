import os
import time
from datetime import datetime
import json
import requests
from dotenv import load_dotenv
import feedparser

# 加载环境变量
load_dotenv()

# 飞书webhook URL
FEISHU_WEBHOOK_URL = os.getenv('FEISHU_WEBHOOK_URL', 'https://open.feishu.cn/open-apis/bot/v2/hook/51fac4c6-a9ec-4d1e-9a8c-cad6a0be2b63')

# RSS 源地址
TRUMP_RSS_URL = "https://nitter.net/realDonaldTrump/rss"

def send_to_feishu(text):
    """发送消息到飞书"""
    data = {
        "msg_type": "text",
        "content": {
            "text": text
        }
    }
    response = requests.post(FEISHU_WEBHOOK_URL, json=data)
    if response.status_code != 200:
        print(f"发送消息失败: {response.text}")
    else:
        print("消息发送成功")

def format_tweet_message(entry):
    """格式化推文消息"""
    return f"""特朗普发布推文：
时间：{entry.published}
内容：{entry.title}
链接：{entry.link}"""

def push_recent_tweets(count=3):
    """推送最近的推文"""
    try:
        feed = feedparser.parse(TRUMP_RSS_URL)
        
        if not feed.entries:
            send_to_feishu("⚠️ 未能获取到特朗普的最近推文")
            return None
        
        # 只取前3条或者全部（如果少于3条）
        entries = feed.entries[:min(count, len(feed.entries))]
        
        # 发送汇总消息
        send_to_feishu(f"📋 特朗普最近{len(entries)}条推文汇总：")
        
        # 逐条发送
        for entry in entries:
            send_to_feishu(format_tweet_message(entry))
            time.sleep(1)  # 短暂延迟避免消息太快
        
        # 返回最新推文的ID用于后续检查
        return feed.entries[0].id if feed.entries else None
    
    except Exception as e:
        send_to_feishu(f"❌ 获取最近推文时发生错误: {str(e)}")
        return None

def main():
    # 发送启动通知
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_to_feishu(f"🤖 特朗普推特监控机器人已启动\n启动时间：{start_time}\n监控频率：每5分钟检查一次")
    print("已发送启动通知")
    
    # 推送最近三条推文并获取最新的推文ID
    print("正在获取最近三条推文...")
    last_entry_id = push_recent_tweets(3)
    print(f"初始推文ID: {last_entry_id}")
    
    while True:
        try:
            # 获取 RSS 源内容
            feed = feedparser.parse(TRUMP_RSS_URL)
            
            if feed.entries:
                latest_entry = feed.entries[0]
                
                # 如果是新推文
                if last_entry_id != latest_entry.id:
                    print(f"发现新推文: {latest_entry.title}")
                    send_to_feishu(format_tweet_message(latest_entry))
                    last_entry_id = latest_entry.id
            
            # 每5分钟检查一次
            time.sleep(300)
            
        except Exception as e:
            error_msg = f"❌ 发生错误: {str(e)}"
            print(error_msg)
            send_to_feishu(error_msg)
            time.sleep(60)  # 发生错误时等待1分钟后重试

if __name__ == "__main__":
    main() 