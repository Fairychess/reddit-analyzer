import re
from collections import Counter
from wordcloud import WordCloud
import pandas as pd


class TopicAnalyzer:
    """话题分析器"""

    def __init__(self, posts_with_sentiment, comments_with_sentiment):
        """初始化话题分析器

        Args:
            posts_with_sentiment: 带情感标签的帖子数据
            comments_with_sentiment: 带情感标签的评论数据
        """
        self.posts_data = posts_with_sentiment
        self.comments_data = comments_with_sentiment

        # 常见停用词
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
            'who', 'when', 'where', 'why', 'how', 'my', 'your', 'his', 'her', 'its',
            'our', 'their', 'me', 'him', 'them', 'us', 'just', 'not', 've', 're',
            'll', 's', 't', 'm', 'd', 'like', 'get', 'got', 'one', 'also', 'really',
            'even', 'still', 'much', 'more', 'very', 'so', 'too', 'out', 'up', 'down',
            'https', 'http', 'com', 'www'
        }

    def _extract_text_from_data(self):
        """从帖子和评论中提取所有文本"""
        all_text = []

        # 提取帖子文本
        for post in self.posts_data:
            all_text.append(post['title'])
            if post.get('selftext'):
                all_text.append(post['selftext'])

        # 提取评论文本
        for comment in self.comments_data:
            if comment.get('body'):
                all_text.append(comment['body'])

        return ' '.join(all_text)

    def _clean_text(self, text):
        """清理文本

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        # 转小写
        text = text.lower()

        # 移除URL
        text = re.sub(r'http\S+|www\S+', '', text)

        # 移除特殊字符，只保留字母、数字和空格
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)

        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def extract_keywords(self, top_n=50):
        """提取关键词

        Args:
            top_n: 返回前N个关键词

        Returns:
            dict: 关键词和出现次数
        """
        all_text = self._extract_text_from_data()
        cleaned_text = self._clean_text(all_text)

        # 分词
        words = cleaned_text.split()

        # 过滤停用词和短词
        filtered_words = [
            word for word in words
            if word not in self.stop_words and len(word) > 2
        ]

        # 统计词频
        word_counts = Counter(filtered_words)

        # 返回前N个
        top_keywords = dict(word_counts.most_common(top_n))

        return top_keywords

    def generate_wordcloud(self, output_path='output/wordcloud.png'):
        """生成词云图

        Args:
            output_path: 输出文件路径
        """
        all_text = self._extract_text_from_data()
        cleaned_text = self._clean_text(all_text)

        if not cleaned_text:
            print("没有足够的文本数据生成词云")
            return

        try:
            # 生成词云
            wordcloud = WordCloud(
                width=1600,
                height=800,
                background_color='white',
                stopwords=self.stop_words,
                max_words=100,
                relative_scaling=0.5,
                min_font_size=10
            ).generate(cleaned_text)

            # 保存词云图
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            wordcloud.to_file(output_path)

            print(f"\n词云图已保存到 {output_path}")

        except Exception as e:
            print(f"生成词云图时出错: {str(e)}")

    def extract_topic_clusters(self, top_n=10):
        """提取话题聚类

        根据关键词共现关系进行简单的话题聚类

        Args:
            top_n: 返回前N个话题

        Returns:
            dict: 话题及相关关键词
        """
        # 获取高频关键词
        keywords = self.extract_keywords(top_n=100)

        if not keywords:
            return {}

        # 简单的基于关键词的话题分类
        topic_patterns = {
            'performance': ['performance', 'speed', 'fast', 'slow', 'lag', 'fps', 'battery', 'processor', 'chip'],
            'design': ['design', 'look', 'color', 'screen', 'display', 'size', 'weight', 'build', 'camera'],
            'price': ['price', 'cost', 'expensive', 'cheap', 'worth', 'value', 'money', 'deal', 'sale'],
            'features': ['feature', 'function', 'support', 'software', 'update', 'version', 'system', 'app'],
            'quality': ['quality', 'issue', 'problem', 'defect', 'break', 'damage', 'fix', 'repair', 'warranty'],
            'comparison': ['better', 'worse', 'compare', 'difference', 'versus', 'vs', 'alternative', 'similar'],
            'user_experience': ['use', 'experience', 'love', 'hate', 'like', 'dislike', 'recommend', 'buy', 'purchased']
        }

        # 统计每个话题的相关词汇
        topic_stats = {}
        for topic, patterns in topic_patterns.items():
            related_words = {}
            for word, count in keywords.items():
                if word in patterns:
                    related_words[word] = count

            if related_words:
                topic_stats[topic] = {
                    'keywords': related_words,
                    'total_mentions': sum(related_words.values())
                }

        # 按提及次数排序
        sorted_topics = dict(sorted(
            topic_stats.items(),
            key=lambda x: x[1]['total_mentions'],
            reverse=True
        )[:top_n])

        return sorted_topics

    def get_topic_sentiment_distribution(self):
        """获取话题的情感分布"""
        topics = self.extract_topic_clusters()

        topic_sentiment = {}

        for topic, info in topics.items():
            keywords = list(info['keywords'].keys())

            sentiment_counts = {
                'positive': 0,
                'neutral': 0,
                'negative': 0
            }

            # 统计包含该话题关键词的内容的情感
            for post in self.posts_data:
                text = f"{post['title']} {post.get('selftext', '')}".lower()
                if any(keyword in text for keyword in keywords):
                    sentiment_counts[post['sentiment']] += 1

            for comment in self.comments_data:
                text = comment.get('body', '').lower()
                if any(keyword in text for keyword in keywords):
                    sentiment_counts[comment['sentiment']] += 1

            topic_sentiment[topic] = sentiment_counts

        return topic_sentiment

    def get_hashtags_and_mentions(self):
        """提取hashtags和@mentions"""
        hashtags = []
        mentions = []

        for post in self.posts_data:
            text = f"{post['title']} {post.get('selftext', '')}"

            # 提取hashtags
            hashtags.extend(re.findall(r'#(\w+)', text))

            # 提取mentions
            mentions.extend(re.findall(r'@(\w+)', text))

        for comment in self.comments_data:
            text = comment.get('body', '')

            # 提取hashtags
            hashtags.extend(re.findall(r'#(\w+)', text))

            # 提取mentions
            mentions.extend(re.findall(r'@(\w+)', text))

        return {
            'top_hashtags': dict(Counter(hashtags).most_common(20)),
            'top_mentions': dict(Counter(mentions).most_common(20))
        }

    def analyze_discussion_threads(self):
        """分析讨论线程

        找出评论最多的帖子和讨论最热烈的话题
        """
        if not self.posts_data:
            return {}

        posts_df = pd.DataFrame(self.posts_data)

        # 最多评论的帖子
        top_discussed = posts_df.nlargest(10, 'num_comments')[
            ['title', 'author', 'subreddit', 'num_comments', 'score', 'sentiment', 'permalink']
        ].to_dict('records')

        return {
            'most_discussed_posts': top_discussed
        }
