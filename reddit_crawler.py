import requests
import json
from datetime import datetime
from tqdm import tqdm
import time
import os


class RedditCrawler:
    """Reddit数据爬取器 - 使用JSON API直接爬取"""

    def __init__(self, config_path='config.json'):
        """初始化Reddit爬虫

        Args:
            config_path: 配置文件路径
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 搜索参数
        self.brand = self.config['search']['brand']
        self.product = self.config['search']['product']
        self.start_date = datetime.strptime(self.config['search']['start_date'], '%d/%m/%Y')
        self.end_date = datetime.strptime(self.config['search']['end_date'], '%d/%m/%Y')
        self.subreddits = self.config['search']['subreddits']
        self.limit = self.config['search']['limit']

        # 数据存储
        self.posts_data = []
        self.comments_data = []

        # 设置请求头，模拟浏览器
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # 请求间隔（秒）
        self.request_delay = 2

    def _is_in_date_range(self, timestamp):
        """检查时间戳是否在指定范围内"""
        post_date = datetime.fromtimestamp(timestamp)
        return self.start_date <= post_date <= self.end_date

    def _make_request(self, url, params=None):
        """发起HTTP请求并返回JSON数据

        Args:
            url: 请求URL
            params: 请求参数

        Returns:
            dict: JSON响应数据
        """
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            time.sleep(self.request_delay)  # 避免请求过快
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {str(e)}")
            return None

    def search_posts(self):
        """搜索相关帖子"""
        search_query = f"{self.brand} {self.product}"
        print(f"\n搜索查询: {search_query}")
        print(f"时间范围: {self.start_date.strftime('%Y-%m-%d')} 到 {self.end_date.strftime('%Y-%m-%d')}")

        for subreddit_name in self.subreddits:
            print(f"\n正在搜索 r/{subreddit_name}...")

            try:
                self._search_subreddit(subreddit_name, search_query)
            except Exception as e:
                print(f"搜索 r/{subreddit_name} 时出错: {str(e)}")
                continue

        print(f"\n共找到 {len(self.posts_data)} 个相关帖子")
        print(f"共收集 {len(self.comments_data)} 条评论")

        return self.posts_data, self.comments_data

    def _search_subreddit(self, subreddit_name, query):
        """在指定subreddit中搜索

        Args:
            subreddit_name: subreddit名称
            query: 搜索关键词
        """
        # 构建搜索URL
        if subreddit_name.lower() == 'all':
            base_url = 'https://www.reddit.com/search.json'
        else:
            base_url = f'https://www.reddit.com/r/{subreddit_name}/search.json'

        # 搜索参数
        params = {
            'q': query,
            'sort': 'new',
            'limit': 100,  # 每次请求最多100条
            'restrict_sr': 'on' if subreddit_name.lower() != 'all' else 'off'
        }

        collected_count = 0
        after = None

        with tqdm(total=self.limit, desc=f"搜索 r/{subreddit_name}") as pbar:
            while collected_count < self.limit:
                # 添加分页参数
                if after:
                    params['after'] = after

                # 发起请求
                data = self._make_request(base_url, params)

                if not data or 'data' not in data:
                    print(f"\n未能获取数据，可能是网络问题或subreddit不存在")
                    break

                posts = data['data'].get('children', [])

                if not posts:
                    print(f"\n没有找到更多帖子")
                    break

                # 处理每个帖子
                for post_data in posts:
                    if collected_count >= self.limit:
                        break

                    post = post_data['data']

                    # 检查时间范围
                    if not self._is_in_date_range(post['created_utc']):
                        continue

                    # 提取帖子信息
                    post_info = {
                        'id': post['id'],
                        'title': post.get('title', ''),
                        'selftext': post.get('selftext', ''),
                        'author': post.get('author', '[deleted]'),
                        'subreddit': post.get('subreddit', ''),
                        'created_utc': post['created_utc'],
                        'created_date': datetime.fromtimestamp(post['created_utc']).strftime('%Y-%m-%d %H:%M:%S'),
                        'score': post.get('score', 0),
                        'upvote_ratio': post.get('upvote_ratio', 0),
                        'num_comments': post.get('num_comments', 0),
                        'url': post.get('url', ''),
                        'permalink': f"https://reddit.com{post.get('permalink', '')}"
                    }

                    self.posts_data.append(post_info)
                    collected_count += 1
                    pbar.update(1)

                    # 获取评论（限制数量以提高速度）
                    if post['num_comments'] > 0:
                        self._fetch_comments(post['permalink'], post['id'], post.get('subreddit', ''))

                # 获取下一页的标记
                after = data['data'].get('after')

                if not after:
                    print(f"\n已到达最后一页")
                    break

    def _fetch_comments(self, permalink, post_id, subreddit):
        """获取帖子的评论

        Args:
            permalink: 帖子的永久链接
            post_id: 帖子ID
            subreddit: 所属subreddit
        """
        try:
            # 构建评论URL
            comments_url = f"https://www.reddit.com{permalink}.json"

            # 获取评论数据
            data = self._make_request(comments_url)

            if not data or len(data) < 2:
                return

            # 评论数据在第二个元素中
            comments_listing = data[1]['data']['children']

            # 递归提取所有评论
            self._extract_comments_recursive(comments_listing, post_id, subreddit)

        except Exception as e:
            print(f"\n获取评论时出错: {str(e)}")

    def _extract_comments_recursive(self, comments_list, post_id, subreddit):
        """递归提取评论及其回复

        Args:
            comments_list: 评论列表
            post_id: 帖子ID
            subreddit: 所属subreddit
        """
        for comment_data in comments_list:
            if comment_data['kind'] != 't1':  # t1是评论类型
                continue

            comment = comment_data['data']

            # 提取评论信息
            if 'body' in comment and comment['body']:
                comment_info = {
                    'id': comment['id'],
                    'post_id': post_id,
                    'body': comment.get('body', ''),
                    'author': comment.get('author', '[deleted]'),
                    'subreddit': subreddit,
                    'created_utc': comment['created_utc'],
                    'created_date': datetime.fromtimestamp(comment['created_utc']).strftime('%Y-%m-%d %H:%M:%S'),
                    'score': comment.get('score', 0),
                    'permalink': f"https://reddit.com{comment.get('permalink', '')}"
                }

                # 检查时间范围
                if self._is_in_date_range(comment['created_utc']):
                    self.comments_data.append(comment_info)

            # 处理子评论
            if 'replies' in comment and comment['replies']:
                if isinstance(comment['replies'], dict) and 'data' in comment['replies']:
                    children = comment['replies']['data'].get('children', [])
                    self._extract_comments_recursive(children, post_id, subreddit)

    def save_raw_data(self, output_dir='output'):
        """保存原始数据到JSON文件"""
        os.makedirs(output_dir, exist_ok=True)

        # 保存帖子数据
        with open(f'{output_dir}/posts_raw.json', 'w', encoding='utf-8') as f:
            json.dump(self.posts_data, f, ensure_ascii=False, indent=2)

        # 保存评论数据
        with open(f'{output_dir}/comments_raw.json', 'w', encoding='utf-8') as f:
            json.dump(self.comments_data, f, ensure_ascii=False, indent=2)

        print(f"\n原始数据已保存到 {output_dir}/ 目录")

    def get_data(self):
        """获取收集的数据"""
        return self.posts_data, self.comments_data
