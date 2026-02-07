import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
from reddit_crawler import RedditCrawler
from data_analyzer import DataAnalyzer
from sentiment_analyzer import SentimentAnalyzer
from topic_analyzer import TopicAnalyzer
from visualizer import DataVisualizer

# 设置页面配置
st.set_page_config(
    page_title="Reddit品牌产品分析器",
    page_icon="📊",
    layout="wide"
)

# 标题
st.title("📊 Reddit品牌产品分析器")
st.markdown("### 无需API凭证，一键分析Reddit舆情")

# 侧边栏 - 配置参数
st.sidebar.header("⚙️ 配置参数")

# 品牌和产品
brand = st.sidebar.text_input("品牌名称", value="Apple", help="例如: Apple, Samsung, Sony")
product = st.sidebar.text_input("产品名称", value="iPhone 15", help="例如: iPhone 15, Galaxy S24")

# 时间范围
st.sidebar.subheader("时间范围")
col1, col2 = st.sidebar.columns(2)

# 默认最近3个月
default_end = datetime.now()
default_start = default_end - timedelta(days=90)

start_date = col1.date_input("开始日期", value=default_start)
end_date = col2.date_input("结束日期", value=default_end)

# Subreddit选择
st.sidebar.subheader("Subreddit")
subreddit_option = st.sidebar.radio(
    "选择方式",
    ["推荐社区", "自定义"]
)

if subreddit_option == "推荐社区":
    # 预设的常用subreddit组合
    preset = st.sidebar.selectbox(
        "选择预设",
        [
            "科技产品 (technology, gadgets)",
            "手机 (smartphone, android, iphone)",
            "游戏 (gaming, PS5, xbox)",
            "笔记本电脑 (laptops, thinkpad, macbook)",
            "所有社区 (all)"
        ]
    )

    preset_map = {
        "科技产品 (technology, gadgets)": ["technology", "gadgets", "tech"],
        "手机 (smartphone, android, iphone)": ["smartphone", "android", "iphone", "samsung"],
        "游戏 (gaming, PS5, xbox)": ["gaming", "PS5", "xbox", "playstation"],
        "笔记本电脑 (laptops, thinkpad, macbook)": ["laptops", "thinkpad", "macbook", "dell"],
        "所有社区 (all)": ["all"]
    }

    subreddits = preset_map[preset]
else:
    subreddit_input = st.sidebar.text_input(
        "输入Subreddit",
        value="technology, apple, iphone",
        help="用逗号分隔多个subreddit"
    )
    subreddits = [s.strip() for s in subreddit_input.split(",") if s.strip()]

# 爬取数量限制
limit = st.sidebar.slider("每个Subreddit爬取数量", min_value=50, max_value=500, value=200, step=50)

# 开始分析按钮
st.sidebar.markdown("---")
start_analysis = st.sidebar.button("🚀 开始分析", type="primary", use_container_width=True)

# 主界面
if not start_analysis:
    # 显示说明
    st.info("👈 请在左侧配置参数，然后点击「开始分析」按钮")

    st.markdown("### 功能特性")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📈 数据统计")
        st.markdown("""
        - 总声量统计
        - 帖子和评论数量
        - 涉及用户数
        - Subreddit分布
        """)

    with col2:
        st.markdown("#### 😊 情感分析")
        st.markdown("""
        - 正面/中性/负面占比
        - 情感趋势分析
        - 各社区情感对比
        - 最正/负面内容
        """)

    with col3:
        st.markdown("#### 🔍 话题分析")
        st.markdown("""
        - 关键词提取
        - 话题聚类
        - 词云生成
        - 热门讨论
        """)

    st.markdown("---")
    st.markdown("### 使用提示")
    st.markdown("""
    1. **时间范围**: 建议选择1-3个月，范围太大会影响速度
    2. **Subreddit**: 可以选择特定社区获得更精准的结果
    3. **爬取数量**: 建议设置100-300，数量越大时间越长
    4. **分析时间**: 根据数据量，通常需要3-10分钟
    """)

