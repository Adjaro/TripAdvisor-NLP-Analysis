import pandas as pd
import tiktoken
from tqdm import tqdm
import os
import re
import uuid
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from chromadb.config import Settings
import logging

# Initialize tiktoken encoding
enc = tiktoken.get_encoding("o200k_base")

class BDDChunks:
    """
    A class to process restaurant data and reviews from a SQLite database,
    transforming them into consolidated chunks with embeddings stored in ChromaDB.
    """

    def __init__(self, embedding_model: str, path: str):
        """
        Initialize the BDDChunks instance.

        Args:
            embedding_model (str): Name of the embedding model to use.
            path (str): Path to the dataset or collection.
        """
        self.path = path
        self.client = chromadb.PersistentClient(
            path="./ChromaDB11", settings=Settings(anonymized_telemetry=False)
        )
        self.embedding_name = embedding_model
        self.embeddings = SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        self.chroma_db = None

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_db(self):
        """
        Provide a database session.

        Yields:
            db: Database session instance.
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
            list[str]: List of restaurant names.
        """
        try:
            with next(self.get_db()) as db:
                restaurants = db.query(models.DimRestaurant).all()
                return [r.nom for r in restaurants]
        except Exception as e:
            self.logger.error(f"An error occurred while fetching restaurant names: {e}")
            return []

    def _sanitize_collection_name(self, name: str) -> str:
        """
        Sanitize collection name to meet ChromaDB requirements:
        - 3-63 characters
        - Alphanumeric with hyphens and underscores
        - No consecutive periods
        """
        sanitized = re.sub(r'[^a-zA-Z0-9-_]', '-', name)
        sanitized = re.sub(r'^[^a-zA-Z0-9]+', '', sanitized)
        sanitized = re.sub(r'[^a-zA-Z0-9]+$', '', sanitized)
        sanitized = re.sub(r'\.{2,}', '.', sanitized)
        if len(sanitized) < 3:
            sanitized = sanitized + "000"[:3-len(sanitized)]
        if len(sanitized) > 63:
            sanitized = sanitized[:63]
        return sanitized

    def _create_collection(self, path: str) -> None:
        """
        Create a new ChromaDB collection to store embeddings.

        Args:
            path (str): Name of the collection to create in ChromaDB.
        """
        try:
            collection_name = self._sanitize_collection_name(path)
            self.chroma_db = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embeddings,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            self.logger.error(f"Error creating collection: {e}")
            raise

    def clean_text(self, text: str) -> str:
        """
        Clean text by removing unwanted characters and spaces.

        Args:
            text (str): Input text.

        Returns:
            str: Cleaned text.
        """
        text = re.sub(r"\s+", " ", text)  # Remove multiple spaces
        text = re.sub(r"[^a-zA-Z0-9À-ÿ\s]", "", text)  # Remove special characters
        return text.strip()

    def get_restaurant_reviews_location(self, restaurant_name: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Get the location and reviews for a specific restaurant.

        Args:
            restaurant_name (str): Name of the restaurant.

        Returns:
            tuple: DataFrames for reviews, location, and restaurant info.
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
            self.logger.error(f"An error occurred while fetching reviews and locations: {e}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # def transform_restaurant_chunk(self, restaurant_name: str,  chuncksize: 500) -> pd.DataFrame:
    #     """
    #     Transform restaurant data and reviews into a single structured chunk.

    #     Args:
    #         restaurant_name (str): Name of the restaurant.

    #     Returns:
    #         pd.DataFrame: DataFrame containing the chunks.
    #     """
    #     colnames = ['restaurant', 'chunk']
    #     avis_df, location_df, restaurant_df = self.get_restaurant_reviews_location(restaurant_name)

    #     if restaurant_df.empty:
    #         return pd.DataFrame(columns=colnames)

    #     # Combine all information into a single chunk
    #     all_info = f"Restaurant: {restaurant_df['nom'].iloc[0]} | Description: {restaurant_df['nom'].iloc[0]} " \
    #                f"| Localisation: {location_df['adresse'].iloc[0]}, {location_df['adresse'].iloc[0]} | " \
    #                f"Avis: {' | '.join(avis_df['review'].apply(self.clean_text))}"

    #     chunks = [{'restaurant': restaurant_name, 'chunk': all_info}]
    #     return pd.DataFrame(chunks, columns=colnames)


    def transform_restaurant_chunk(self, restaurant_name: str, chunk_size: int = 5000) -> pd.DataFrame:
        """
        Transform restaurant data and reviews into structured chunks.

        Args:
            restaurant_name (str): Name of the restaurant.
            chunk_size (int, optional): Maximum size of each chunk (in characters). Defaults to 500.

        Returns:
            pd.DataFrame: DataFrame containing the chunks with restaurant names.
        """
        colnames = ['restaurant', 'chunk']
        avis_df, location_df, restaurant_df = self.get_restaurant_reviews_location(restaurant_name)

        if restaurant_df.empty:
            return pd.DataFrame(columns=colnames)

        # Combine all relevant data into a single string
        combined_info = []
        
        for column in restaurant_df.columns:
            value = self.clean_text(str(restaurant_df[column].iloc[0]))
            combined_info.append(f"{column}: {value}")
        
        for column in location_df.columns:
            value = self.clean_text(str(location_df[column].iloc[0]))
            combined_info.append(f"{column}: {value}")
        
        for _, review in avis_df.iterrows():
            cleaned_review = self.clean_text(review['review'])
            combined_info.append(f"Review: {cleaned_review}")
        
        all_info = " ".join(combined_info)

        # Split the information into chunks of `chunk_size`
        chunks = []
        while len(all_info) > 0:
            chunk = all_info[:chunk_size]
            # Add the restaurant name at the beginning of each chunk
            chunks.append(f"Restaurant: {restaurant_name} | {chunk}")
            all_info = all_info[chunk_size:]

        # Create a DataFrame for the chunks
        chunk_data = [{'restaurant': restaurant_name, 'chunk': chunk} for chunk in chunks]
        return pd.DataFrame(chunk_data, columns=colnames)


    def create_corpus(self) -> str:
        """
        Create a corpus with a single chunk per restaurant.

        Returns:
            str: Text corpus containing all information.
        """
        corpus = []
        for restaurant in self.get_all_restaurants_names():
            df = self.transform_restaurant_chunk(restaurant)
            if not df.empty:
                corpus.append(" ".join(df['chunk'].values))
        return " ".join(corpus)

    def split_text_into_chunks(self, corpus: str, chunk_size: int = 100) -> list[str]:
        """
        Split text into chunks of specified size.

        Args:
            corpus (str): Text to split.
            chunk_size (int, optional): Size of each chunk.

        Returns:
            list[str]: List of chunks.
        """
        tokenized_corpus = enc.encode(corpus)
        chunks = [
            "".join(enc.decode(tokenized_corpus[i : i + chunk_size]))
            for i in tqdm(range(0, len(tokenized_corpus), chunk_size))
        ]
        return chunks
    
    

    def add_embeddings(self, restaurant_chunks: pd.DataFrame) -> None:
        """
        Add embeddings for each restaurant chunk to the ChromaDB collection.

        Args:
            restaurant_chunks (pd.DataFrame): DataFrame containing restaurant names and their corresponding chunks.
        """
        if self.chroma_db is None:
            raise ValueError("ChromaDB collection is not initialized. Call `_create_collection` first.")

        for _, row in tqdm(restaurant_chunks.iterrows(), total=restaurant_chunks.shape[0]):
            restaurant_name = row['restaurant']
            chunk = row['chunk']
            document_id = str(uuid.uuid4())  # Generate a unique ID for this chunk
            self.chroma_db.add(documents=[chunk], ids=[document_id], metadatas=[{"restaurant": restaurant_name}])


    def __call__(self, *args, **kwargs):
        """
        Entry point to execute class methods.
        """
        self._create_collection(self.path)
        all_restaurant_chunks = []

        for restaurant_name in self.get_all_restaurants_names():
            restaurant_chunk = self.transform_restaurant_chunk(restaurant_name)
            if not restaurant_chunk.empty:
                all_restaurant_chunks.append(restaurant_chunk)

        if all_restaurant_chunks:
            all_chunks_df = pd.concat(all_restaurant_chunks, ignore_index=True)
            self.add_embeddings(all_chunks_df)


# # Test the class
# if __name__ == "__main__":
#     test = BDDChunks(embedding_model="paraphrase-multilingual-MiniLM-L12-v2", path="./")
#     test()
#     print("Done")
