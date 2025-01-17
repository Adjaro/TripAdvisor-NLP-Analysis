# from model import models, schemas
from  model import models, schemas
from utils import database
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
    A class to process reviews from a SQLite database and store them as chunks with embeddings.
    Each review is considered a single chunk.
    """

    def __init__(self, embedding_model: str, path: str):
        """
        Initialize the BDDChunks instance.

        Args:
            embedding_model (str): Name of the embedding model to use.
            path (str): Path to the PDF or dataset to process.
        """
        self.path = path
        self.chunks: list[str] | None = None
        self.client = chromadb.PersistentClient(
            path="./ChromaDB", settings=Settings(anonymized_telemetry=False)
        )
        self.embedding_name = embedding_model
        self.embeddings = SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        self.chroma_db = None
        # self.chroma_db = self._create_collection(path)
        # self.chroma_db = self.client.get_or_create_collection(name=file_name, embedding_function=self.embeddings, metadata={"hnsw:space": "cosine"})  # type: ignore

        
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
        # Replace invalid characters with hyphens
        sanitized = re.sub(r'[^a-zA-Z0-9-_]', '-', name)
        
        # Ensure name starts and ends with alphanumeric
        sanitized = re.sub(r'^[^a-zA-Z0-9]+', '', sanitized)
        sanitized = re.sub(r'[^a-zA-Z0-9]+$', '', sanitized)
        
        # Remove consecutive periods
        sanitized = re.sub(r'\.{2,}', '.', sanitized)
        
        # Ensure minimum length
        if len(sanitized) < 3:
            sanitized = sanitized + "000"[:3-len(sanitized)]
            
        # Truncate if too long
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
            # Create a valid collection name
            collection_name = self._sanitize_collection_name(path)
            self.chroma_db = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embeddings,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            self.logger.error(f"Error creating collection: {e}")
            raise

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

    def transform_restaurant_chunk(self, restaurant_name: str) -> pd.DataFrame:
        """
        Transform restaurant data and reviews into structured chunks.

        Args:
            restaurant_name (str): Name of the restaurant.

        Returns:
            pd.DataFrame: DataFrame containing the chunks.
        """
        colnames = ['restaurant', 'chunk']
        avis_df, location_df, restaurant_df = self.get_restaurant_reviews_location(restaurant_name)
        
        if restaurant_df.empty:
            return pd.DataFrame(columns=colnames)

        chunks = []
        for column in restaurant_df.columns:
            value = restaurant_df[column].iloc[0]
            chunks.append({'restaurant': restaurant_name, 'chunk': f"{column}: {value}"})

        # Include reviews as chunks
        for _, review in avis_df.iterrows():
            chunks.append({'restaurant': restaurant_name, 'chunk': f"Review: {review['review']}"})

        return pd.DataFrame(chunks, columns=colnames)

    def create_corpus(self) -> str:
        """
        Create a corpus from restaurant chunks.

        Returns:
            str: Text corpus.
        """
        corpus = ""
        for restaurant in self.get_all_restaurants_names():
            df = self.transform_restaurant_chunk(restaurant)
            corpus += " ".join(df['chunk'].values) + " "
        return corpus

    def split_text_into_chunks(self, corpus: str, chunk_size: int = 500) -> list[str]:
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

    def add_embeddings(self, list_chunks: list[str], batch_size: int = 100) -> None:
        """
        Add embeddings to the ChromaDB collection.

        Args:
            list_chunks (list[str]): List of chunks.
            batch_size (int, optional): Batch size.
        """
        if self.chroma_db is None:
            raise ValueError("ChromaDB collection is not initialized. Call `_create_collection` first.")
        
        if len(list_chunks) < batch_size:
            batch_size_for_chromadb = len(list_chunks)
        else:
            batch_size_for_chromadb = batch_size

        for i in tqdm(range(0, len(list_chunks), batch_size_for_chromadb)):
            batch_documents = list_chunks[i : i + batch_size_for_chromadb]
            list_ids = [str(uuid.uuid4()) for _ in batch_documents]
            self.chroma_db.add(documents=batch_documents, ids=list_ids)

    def __call__(self, *args, **kwargs):
        """
        Entry point to execute class methods.
        """
        # corpus = self.create_corpus()
        # corpus = self.read_pdf(file_path=self.path)
        # chunks = self.split_text_into_chunks(corpus=corpus)
        # self._create_collection(path=self.path)
        # self.add_embeddings(list_chunks=chunks)

# # Test the class
# if __name__ == "__main__":
#     test = BDDChunks(embedding_model="paraphrase-xlm-r-multilingual-v1", path="./")
#     test()