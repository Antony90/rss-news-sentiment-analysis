# RSS News Sentiment Analysis
A Python application that aggregates news articles from multiple RSS feeds, performs sentiment analysis on their content, and stores results in MongoDB.

This backend aggregates all the data used by [my news web app](https://github.com/Antony90/my-news). 

## Features  
- **Multi-source aggregation** - BBC, Sky News, Daily Mail RSS feeds  
- **Sentiment analysis** - DistilBERT model fine-tuned on SST-2  
- **MongoDB storage** - Persistent article storage using indexes for efficient operations and Beautiful charts using [MongoDB Atlas](https://www.mongodb.com/products/platform/atlas-charts)
- **Scheduled processing** - Hourly updates via APScheduler  

## Requirements  
- Python 3.10+
- MongoDB Atlas (or local MongoDB instance)  

## Setup
1. Create a `.env` file with the contents:
    ```env
    MONGODB_USER=db_username
    MONGODB_PASS=db_password
    DB=sentiment_analysis
    ```
2. Install python dependencies
    ```
    python3 -m pip install -r requirements.txt
    ```

3. Start the scheduler. Will poll all RSS feeds hourly.
    ```
    python3 main.py
    ```

This repository is fully compatible with [Heroku's free deployment tier for Python](https://www.heroku.com/python), and is what I personally.

## Key Components  
### Article Processing Pipeline  
1. **Fetch** - Retrieve articles from configured RSS providers  
2. **Filter** - Remove previously stored articles  
3. **Analyze** - Calculate sentiment scores using DistilBERT  
4. **Enrich** - Extract preview images via OpenGraph  
5. **Store** - Save results, ensuring no duplicates with same link URL

### Sentiment Analysis  
- **Model** - `distilbert-base-uncased-finetuned-sst-2-english`  
- **Scoring** - The title of the article is processed, and the sentiment score is parsed as positive for 0 to 1 range, and negative for 0 to -1 range.

### Database Schema
The MongoDB collection is given the following schema with indexing:
```ts
{
    "title": str,
    "summary": str,
    "link": str, // Unique index
    "publisher": str,
    "published_date": datetime, // indexed
    "category": str,
    "sentiment": float, // Range: -1.0 to 1.0, indexed
    "img_url": str
}
```

## Limitations  
- **Single-threaded** - No parallel processing for image extraction (TODO)  
- **English-only** - Model optimized for English content  
- **Title-based** - Sentiment analysis limited to article titles, and may be tricked with nuanced titles.