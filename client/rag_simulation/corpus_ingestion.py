from model import models, schemas
from utils import database
import pandas as pd
import tiktoken
from tqdm import tqdm


enc = tiktoken.get_encoding("o200k_base")

class BDDChunks:
    """
    A class to process reviews from a SQLite database and store them as chunks with embeddings.
    Each review is considered a single chunk.
    """

    def __init__(self):
        """
        Initialize the BDDChunksSQLite instance.
        """
        self.db = None  # Placeholder for the database session.

    def get_db(self):
        """
        Provide a database session.

        Yields:
            db: A session instance from the database.
        """
        db = database.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def get_all_restaurants_names(self) -> list[str]:
        """
        Get all restaurant names from the SQLite database.

        Returns:
            list[str]: A list of restaurant names.
        """
        try:
            with next(self.get_db()) as db:
                restaurants = db.query(models.DimRestaurant).all()
                return [r.nom for r in restaurants]
        except Exception as e:
            print(f"An error occurred while fetching restaurant names: {e}")
            return []

    def convert_to_arrow_compatible(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert a DataFrame to an Arrow-compatible format.
        
        Args:
            df (pd.DataFrame): Input DataFrame.
        
        Returns:
            pd.DataFrame: Converted DataFrame.
        """
        for column in df.columns:
            if df[column].dtype == 'object':
                df[column] = df[column].astype(str)
            elif df[column].dtype == 'int64':
                df[column] = df[column].astype('int32')
        return df

    def get_restaurant_reviews_location(self, restaurant_name: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Get the location and reviews for a specific restaurant.

        Args:
            restaurant_name (str): The name of the restaurant.

        Returns:
            tuple: DataFrames for reviews, location, and restaurant information.
        """
        try:
            with next(self.get_db()) as db:
                restaurant = db.query(models.DimRestaurant).filter(models.DimRestaurant.nom == restaurant_name).first()
                location = db.query(models.DimLocation).filter(models.DimLocation.id_location == restaurant.id_location).first()
                avis = db.query(models.FaitAvis).filter(models.FaitAvis.id_restaurant == restaurant.id_restaurant).all()
            
            avis_df = pd.DataFrame([schemas.FaitAvis.from_orm(a).dict() for a in avis])
            location_df = pd.DataFrame([schemas.DimLocation.from_orm(location).dict()])
            restaurant_df = pd.DataFrame([schemas.DimRestaurant.from_orm(restaurant).dict()])
            
            return avis_df, location_df, restaurant_df
        except Exception as e:
            print(f"An error occurred while fetching restaurant reviews location: {e}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def transform_restaurant_chunk(self, restaurant_name: str) -> pd.DataFrame:
        """
        Transform a restaurant's data and reviews into structured chunks.

        Args:
            restaurant_name (str): The name of the restaurant.

        Returns:
            pd.DataFrame: A DataFrame containing the restaurant chunks.
        """
        colnames = ['restaurant', 'chunk']
        avis_df, location_df, restaurant_df = self.get_restaurant_reviews_location(restaurant_name)
        
        if restaurant_df.empty:
            return pd.DataFrame(columns=colnames)

        chunks = []
        for column in restaurant_df.columns:
            value = restaurant_df[column].iloc[0]
            chunks.append({'restaurant': restaurant_name, 'chunk': f"{column}: {value}"})

        # Include review comments as chunks
        for _, review in avis_df.iterrows():
            chunks.append({'restaurant': restaurant_name, 'chunk': f"Review: {review['review']}"})

        return pd.DataFrame(chunks, columns=colnames)

    def create_corpus(self) -> str:
        """
        Create a corpus from the restaurant chunks.

        Returns:
            str: The text corpus.
        """
        corpus = ""
        for restaurant in self.get_all_restaurants_names():
            df = self.transform_restaurant_chunk(restaurant)
            corpus += " ".join(df['chunk'].values) + " "
        return corpus

    def insert_into_db(self):
        """
        Insert the chunks into the SQLite database in batches for improved performance.
        """
        all_restaurants = self.get_all_restaurants_names()
        batch_size = 100 # Define the batch size for insertion

        for restaurant in tqdm(all_restaurants):
            #verifier si le restaurant est deja dans la table rag_avis
            try:
                with next(self.get_db()) as db:
                    restaurant_exists = db.query(models.RagAvis).filter(models.RagAvis.restaurantName == restaurant).first()
            except Exception as e:
                print(f"An error occurred while checking if the restaurant exists in the database: {e}")
                restaurant_exists = None

            if restaurant_exists:
                print(f"Restaurant {restaurant} already exists in the database.")
                continue
            df = self.transform_restaurant_chunk(restaurant)
            chunks = [
                models.RagAvis(restaurantName=row['restaurant'], review=row['chunk'])
                for _, row in df.iterrows()
            ]

            try:
                with next(self.get_db()) as db:
                    for i in range(0, len(chunks), batch_size):
                        db.bulk_save_objects(chunks[i:i + batch_size])
                        db.commit()
            except Exception as e:
                print(f"An error occurred while inserting chunks into the database for {restaurant}: {e}")


    def __call__(self, *args, **kwargs):
        """
        Entry point to invoke methods of the class.
        """
        self.insert_into_db()


# # Test the class
# if __name__ == "__main__":
#     test = BDDChunksSQLite()
#     test.insert_into_db()
