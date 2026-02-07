from textblob import TextBlob
import pandas as pd
from tqdm import tqdm


class SentimentAnalyzer:
    """情感分析器"""

    def __init__(self, posts_data, comments_data):
        """初始化情感分析器

        Args:
            posts_data: 帖子数据列表
            comments_data: 评论数据列表
        """
        self.posts_data = posts_data
        self.comments_data = comments_data

        self.posts_with_sentiment = []
        self.comments_with_sentiment = []

    def _analyze_text_sentiment(self, text):
        """分析文本情感

        Args:
            text: 要分析的文本

        Returns:
            tuple: (polarity, subjectivity, sentiment_label)
                - polarity: 极性值 [-1, 1]，-1最负面，1最正面
                - subjectivity: 主观性 [0, 1]，0最客观，1最主观
                - sentiment_label: 情感标签 (positive/neutral/negative)
        """
        try:
            if not text or text.strip() == '':
                return 0.0, 0.0, 'neutral'

            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # 根据极性值分类
            if polarity > 0.1:
                sentiment_label = 'positive'
            elif polarity < -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'

            return polarity, subjectivity, sentiment_label

        except Exception as e:
            print(f"情感分析出错: {str(e)}")
            return 0.0, 0.0, 'neutral'

    def analyze_posts(self):
        """分析所有帖子的情感"""
        print("\n正在分析帖子情感...")

        for post in tqdm(self.posts_data, desc="帖子情感分析"):
            # 合并标题和正文进行分析
            combined_text = f"{post['title']} {post['selftext']}"

            polarity, subjectivity, sentiment = self._analyze_text_sentiment(combined_text)

            post_with_sentiment = post.copy()
            post_with_sentiment.update({
                'sentiment_polarity': polarity,
                'sentiment_subjectivity': subjectivity,
                'sentiment': sentiment
            })

            self.posts_with_sentiment.append(post_with_sentiment)

        return self.posts_with_sentiment

    def analyze_comments(self):
        """分析所有评论的情感"""
        print("\n正在分析评论情感...")

        for comment in tqdm(self.comments_data, desc="评论情感分析"):
            polarity, subjectivity, sentiment = self._analyze_text_sentiment(comment['body'])

            comment_with_sentiment = comment.copy()
            comment_with_sentiment.update({
                'sentiment_polarity': polarity,
                'sentiment_subjectivity': subjectivity,
                'sentiment': sentiment
            })

            self.comments_with_sentiment.append(comment_with_sentiment)

        return self.comments_with_sentiment

    def get_sentiment_distribution(self):
        """获取情感分布统计

        Returns:
            dict: 包含正面、中性、负面的数量和占比
        """
        all_sentiments = []

        # 收集所有情感标签
        for post in self.posts_with_sentiment:
            all_sentiments.append(post['sentiment'])

        for comment in self.comments_with_sentiment:
            all_sentiments.append(comment['sentiment'])

        total = len(all_sentiments)

        if total == 0:
            return {
                'positive': {'count': 0, 'percentage': 0},
                'neutral': {'count': 0, 'percentage': 0},
                'negative': {'count': 0, 'percentage': 0}
            }

        # 统计各类情感数量
        positive_count = all_sentiments.count('positive')
        neutral_count = all_sentiments.count('neutral')
        negative_count = all_sentiments.count('negative')

        distribution = {
            'positive': {
                'count': positive_count,
                'percentage': round(positive_count / total * 100, 2)
            },
            'neutral': {
                'count': neutral_count,
                'percentage': round(neutral_count / total * 100, 2)
            },
            'negative': {
                'count': negative_count,
                'percentage': round(negative_count / total * 100, 2)
            }
        }

        return distribution

    def get_sentiment_by_subreddit(self):
        """按subreddit统计情感分布"""
        df = pd.DataFrame(self.posts_with_sentiment + self.comments_with_sentiment)

        if df.empty:
            return {}

        # 按subreddit分组统计
        subreddit_sentiment = df.groupby(['subreddit', 'sentiment']).size().unstack(fill_value=0)

        # 转换为字典格式
        result = {}
        for subreddit in subreddit_sentiment.index:
            result[subreddit] = {
                'positive': int(subreddit_sentiment.loc[subreddit].get('positive', 0)),
                'neutral': int(subreddit_sentiment.loc[subreddit].get('neutral', 0)),
                'negative': int(subreddit_sentiment.loc[subreddit].get('negative', 0))
            }

        return result

    def get_sentiment_over_time(self):
        """获取情感随时间变化的趋势"""
        all_data = []

        for post in self.posts_with_sentiment:
            all_data.append({
                'date': post['created_date'].split()[0],
                'sentiment': post['sentiment']
            })

        for comment in self.comments_with_sentiment:
            all_data.append({
                'date': comment['created_date'].split()[0],
                'sentiment': comment['sentiment']
            })

        if not all_data:
            return {}

        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])

        # 按日期和情感分组
        time_sentiment = df.groupby([df['date'].dt.date, 'sentiment']).size().unstack(fill_value=0)

        # 转换为字典
        result = {}
        for date in time_sentiment.index:
            result[str(date)] = {
                'positive': int(time_sentiment.loc[date].get('positive', 0)),
                'neutral': int(time_sentiment.loc[date].get('neutral', 0)),
                'negative': int(time_sentiment.loc[date].get('negative', 0))
            }

        return result

    def get_most_positive_and_negative(self, top_n=5):
        """获取最正面和最负面的内容

        Args:
            top_n: 返回前N条

        Returns:
            dict: 包含最正面和最负面的帖子和评论
        """
        result = {
            'most_positive_posts': [],
            'most_negative_posts': [],
            'most_positive_comments': [],
            'most_negative_comments': []
        }

        # 处理帖子
        if self.posts_with_sentiment:
            posts_df = pd.DataFrame(self.posts_with_sentiment)
            posts_df = posts_df.sort_values('sentiment_polarity', ascending=False)

            # 最正面的帖子
            result['most_positive_posts'] = posts_df.head(top_n)[
                ['title', 'author', 'subreddit', 'sentiment_polarity', 'permalink']
            ].to_dict('records')

            # 最负面的帖子
            result['most_negative_posts'] = posts_df.tail(top_n)[
                ['title', 'author', 'subreddit', 'sentiment_polarity', 'permalink']
            ].to_dict('records')

        # 处理评论
        if self.comments_with_sentiment:
            comments_df = pd.DataFrame(self.comments_with_sentiment)
            comments_df = comments_df.sort_values('sentiment_polarity', ascending=False)

            # 最正面的评论
            result['most_positive_comments'] = comments_df.head(top_n)[
                ['body', 'author', 'subreddit', 'sentiment_polarity', 'permalink']
            ].to_dict('records')

            # 最负面的评论
            result['most_negative_comments'] = comments_df.tail(top_n)[
                ['body', 'author', 'subreddit', 'sentiment_polarity', 'permalink']
            ].to_dict('records')

        return result

    def get_analyzed_data(self):
        """获取带情感分析的数据"""
        return self.posts_with_sentiment, self.comments_with_sentiment
