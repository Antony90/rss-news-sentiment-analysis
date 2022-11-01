from pymongo import ASCENDING, HASHED, MongoClient
from dotenv import load_dotenv
from os import environ
env = environ
load_dotenv()

# Flag for when database is new
# Will create index for unique article links
new_database = False

def get_database():
    # MongoDB Atlas URL to connect pymongo to database
    connection_string = f"mongodb+srv://{env['MONGODB_USER']}:{env['MONGODB_PASS']}@cluster0.rr5os7q.mongodb.net/{env['DB']}"
    
    client = MongoClient(connection_string)
    db = client[env['DB']]
    # Links are unique to prevent duplicate stories being saved
    if new_database:
        articles_collection = db.get_collection('articles')
        articles_collection.create_index('link', unique=True)
        articles_collection.create_index([('published_date', ASCENDING)])
        articles_collection.create_index([('category_id', ASCENDING)])
        articles_collection.create_index([('provider', ASCENDING)])

    return db
