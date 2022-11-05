from dataclasses import dataclass
from datetime import datetime
from models.article import Article
from models.provider import INewsProvider

import requests

@dataclass
class RESTNewsProvider(INewsProvider):
    api_endpoint: str

    def get_articles(self) -> list[Article]:
        response = requests.get(self.api_endpoint)
        if response.status_code != 200:
            print(f'[provider] [REST] Error: {response.status_code}')
            
        articles = [
            Article(
                title=article['title'],
                summary=article['summary'],
                link=article['link'],
                publisher=article['publisher'],
                published_date=datetime(article['published_date']),
                category=article['topic']  # Category is constant per RSS feed URL
            )
            for article in response.json.get("articles")]
        print(f'[provider] [REST] Fetched {len(articles)} articles')
        return articles


if __name__ == '__main__':
    prov = RESTNewsProvider("")
    articles = prov.get_articles()
    print(articles)
    print(f'{len(articles)} articles')
