import os
import time
import logging
from datetime import datetime
import json
import requests
from dotenv import load_dotenv
import feedparser
import urllib.request
import socks
import socket

# 设置日志记录
logging.basicConfig(
    filename='trump_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 加载环境变量
load_dotenv()

# 飞书webhook URL
FEISHU_WEBHOOK_URL = os.getenv('FEISHU_WEBHOOK_URL', 'https://open.feishu.cn/open-apis/bot/v2/hook/51fac4c6-a9ec-4d1e-9a8c-cad6a0be2b63')

# 代理设置
USE_PROXY = True  # 是否使用代理
PROXY_TYPE = 'HTTP'  # 代理类型: 'HTTP', 'SOCKS4', 'SOCKS5'
PROXY_HOST = '127.0.0.1'  # 代理主机
PROXY_PORT = 7890  # 代理端口 (Clash默认端口)

# RSS 源地址 - 根据测试调整优先级
TRUMP_RSS_URL = "https://nitter.privacydev.net/realDonaldTrump/rss"  # 测试有20条内容的源优先
# 备用RSS源
BACKUP_RSS_URLS = [
    "https://nitter.net/realDonaldTrump/rss",  # 连接成功但无内容
    "https://nitter.net/JDVance/rss",  # 副总统候选人账号
    "https://nitter.net/realDonaldTrump45/rss",  # 可能的备用账号
    "https://nitter.mehicano.me/realDonaldTrump/rss",
    "https://twitter116.com/realDonaldTrump/rss",
    "https://nitter.pussthecat.org/realDonaldTrump/rss",
    "https://nitter.1d4.us/realDonaldTrump/rss",
    "https://nitter.poast.org/realDonaldTrump/rss",  # 403
    "https://twiiit.com/realDonaldTrump/rss",  # 403
    "https://x.com/realDonaldTrump/rss"  # 直接尝试X.com，虽然可能不提供RSS
]

# 设置代理
def setup_proxy():
    if USE_PROXY:
        logging.info(f"设置{PROXY_TYPE}代理: {PROXY_HOST}:{PROXY_PORT}")
        
        # 为requests设置代理
        global proxies
        if PROXY_TYPE.upper() in ['HTTP', 'HTTPS']:
            proxies = {
                'http': f'http://{PROXY_HOST}:{PROXY_PORT}',
                'https': f'http://{PROXY_HOST}:{PROXY_PORT}'
            }
        else:  # SOCKS代理
            proxies = {
                'http': f'socks5://{PROXY_HOST}:{PROXY_PORT}',
                'https': f'socks5://{PROXY_HOST}:{PROXY_PORT}'
            }
        
        # 为urllib和feedparser设置代理
        if PROXY_TYPE.upper() == 'HTTP':
            proxy_handler = urllib.request.ProxyHandler({
                'http': f'http://{PROXY_HOST}:{PROXY_PORT}',
                'https': f'http://{PROXY_HOST}:{PROXY_PORT}'
            })
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
        elif PROXY_TYPE.upper() in ['SOCKS4', 'SOCKS5']:
            socks_type = socks.SOCKS5 if PROXY_TYPE.upper() == 'SOCKS5' else socks.SOCKS4
            socks.set_default_proxy(socks_type, PROXY_HOST, PROXY_PORT)
            socket.socket = socks.socksocket
        
        logging.info("代理设置完成")

def send_to_feishu(text):
    """发送消息到飞书"""
    data = {
        "msg_type": "text",
        "content": {
            "text": text
        }
    }
    try:
        # 使用代理发送请求
        if USE_PROXY:
            response = requests.post(FEISHU_WEBHOOK_URL, json=data, proxies=proxies)
        else:
            response = requests.post(FEISHU_WEBHOOK_URL, json=data)
            
        if response.status_code != 200:
            logging.error(f"发送消息失败: {response.text}")
            print(f"发送消息失败: {response.text}")
            return False
        else:
            logging.info("消息发送成功")
            print("消息发送成功")
            return True
    except Exception as e:
        logging.error(f"发送消息异常: {str(e)}")
        print(f"发送消息异常: {str(e)}")
        return False

def format_tweet_message(entry):
    """格式化推文消息"""
    return f"""特朗普发布推文：
时间：{entry.published}
内容：{entry.title}
链接：{entry.link}"""

def parse_rss_with_proxy(url):
    """使用代理解析RSS"""
    try:
        logging.info(f"尝试通过代理获取RSS: {url}")
        if USE_PROXY:
            # 使用urllib创建带代理的请求
            req = urllib.request.Request(url)
            # 设置较短的超时时间，避免长时间阻塞
            with urllib.request.urlopen(req, timeout=15) as response:
                rss_content = response.read()
            # 使用内容手动解析
            return feedparser.parse(rss_content)
        else:
            # 不使用代理时直接调用，也设置超时
            return feedparser.parse(url, timeout=15)
    except Exception as e:
        logging.error(f"代理获取RSS异常 ({url}): {str(e)}")
        return feedparser.FeedParserDict()

def push_recent_tweets(count=3):
    """推送最近的推文"""
    logging.info(f"尝试获取最近{count}条推文")
    
    # 尝试主RSS源
    feed = parse_rss_with_proxy(TRUMP_RSS_URL)
    
    # 检查RSS源是否有效
    if not feed.entries:
        logging.warning("主RSS源未返回任何条目")
        
        # 尝试备用RSS源
        for backup_url in BACKUP_RSS_URLS:
            logging.info(f"尝试备用RSS源: {backup_url}")
            feed = parse_rss_with_proxy(backup_url)
            if feed.entries:
                logging.info(f"备用源 {backup_url} 成功获取到 {len(feed.entries)} 条推文")
                break
        
        if not feed.entries:
            logging.error("所有RSS源均未返回数据")
            send_to_feishu("⚠️ 未能获取到特朗普的最近推文，所有RSS源均无返回")
            return None
    else:
        logging.info(f"成功获取到 {len(feed.entries)} 条推文")
    
    # 只取前count条或者全部（如果少于count条）
    entries = feed.entries[:min(count, len(feed.entries))]
    
    # 发送汇总消息
    send_to_feishu(f"📋 特朗普最近{len(entries)}条推文汇总：")
    
    # 逐条发送
    for entry in entries:
        send_to_feishu(format_tweet_message(entry))
        logging.info(f"推送推文: {entry.id}")
        time.sleep(1)  # 短暂延迟避免消息太快
    
    # 返回最新推文的ID用于后续检查
    if feed.entries:
        logging.info(f"最新推文ID: {feed.entries[0].id}")
        return feed.entries[0].id
    return None

def main():
    # 设置代理
    setup_proxy()
    
    # 发送启动通知
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    proxy_info = f"代理设置: {'启用' if USE_PROXY else '禁用'}"
    startup_msg = f"🤖 特朗普推特监控机器人已启动\n启动时间：{start_time}\n{proxy_info}\n监控频率：每5分钟检查一次"
    logging.info(startup_msg)
    send_to_feishu(startup_msg)
    print("已发送启动通知")
    
    # 推送最近三条推文并获取最新的推文ID
    logging.info("正在获取最近三条推文...")
    print("正在获取最近三条推文...")
    last_entry_id = push_recent_tweets(3)
    logging.info(f"初始推文ID: {last_entry_id}")
    print(f"初始推文ID: {last_entry_id}")
    
    while True:
        try:
            logging.info("检查新推文...")
            # 获取 RSS 源内容
            feed = parse_rss_with_proxy(TRUMP_RSS_URL)
            
            if feed.entries:
                latest_entry = feed.entries[0]
                
                # 如果是新推文
                if last_entry_id != latest_entry.id:
                    new_tweet_msg = f"发现新推文: {latest_entry.title}"
                    logging.info(new_tweet_msg)
                    print(new_tweet_msg)
                    send_to_feishu(format_tweet_message(latest_entry))
                    last_entry_id = latest_entry.id
                    logging.info(f"更新最新推文ID: {last_entry_id}")
                else:
                    logging.info("没有新推文")
            else:
                logging.warning("RSS源未返回任何条目")
                
                # 尝试备用RSS源
                success = False
                for backup_url in BACKUP_RSS_URLS:
                    feed = parse_rss_with_proxy(backup_url)
                    if feed.entries:
                        if last_entry_id != feed.entries[0].id:
                            new_tweet_msg = f"发现新推文(来自备用源): {feed.entries[0].title}"
                            logging.info(new_tweet_msg)
                            print(new_tweet_msg)
                            send_to_feishu(format_tweet_message(feed.entries[0]))
                            last_entry_id = feed.entries[0].id
                        success = True
                        break
                
                if not success:
                    # 每24小时发送一次状态报告
                    current_hour = datetime.now().hour
                    if current_hour == 9:  # 每天上午9点
                        status_msg = f"📊 监控状态报告: 所有RSS源目前未返回任何推文，但监控服务正常运行中"
                        logging.info(status_msg)
                        send_to_feishu(status_msg)
            
            # 每5分钟检查一次
            logging.info("休眠5分钟...")
            time.sleep(300)
            
        except Exception as e:
            error_msg = f"❌ 发生错误: {str(e)}"
            logging.error(error_msg)
            print(error_msg)
            send_to_feishu(error_msg)
            time.sleep(60)  # 发生错误时等待1分钟后重试

if __name__ == "__main__":
    main()