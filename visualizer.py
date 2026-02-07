import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
import json


class DataVisualizer:
    """数据可视化器"""

    def __init__(self, output_dir='output'):
        """初始化可视化器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # 设置中文字体（如果需要）
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # 设置样式
        sns.set_style("whitegrid")

    def plot_sentiment_distribution(self, sentiment_data, filename='sentiment_distribution.png'):
        """绘制情感分布饼图

        Args:
            sentiment_data: 情感分布数据
            filename: 输出文件名
        """
        labels = ['Positive', 'Neutral', 'Negative']
        sizes = [
            sentiment_data['positive']['count'],
            sentiment_data['neutral']['count'],
            sentiment_data['negative']['count']
        ]
        colors = ['#4CAF50', '#FFC107', '#F44336']
        explode = (0.1, 0, 0)

        plt.figure(figsize=(10, 8))
        plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=90)
        plt.title('Sentiment Distribution', fontsize=16, fontweight='bold')
        plt.axis('equal')

        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"情感分布图已保存到 {output_path}")

    def plot_subreddit_distribution(self, subreddit_data, filename='subreddit_distribution.png'):
        """绘制subreddit分布条形图

        Args:
            subreddit_data: subreddit分布数据
            filename: 输出文件名
        """
        if not subreddit_data:
            print("没有subreddit数据可视化")
            return

        # 准备数据
        subreddits = list(subreddit_data.keys())
        counts = list(subreddit_data.values())

        plt.figure(figsize=(12, 8))
        bars = plt.barh(subreddits, counts, color='steelblue')

        # 添加数值标签
        for i, bar in enumerate(bars):
            plt.text(bar.get_width(), bar.get_y() + bar.get_height()/2,
                    f' {counts[i]}', va='center', fontsize=10)

        plt.xlabel('Number of Posts/Comments', fontsize=12)
        plt.ylabel('Subreddit', fontsize=12)
        plt.title('Distribution Across Subreddits', fontsize=16, fontweight='bold')
        plt.tight_layout()

        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Subreddit分布图已保存到 {output_path}")

    def plot_time_series(self, time_data, filename='time_series.png'):
        """绘制时间序列图

        Args:
            time_data: 时间分布数据
            filename: 输出文件名
        """
        posts_by_date = time_data.get('posts_by_date', {})
        comments_by_date = time_data.get('comments_by_date', {})

        if not posts_by_date and not comments_by_date:
            print("没有时间序列数据可视化")
            return

        # 准备数据
        dates = sorted(set(list(posts_by_date.keys()) + list(comments_by_date.keys())))
        dates = [pd.to_datetime(str(date)) for date in dates]

        posts_counts = [posts_by_date.get(str(date.date()), 0) for date in dates]
        comments_counts = [comments_by_date.get(str(date.date()), 0) for date in dates]

        plt.figure(figsize=(14, 8))

        plt.plot(dates, posts_counts, marker='o', label='Posts', linewidth=2, markersize=6)
        plt.plot(dates, comments_counts, marker='s', label='Comments', linewidth=2, markersize=6)

        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.title('Activity Over Time', fontsize=16, fontweight='bold')
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"时间序列图已保存到 {output_path}")

    def plot_topic_distribution(self, topic_data, filename='topic_distribution.png'):
        """绘制话题分布图

        Args:
            topic_data: 话题数据
            filename: 输出文件名
        """
        if not topic_data:
            print("没有话题数据可视化")
            return

        # 准备数据
        topics = list(topic_data.keys())
        mentions = [info['total_mentions'] for info in topic_data.values()]

        plt.figure(figsize=(12, 8))
        bars = plt.bar(topics, mentions, color='coral')

        # 添加数值标签
        for i, bar in enumerate(bars):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{mentions[i]}', ha='center', va='bottom', fontsize=10)

        plt.xlabel('Topic', fontsize=12)
        plt.ylabel('Total Mentions', fontsize=12)
        plt.title('Topic Distribution', fontsize=16, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"话题分布图已保存到 {output_path}")

    def plot_sentiment_by_subreddit(self, sentiment_by_subreddit, filename='sentiment_by_subreddit.png'):
        """绘制各subreddit的情感分布堆叠条形图

        Args:
            sentiment_by_subreddit: 各subreddit的情感数据
            filename: 输出文件名
        """
        if not sentiment_by_subreddit:
            print("没有按subreddit的情感数据可视化")
            return

        # 准备数据
        subreddits = list(sentiment_by_subreddit.keys())
        positive = [data['positive'] for data in sentiment_by_subreddit.values()]
        neutral = [data['neutral'] for data in sentiment_by_subreddit.values()]
        negative = [data['negative'] for data in sentiment_by_subreddit.values()]

        # 限制显示前10个
        if len(subreddits) > 10:
            subreddits = subreddits[:10]
            positive = positive[:10]
            neutral = neutral[:10]
            negative = negative[:10]

        plt.figure(figsize=(14, 8))

        x = range(len(subreddits))
        width = 0.6

        p1 = plt.bar(x, positive, width, label='Positive', color='#4CAF50')
        p2 = plt.bar(x, neutral, width, bottom=positive, label='Neutral', color='#FFC107')
        p3 = plt.bar(x, negative, width, bottom=[i+j for i, j in zip(positive, neutral)],
                    label='Negative', color='#F44336')

        plt.xlabel('Subreddit', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.title('Sentiment Distribution by Subreddit', fontsize=16, fontweight='bold')
        plt.xticks(x, subreddits, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()

        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Subreddit情感分布图已保存到 {output_path}")

    def export_to_csv(self, posts_data, comments_data, prefix='reddit_data'):
        """导出数据到CSV文件

        Args:
            posts_data: 帖子数据
            comments_data: 评论数据
            prefix: 文件名前缀
        """
        # 导出帖子
        if posts_data:
            posts_df = pd.DataFrame(posts_data)
            posts_path = os.path.join(self.output_dir, f'{prefix}_posts.csv')
            posts_df.to_csv(posts_path, index=False, encoding='utf-8-sig')
            print(f"帖子数据已导出到 {posts_path}")

        # 导出评论
        if comments_data:
            comments_df = pd.DataFrame(comments_data)
            comments_path = os.path.join(self.output_dir, f'{prefix}_comments.csv')
            comments_df.to_csv(comments_path, index=False, encoding='utf-8-sig')
            print(f"评论数据已导出到 {comments_path}")

    def generate_report(self, all_results):
        """生成完整的分析报告

        Args:
            all_results: 包含所有分析结果的字典
        """
        report_path = os.path.join(self.output_dir, 'analysis_report.json')

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        print(f"\n完整分析报告已保存到 {report_path}")

        # 生成简单的文本报告
        text_report_path = os.path.join(self.output_dir, 'analysis_report.txt')

        with open(text_report_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("Reddit Brand Product Analysis Report\n")
            f.write("="*80 + "\n\n")

            # 基础统计
            if 'basic_stats' in all_results:
                f.write("Basic Statistics:\n")
                f.write("-"*80 + "\n")
                stats = all_results['basic_stats']
                f.write(f"Total Volume: {stats.get('total_volume', 0)}\n")
                f.write(f"Post Count: {stats.get('post_count', 0)}\n")
                f.write(f"Comment Count: {stats.get('comment_count', 0)}\n")
                f.write(f"Unique Users: {stats.get('unique_users', 0)}\n")
                f.write(f"Unique Subreddits: {stats.get('unique_subreddits', 0)}\n\n")

            # 情感分布
            if 'sentiment_distribution' in all_results:
                f.write("Sentiment Distribution:\n")
                f.write("-"*80 + "\n")
                sentiment = all_results['sentiment_distribution']
                f.write(f"Positive: {sentiment['positive']['count']} ({sentiment['positive']['percentage']}%)\n")
                f.write(f"Neutral: {sentiment['neutral']['count']} ({sentiment['neutral']['percentage']}%)\n")
                f.write(f"Negative: {sentiment['negative']['count']} ({sentiment['negative']['percentage']}%)\n\n")

            # Subreddit分布
            if 'subreddit_distribution' in all_results:
                f.write("Top Subreddits:\n")
                f.write("-"*80 + "\n")
                for subreddit, count in list(all_results['subreddit_distribution'].items())[:10]:
                    f.write(f"r/{subreddit}: {count}\n")
                f.write("\n")

            # 话题分布
            if 'topics' in all_results:
                f.write("Top Topics:\n")
                f.write("-"*80 + "\n")
                for topic, info in list(all_results['topics'].items())[:10]:
                    f.write(f"{topic}: {info['total_mentions']} mentions\n")
                f.write("\n")

        print(f"文本报告已保存到 {text_report_path}")
