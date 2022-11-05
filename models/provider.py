from models.article import Article

class INewsProvider:

    def get_articles(self) -> list[Article]:
        pass
        