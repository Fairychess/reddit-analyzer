import pandas as pd
from collections import Counter
import json


class DataAnalyzer:
    """数据统计分析器"""

    def __init__(self, posts_data, comments_data):
        """初始化分析器

        Args:
            posts_data: 帖子数据列表
            comments_data: 评论数据列表
        """
        self.posts_df = pd.DataFrame(posts_data)
        self.comments_df = pd.DataFrame(comments_data)

        # 确保数据不为空
        if self.posts_df.empty:
            self.posts_df = pd.DataFrame(columns=['id', 'author', 'subreddit'])
        if self.comments_df.empty:
            self.comments_df = pd.DataFrame(columns=['id', 'author', 'subreddit'])

    def calculate_basic_stats(self):
        """计算基础统计指标"""
        stats = {
            'total_volume': len(self.posts_df) + len(self.comments_df),
            'post_count': len(self.posts_df),
            'comment_count': len(self.comments_df),
            'unique_users': self._count_unique_users(),
            'unique_subreddits': self._count_unique_subreddits()
        }

        return stats

    def _count_unique_users(self):
        """统计涉及的唯一用户数"""
        post_authors = set(self.posts_df['author'].unique()) if not self.posts_df.empty else set()
        comment_authors = set(self.comments_df['author'].unique()) if not self.comments_df.empty else set()

        all_authors = post_authors.union(comment_authors)

        # 移除删除的用户
        all_authors.discard('[deleted]')
        all_authors.discard('AutoModerator')

        return len(all_authors)

    def _count_unique_subreddits(self):
        """统计涉及的唯一subreddit数"""
        post_subreddits = set(self.posts_df['subreddit'].unique()) if not self.posts_df.empty else set()
        comment_subreddits = set(self.comments_df['subreddit'].unique()) if not self.comments_df.empty else set()

        all_subreddits = post_subreddits.union(comment_subreddits)

        return len(all_subreddits)

    def get_subreddit_distribution(self, top_n=10):
        """获取subreddit分布

        Args:
            top_n: 返回前N个最活跃的subreddit

        Returns:
            dict: subreddit名称和对应的数量
        """
        # 合并帖子和评论的subreddit
        all_subreddits = []

        if not self.posts_df.empty:
            all_subreddits.extend(self.posts_df['subreddit'].tolist())
        if not self.comments_df.empty:
            all_subreddits.extend(self.comments_df['subreddit'].tolist())

        subreddit_counts = Counter(all_subreddits)

        # 返回前N个
        top_subreddits = dict(subreddit_counts.most_common(top_n))

        return top_subreddits

    def get_time_distribution(self):
        """获取时间分布"""
        time_stats = {
            'posts_by_date': {},
            'comments_by_date': {}
        }

        # 帖子按日期统计
        if not self.posts_df.empty:
            self.posts_df['date'] = pd.to_datetime(self.posts_df['created_date']).dt.date
            posts_by_date = self.posts_df.groupby('date').size()
            time_stats['posts_by_date'] = posts_by_date.to_dict()

        # 评论按日期统计
        if not self.comments_df.empty:
            self.comments_df['date'] = pd.to_datetime(self.comments_df['created_date']).dt.date
            comments_by_date = self.comments_df.groupby('date').size()
            time_stats['comments_by_date'] = comments_by_date.to_dict()

        return time_stats

    def get_engagement_stats(self):
        """获取互动统计"""
        engagement = {
            'avg_post_score': 0,
            'avg_comment_score': 0,
            'total_post_score': 0,
            'total_comment_score': 0,
            'avg_comments_per_post': 0,
            'median_post_score': 0,
            'median_comment_score': 0
        }

        if not self.posts_df.empty:
            engagement['avg_post_score'] = float(self.posts_df['score'].mean())
            engagement['total_post_score'] = int(self.posts_df['score'].sum())
            engagement['median_post_score'] = float(self.posts_df['score'].median())
            engagement['avg_comments_per_post'] = float(self.posts_df['num_comments'].mean())

        if not self.comments_df.empty:
            engagement['avg_comment_score'] = float(self.comments_df['score'].mean())
            engagement['total_comment_score'] = int(self.comments_df['score'].sum())
            engagement['median_comment_score'] = float(self.comments_df['score'].median())

        return engagement

    def get_top_posts(self, top_n=10):
        """获取最热门的帖子

        Args:
            top_n: 返回前N个帖子

        Returns:
            list: 包含帖子信息的字典列表
        """
        if self.posts_df.empty:
            return []

        top_posts = self.posts_df.nlargest(top_n, 'score')[
            ['title', 'author', 'subreddit', 'score', 'num_comments', 'permalink', 'created_date']
        ].to_dict('records')

        return top_posts

    def get_top_users(self, top_n=10):
        """获取最活跃的用户

        Args:
            top_n: 返回前N个用户

        Returns:
            dict: 用户名和活动次数
        """
        all_authors = []

        if not self.posts_df.empty:
            all_authors.extend(self.posts_df['author'].tolist())
        if not self.comments_df.empty:
            all_authors.extend(self.comments_df['author'].tolist())

        # 移除删除的用户
        all_authors = [a for a in all_authors if a not in ['[deleted]', 'AutoModerator']]

        author_counts = Counter(all_authors)
        top_users = dict(author_counts.most_common(top_n))

        return top_users

    def export_summary(self, output_path='output/analysis_summary.json'):
        """导出分析摘要"""
        summary = {
            'basic_stats': self.calculate_basic_stats(),
            'subreddit_distribution': self.get_subreddit_distribution(),
            'time_distribution': self.get_time_distribution(),
            'engagement_stats': self.get_engagement_stats(),
            'top_posts': self.get_top_posts(),
            'top_users': self.get_top_users()
        }

        # 转换日期对象为字符串
        def convert_dates(obj):
            if isinstance(obj, dict):
                return {str(k): convert_dates(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_dates(item) for item in obj]
            else:
                return obj

        summary = convert_dates(summary)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n分析摘要已保存到 {output_path}")

        return summary
