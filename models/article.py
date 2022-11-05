from dataclasses import dataclass
from datetime import datetime

@dataclass
class Article:
  title: str
  summary: str
  link: str
  publisher: str # TODO: update backend, rename provider
  published_date: datetime
  category: str
  sentiment: float = 0 # Initial value
  img_url: str = ""
