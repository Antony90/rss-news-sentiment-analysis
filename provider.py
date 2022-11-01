from dataclasses import dataclass
from datetime import datetime
import json
from time import mktime
from feedparser import parse


article_attrs = ['title', 'link', 'summary', 'published_parsed']
@dataclass
class NewsProvider:
    source: str
    # URLs are ordered by category 
    # [ technology, world, politics, business, entertainment ]
    feed_category_urls: dict[str, str]


    def get_articles(self) -> list[dict]:
        articles = []
        for category_id, feed_url in enumerate(self.feed_category_urls):
            xml = parse(feed_url)
            if xml.get('status') != 200:
                print(f'[provider] [{self.source}] Error: {xml.get("status")}, cat_id: {category_id}')
                continue
            
            category_articles = xml.entries

            # Filter dictionary
            category_articles = [{key: val for (key, val) in article.items() if key in article_attrs}
                        for article in category_articles]
            for article in category_articles:
                time_struct = article.pop('published_parsed')
                
                article.update({
                    'published_date': datetime.fromtimestamp(mktime(time_struct)),
                    'provider': self.source,
                    'category_id': category_id,
                })
            print(f'[provider] [{self.source}] Fetched {len(category_articles)} aricles, cat_id: {category_id}')
            articles.extend(category_articles)
        return articles


if __name__ == '__main__':
    prov = NewsProvider(
        source='Telegraph',
        feed_url='https://www.telegraph.co.uk/rss.xml'
    )
    articles = prov.get_articles()
    
    print(articles[0].keys())
    print(json.dumps(articles[0], indent=4))
    print(f'{len(articles)} articles')
