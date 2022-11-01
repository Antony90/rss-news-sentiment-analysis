'''
Pull news articles from API, several sources
analyze each article, store article + sent under source 
'''
from datetime import datetime
from database import get_database
from provider import NewsProvider
from transformers import pipeline
from pymongo.errors import DuplicateKeyError
import opengraph_parse


class AnalyzeNews:
    def __init__(self):
        self.sentiment_pipeline = pipeline(
            model="distilbert-base-uncased-finetuned-sst-2-english",
            task="sentiment-analysis")
        self.providers: list[NewsProvider] = self._init_providers()
        self.db = get_database()
        self.articles_ref = self.db.get_collection('articles')

    def _init_providers(self):
        '''
        RSS Feeds are listed by category
        '''
        provider_category_feeds ={
            'BBC': [
                'http://feeds.bbci.co.uk/news/rss.xml',
                'http://feeds.bbci.co.uk/news/technology/rss.xml',
                'http://feeds.bbci.co.uk/news/world/rss.xml',
                'http://feeds.bbci.co.uk/news/politics/rss.xml',
                'http://feeds.bbci.co.uk/news/business/rss.xml',
                'http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml'
            ],
            'Sky News': [
                'https://feeds.skynews.com/feeds/rss/home.xml',
                'https://feeds.skynews.com/feeds/rss/technology.xml',
                'https://feeds.skynews.com/feeds/rss/world.xml',
                'https://feeds.skynews.com/feeds/rss/politics.xml',
                'https://feeds.skynews.com/feeds/rss/business.xml',
                'https://feeds.skynews.com/feeds/rss/entertainment.xml'
            ],
            'Daily Mail': [
                'https://www.dailymail.co.uk/news/index.rss',
            ]
        }
        return [NewsProvider(source, feed_category_urls)
                for source, feed_category_urls in provider_category_feeds.items()
                ]

    def _fetch_all_articles(self):
        providers = (prov.get_articles() for prov in self.providers)
        all_articles = []
        for prov_articles in providers:
            all_articles.extend(prov_articles)
        return all_articles

    def _filter_saved_articles(self, articles):
        '''
        Poll db for links of saved articles. Prune article
        if link exists already.
        '''
        article_docs = self.articles_ref.find({}, {"link": 1})
        article_links = map(lambda doc: doc['link'], article_docs)
        article_links = set(article_links)
        return [art for art in articles if art['link'] not in article_links]
        

    def save_articles(self, articles: list[dict]):
        insert_count = 0
        for article in articles:
            try:
                self.articles_ref.insert_one(article)
            except DuplicateKeyError:  # Article has existing link
                continue
            else:
                insert_count += 1
        return insert_count
    
    def _get_preview_img_url(self, article): # TODO: multi thread function
        '''
        Get the url used by preview images using open graph meta tags.
        See https://ogp.me/
        '''
        return opengraph_parse \
            .parse_page(article.get('link'), ["og:image"]) \
            .get("og:image")

    def get_sentiment(self, articles):
        article_titles = [article.get('title') for article in articles]
        predictions = self.sentiment_pipeline(article_titles)
        return predictions
        # batch_input_ids = self.tokenizer.batch_encode_plus(article_titles,
        #                         padding='longest',
        #                         truncation=True,
        #                         return_tensors="tf")
        # predictions = self.model(batch_input_ids)

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
            article.update({
                'img_url': img_url,
                'sentiment': score
            })
            article['sentiment'] = i * sentiment.get('score')

        # Update articles database
        num_saved = self.save_articles(articles)
        print(
            f"[analyzer] [{datetime.now().strftime('%H:%M')}] Saved {num_saved} articles")


if __name__ == '__main__':
    task = AnalyzeNews()
    task.run()
