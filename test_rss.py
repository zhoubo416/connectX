import requests
import urllib.request
import socket
import time
import feedparser
import sys

# 代理设置
USE_PROXY = True
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 7890

# 设置请求超时时间
TIMEOUT = 10

# RSS源列表
RSS_SOURCES = [
    "https://nitter.net/realDonaldTrump/rss",
    "https://nitter.net/realDonaldTrump45/rss",
    "https://nitter.net/JDVance/rss",
    "https://nitter.mehicano.me/realDonaldTrump/rss",
    "https://nitter.privacydev.net/realDonaldTrump/rss",
    "https://twiiit.com/realDonaldTrump/rss",
    "https://twitter116.com/realDonaldTrump/rss",
    "https://nitter.pussthecat.org/realDonaldTrump/rss",
    "https://nitter.1d4.us/realDonaldTrump/rss",
    "https://nitter.poast.org/realDonaldTrump/rss"
]

# 设置代理
proxies = {
    'http': f'http://{PROXY_HOST}:{PROXY_PORT}',
    'https': f'http://{PROXY_HOST}:{PROXY_PORT}'
}

# 为urllib设置代理
proxy_handler = urllib.request.ProxyHandler({
    'http': f'http://{PROXY_HOST}:{PROXY_PORT}',
    'https': f'http://{PROXY_HOST}:{PROXY_PORT}'
})
opener = urllib.request.build_opener(proxy_handler)
urllib.request.install_opener(opener)

def test_connection_requests(url):
    """使用requests测试连接"""
    try:
        if USE_PROXY:
            response = requests.get(url, proxies=proxies, timeout=TIMEOUT)
        else:
            response = requests.get(url, timeout=TIMEOUT)
        return response.status_code, response.elapsed.total_seconds(), len(response.content)
    except Exception as e:
        return f"错误: {str(e)}", None, None

def test_connection_urllib(url):
    """使用urllib测试连接"""
    try:
        req = urllib.request.Request(url)
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            content = response.read()
        elapsed = time.time() - start_time
        return response.status, elapsed, len(content)
    except Exception as e:
        return f"错误: {str(e)}", None, None

def test_feed_parser(url):
    """使用feedparser测试RSS解析"""
    try:
        if USE_PROXY:
            # 使用urllib获取内容
            req = urllib.request.Request(url)
            start_time = time.time()
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                content = response.read()
                
            # 使用feedparser解析
            feed = feedparser.parse(content)
            elapsed = time.time() - start_time
            
            if hasattr(feed, 'status') and feed.status != 200:
                return f"状态码: {feed.status}", elapsed, 0
                
            if feed.entries:
                return f"成功: {len(feed.entries)}条目", elapsed, len(feed.entries)
            else:
                return "成功但无条目", elapsed, 0
        else:
            # 直接使用feedparser
            start_time = time.time()
            feed = feedparser.parse(url, timeout=TIMEOUT)
            elapsed = time.time() - start_time
            
            if hasattr(feed, 'status') and feed.status != 200:
                return f"状态码: {feed.status}", elapsed, 0
                
            if feed.entries:
                return f"成功: {len(feed.entries)}条目", elapsed, len(feed.entries)
            else:
                return "成功但无条目", elapsed, 0
    except Exception as e:
        return f"错误: {str(e)}", None, None

def main():
    print(f"测试RSS源连接性 (代理: {'启用' if USE_PROXY else '禁用'}, 主机: {PROXY_HOST}, 端口: {PROXY_PORT})\n")
    
    print("=== 测试结果 ===")
    print(f"{'URL':<60} | {'Requests':<20} | {'urllib':<20} | {'FeedParser':<20}")
    print("-" * 125)
    
    success_count = 0
    for url in RSS_SOURCES:
        # 测试requests
        req_result, req_time, req_size = test_connection_requests(url)
        req_status = f"{req_result} ({req_time:.2f}s)" if isinstance(req_result, int) else req_result
        
        # 测试urllib
        urllib_result, urllib_time, urllib_size = test_connection_urllib(url)
        urllib_status = f"{urllib_result} ({urllib_time:.2f}s)" if isinstance(urllib_result, int) else urllib_result
        
        # 测试feedparser
        feed_result, feed_time, feed_size = test_feed_parser(url)
        feed_status = f"{feed_result} ({feed_time:.2f}s)" if feed_time else feed_result
        
        print(f"{url:<60} | {req_status:<20} | {urllib_status:<20} | {feed_status:<20}")
        
        # 计算成功数
        if (isinstance(req_result, int) and req_result == 200) or \
           (isinstance(urllib_result, int) and urllib_result == 200) or \
           (isinstance(feed_result, str) and feed_result.startswith("成功")):
            success_count += 1
    
    print("\n=== 测试总结 ===")
    print(f"成功连接: {success_count}/{len(RSS_SOURCES)} 个RSS源")
    print(f"代理状态: {'启用' if USE_PROXY else '禁用'}")
    
    if success_count == 0:
        print("\n❌ 所有RSS源连接失败！请检查代理设置或网络连接。")
        if USE_PROXY:
            print(f"  - 当前代理: http://{PROXY_HOST}:{PROXY_PORT}")
            print("  - 请确认代理服务器正在运行")
            print("  - 可以尝试关闭代理后再测试: 将USE_PROXY设置为False")
    else:
        print(f"\n✅ 有{success_count}个RSS源连接成功！")
        
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(0) 