else:
    # 开始分析
    try:
        # 创建配置
        config = {
            "search": {
                "brand": brand,
                "product": product,
                "start_date": start_date.strftime("%d/%m/%Y"),
                "end_date": end_date.strftime("%d/%m/%Y"),
                "subreddits": subreddits,
                "limit": limit
            }
        }

        # 保存配置
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # 显示配置信息
        st.success(f"正在分析: {brand} {product}")
        st.info(f"时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        st.info(f"搜索社区: {', '.join(subreddits)}")

        # 进度显示
        progress_bar = st.progress(0)
        status_text = st.empty()

        # 步骤1: 爬取数据
        status_text.text("步骤 1/6: 正在爬取Reddit数据...")
        progress_bar.progress(10)

        crawler = RedditCrawler('config.json')
        posts_data, comments_data = crawler.search_posts()

        if not posts_data and not comments_data:
            st.error("❌ 未找到相关数据，请尝试：")
            st.markdown("""
            - 扩大时间范围
            - 使用更通用的关键词
            - 选择更多的Subreddit
            """)
            st.stop()

        progress_bar.progress(25)

        # 步骤2: 数据统计
        status_text.text("步骤 2/6: 正在进行数据统计...")
        analyzer = DataAnalyzer(posts_data, comments_data)
        basic_stats = analyzer.calculate_basic_stats()
        subreddit_distribution = analyzer.get_subreddit_distribution()
        time_distribution = analyzer.get_time_distribution()
        engagement_stats = analyzer.get_engagement_stats()
        top_posts = analyzer.get_top_posts()

        progress_bar.progress(40)

        # 步骤3: 情感分析
        status_text.text("步骤 3/6: 正在进行情感分析...")
        sentiment_analyzer = SentimentAnalyzer(posts_data, comments_data)
        posts_with_sentiment = sentiment_analyzer.analyze_posts()
        comments_with_sentiment = sentiment_analyzer.analyze_comments()
        sentiment_distribution = sentiment_analyzer.get_sentiment_distribution()
        sentiment_by_subreddit = sentiment_analyzer.get_sentiment_by_subreddit()

        progress_bar.progress(60)

        # 步骤4: 话题分析
        status_text.text("步骤 4/6: 正在进行话题分析...")
        topic_analyzer = TopicAnalyzer(posts_with_sentiment, comments_with_sentiment)
        keywords = topic_analyzer.extract_keywords(top_n=30)
        topics = topic_analyzer.extract_topic_clusters()

        progress_bar.progress(75)

        # 步骤5: 生成可视化
        status_text.text("步骤 5/6: 正在生成可视化图表...")
        visualizer = DataVisualizer(output_dir='output')
        visualizer.plot_sentiment_distribution(sentiment_distribution)
        visualizer.plot_subreddit_distribution(subreddit_distribution)
        visualizer.plot_time_series(time_distribution)
        if topics:
            visualizer.plot_topic_distribution(topics)
        if sentiment_by_subreddit:
            visualizer.plot_sentiment_by_subreddit(sentiment_by_subreddit)
        topic_analyzer.generate_wordcloud()

        progress_bar.progress(90)

        # 步骤6: 导出数据
        status_text.text("步骤 6/6: 正在导出结果...")
        visualizer.export_to_csv(posts_with_sentiment, comments_with_sentiment)

        progress_bar.progress(100)
        status_text.text("✅ 分析完成！")

        # 显示结果
        st.success("🎉 分析完成！")

        # Tab布局
        tab1, tab2, tab3, tab4 = st.tabs(["📊 基础统计", "😊 情感分析", "🔍 话题分析", "📥 数据下载"])

        with tab1:
            st.header("基础统计")

            # 关键指标
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("总声量", f"{basic_stats['total_volume']:,}")
            col2.metric("帖子数", f"{basic_stats['post_count']:,}")
            col3.metric("评论数", f"{basic_stats['comment_count']:,}")
            col4.metric("涉及用户", f"{basic_stats['unique_users']:,}")

            st.markdown("---")

            # 图表
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Subreddit分布")
                if os.path.exists('output/subreddit_distribution.png'):
                    st.image('output/subreddit_distribution.png')

            with col2:
                st.subheader("时间序列趋势")
                if os.path.exists('output/time_series.png'):
                    st.image('output/time_series.png')

            # 热门帖子
            st.subheader("🔥 热门帖子 Top 10")
            if top_posts:
                for i, post in enumerate(top_posts[:10], 1):
                    with st.expander(f"{i}. {post['title'][:80]}..."):
                        st.write(f"**作者**: u/{post['author']}")
                        st.write(f"**社区**: r/{post['subreddit']}")
                        st.write(f"**得分**: {post['score']} | **评论数**: {post['num_comments']}")
                        st.write(f"**发布时间**: {post['created_date']}")
                        st.markdown(f"[查看原帖]({post['permalink']})")

        with tab2:
            st.header("情感分析")

            # 情感分布概览
            col1, col2, col3 = st.columns(3)
            col1.metric(
                "😊 正面",
                f"{sentiment_distribution['positive']['percentage']}%",
                f"{sentiment_distribution['positive']['count']} 条"
            )
            col2.metric(
                "😐 中性",
                f"{sentiment_distribution['neutral']['percentage']}%",
                f"{sentiment_distribution['neutral']['count']} 条"
            )
            col3.metric(
                "😞 负面",
                f"{sentiment_distribution['negative']['percentage']}%",
                f"{sentiment_distribution['negative']['count']} 条"
            )

            st.markdown("---")

            # 情感图表
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("整体情感分布")
                if os.path.exists('output/sentiment_distribution.png'):
                    st.image('output/sentiment_distribution.png')

            with col2:
                st.subheader("各Subreddit情感对比")
                if os.path.exists('output/sentiment_by_subreddit.png'):
                    st.image('output/sentiment_by_subreddit.png')

        with tab3:
            st.header("话题分析")

            # 词云
            st.subheader("词云图")
            if os.path.exists('output/wordcloud.png'):
                st.image('output/wordcloud.png', use_container_width=True)

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                # 关键词
                st.subheader("🔑 高频关键词 Top 20")
                if keywords:
                    keywords_df = pd.DataFrame(
                        list(keywords.items())[:20],
                        columns=['关键词', '出现次数']
                    )
                    st.dataframe(keywords_df, use_container_width=True, hide_index=True)

            with col2:
                # 话题分布
                st.subheader("📊 话题分布")
                if os.path.exists('output/topic_distribution.png'):
                    st.image('output/topic_distribution.png')

        with tab4:
            st.header("数据下载")

            st.markdown("### 📥 导出文件")

            # CSV文件下载
            col1, col2 = st.columns(2)

            with col1:
                if os.path.exists('output/reddit_data_posts.csv'):
                    with open('output/reddit_data_posts.csv', 'rb') as f:
                        st.download_button(
                            label="📄 下载帖子数据 (CSV)",
                            data=f,
                            file_name=f"{brand}_{product}_posts.csv",
                            mime="text/csv"
                        )

            with col2:
                if os.path.exists('output/reddit_data_comments.csv'):
                    with open('output/reddit_data_comments.csv', 'rb') as f:
                        st.download_button(
                            label="💬 下载评论数据 (CSV)",
                            data=f,
                            file_name=f"{brand}_{product}_comments.csv",
                            mime="text/csv"
                        )

            # 报告下载
            st.markdown("### 📊 分析报告")

            col1, col2 = st.columns(2)

            with col1:
                if os.path.exists('output/analysis_report.json'):
                    with open('output/analysis_report.json', 'rb') as f:
                        st.download_button(
                            label="📋 下载完整报告 (JSON)",
                            data=f,
                            file_name=f"{brand}_{product}_report.json",
                            mime="application/json"
                        )

            with col2:
                if os.path.exists('output/analysis_report.txt'):
                    with open('output/analysis_report.txt', 'rb') as f:
                        st.download_button(
                            label="📝 下载简要报告 (TXT)",
                            data=f,
                            file_name=f"{brand}_{product}_report.txt",
                            mime="text/plain"
                        )

            # 图表下载说明
            st.markdown("### 🖼️ 图表文件")
            st.info("所有图表已保存在 `output/` 目录，包括：\n- sentiment_distribution.png\n- subreddit_distribution.png\n- time_series.png\n- topic_distribution.png\n- sentiment_by_subreddit.png\n- wordcloud.png")

    except Exception as e:
        st.error(f"❌ 分析过程中出现错误: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Reddit品牌产品分析器 | 无需API凭证，简单易用</p>
    <p>基于Python + Streamlit构建</p>
</div>
""", unsafe_allow_html=True)
