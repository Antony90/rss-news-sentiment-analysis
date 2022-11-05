'''
Pull news articles from API, several sources
analyze each article, store article + sent under source 
'''
from datetime import datetime
from database import get_database
from models.article import Article
from models.provider import INewsProvider
from models.rss_provider import RSSNewsProvider
from transformers import pipeline
from pymongo.errors import DuplicateKeyError
import opengraph_parse


class AnalyzeNews:
    def __init__(self):
        self.sentiment_pipeline = pipeline(
            model="distilbert-base-uncased-finetuned-sst-2-english",
            task="sentiment-analysis")
        self.providers: list[INewsProvider] = self._init_providers()
        self.db = get_database()
        self.articles_ref = self.db.get_collection('articles')

    def _init_providers(self):
        '''
        RSS Feeds are listed by category
        '''
        provider_category_feeds = {
            'BBC': [
                ("Top Stories"  , 'http://feeds.bbci.co.uk/news/rss.xml'                       ),
                ("Technology"   , 'http://feeds.bbci.co.uk/news/technology/rss.xml'            ),
                ("World"        , 'http://feeds.bbci.co.uk/news/world/rss.xml'                 ),
                ("Politics"     , 'http://feeds.bbci.co.uk/news/politics/rss.xml'              ),
                ("Business"     , 'http://feeds.bbci.co.uk/news/business/rss.xml'              ),
                ("Entertainment", 'http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml')
            ],
            'Sky News': [
                ("Top Stories"  , 'https://feeds.skynews.com/feeds/rss/home.xml'         ),
                ("Technology"   , 'https://feeds.skynews.com/feeds/rss/technology.xml'   ),
                ("World"        , 'https://feeds.skynews.com/feeds/rss/world.xml'        ),
                ("Politics"     , 'https://feeds.skynews.com/feeds/rss/politics.xml'     ),
                ("Business"     , 'https://feeds.skynews.com/feeds/rss/business.xml'     ),
                ("Entertainment", 'https://feeds.skynews.com/feeds/rss/entertainment.xml')
            ],
            'Daily Mail': [
                ("Top Stories", 'https://www.dailymail.co.uk/news/index.rss'),
            ]
        }
        return [
            RSSNewsProvider(source_url=source_url,
                            category=category,
                            publisher=publisher)
            for publisher, feed_category_urls in provider_category_feeds.items()
            for (category, source_url) in feed_category_urls
        ]

    def _fetch_all_articles(self) -> list[Article]:
        '''
        Get providers' articles, concatenate all lists
        '''
        providers = (prov.get_articles() for prov in self.providers)
        all_articles = []
        for prov_articles in providers:
            all_articles.extend(prov_articles)
        return all_articles

    def _filter_saved_articles(self, articles: list[Article]):
        '''
        Poll db for links of saved articles. Prune article
        if link already exists.
        '''
        article_docs = self.articles_ref.find({}, {"link": 1})
        article_links = map(lambda doc: doc['link'], article_docs)
        article_links = set(article_links)
        return [art for art in articles if art.link not in article_links]

    def save_articles(self, articles: list[Article]):
        insert_count = 0
        for article in articles:
            try:
                # Convert Article object to dictionary
                self.articles_ref.insert_one(article.__dict__)
            except DuplicateKeyError:  # Article has existing link
                continue
            else:
                insert_count += 1
        return insert_count

    def _get_preview_img_url(self, article):  # TODO: multi thread function
        '''
        Get the url used by preview images using open graph meta tags.
        See https://ogp.me/
        '''
        return opengraph_parse \
            .parse_page(article.link, ["og:image"]) \
            .get("og:image")

    def get_sentiment(self, articles: list[Article]):
        article_titles = [article.title for article in articles]
        predictions = self.sentiment_pipeline(article_titles)
        return predictions

    def run(self):
        print(f"[analyzer] [{datetime.now().strftime('%H:%M')}] Start job")
        articles = self._fetch_all_articles()
        init_len = len(articles)
        articles = self._filter_saved_articles(articles)
        print(f'[analyzer] Pruned {init_len-len(articles)} existing articles')
        sentiment = self.get_sentiment(articles)
        print(f'[analyzer] Analyzed sentiment of {len(articles)} articles')

        # Add sentiment key to each dict
        for article, sentiment in zip(articles, sentiment):
            img_url = self._get_preview_img_url(article)
            i = 1 if sentiment.get('label') == 'POSITIVE' else -1
            score = i * sentiment.get('score')
            article.img_url = img_url
            article.sentiment = score

        # Update articles database
        # num_saved = self.save_articles(articles)
        print(
            f"[analyzer] [{datetime.now().strftime('%H:%M')}] Saved {len(articles)} articles")


if __name__ == '__main__':
    task = AnalyzeNews()
    task.run()
