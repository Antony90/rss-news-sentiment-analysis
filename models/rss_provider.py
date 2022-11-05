from dataclasses import dataclass
from datetime import datetime
from time import mktime
from feedparser import parse
from models.article import Article

from models.provider import INewsProvider


@dataclass
class RSSNewsProvider(INewsProvider):
    # [ technology, world, politics, business, entertainment ]
    source_url: str
    category: str
    publisher: str
    
    def _time_struct_to_datetime(self, time_struct):
        return datetime.fromtimestamp(mktime(time_struct))
        
    def get_articles(self) -> list[Article]:
        articles = []
        xml = parse(self.source_url)
        if xml.get('status') != 200:
            print(
                f'[provider] [{self.source[:10]+"..."}] Error: {xml.get("status")}')

        articles = [
            Article(
                title=article['title'],
                summary=article['summary'],
                link=article['link'],
                publisher=self.publisher,
                published_date=self._time_struct_to_datetime(article['published_parsed']),
                category=self.category # Category is constant per RSS feed URL
            )
            for article in xml.entries]
        print(f'[provider] [{self.publisher}] Fetched {len(articles)} articles')
        return articles


if __name__ == '__main__':
    prov = RSSNewsProvider(
        publisher='BBC',
        source_url='http://feeds.bbci.co.uk/news/rss.xml',
        category="Top Stories"
    )
    articles = prov.get_articles()
    print(articles)
    print(f'{len(articles)} articles')
