import os
import pymongo
import pandas as pd
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)

def configure():
    """Load environment variables."""
    load_dotenv()

def connect_to_mongo():
    """Connect to MongoDB and return the database."""
    mongo_uri = os.getenv('MONGO_URI')
    client = pymongo.MongoClient(mongo_uri)
    db_name = os.getenv('MONGODB_DATABASE', 'default_db_name').replace(' ', '_')
    return client[db_name]

def extract_data(collection_name, db):
    """Extract data from a MongoDB collection and convert to DataFrame."""
    collection = db[collection_name]
    data = list(collection.find())
    logging.info(f"Extracted {len(data)} records from {collection_name}.")
    return pd.DataFrame(data)  # Convert to DataFrame directly

def main():
    configure()  # Load environment variables
    db = connect_to_mongo()  # Connect to MongoDB

    # List of your collection names
    collections = ['movie_details']  
    
    # Dictionary to store DataFrames
    all_dataframes = {}

    # Extract data from each collection and convert to DataFrame
    for collection_name in collections:
        df = extract_data(collection_name, db)
        all_dataframes[collection_name] = df  # Store DataFrame in dictionary

    # Optional: Print the DataFrames or perform further operations
    for name, df in all_dataframes.items():
        print(f"\nData from collection: {name}")
        print(df.head())  # Display the first few rows of each DataFrame

if __name__ == "__main__":
    main()