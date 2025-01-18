from ..model import models, schemas
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

import litellm
import numpy as np
from numpy.typing import NDArray
import  time
from dotenv import load_dotenv, find_dotenv

# from .rag_simulation.corpus_ingestion import BDDChunks
load_dotenv(find_dotenv())


class AugmentedRAG:
    """A class for performing a simple RAG process.

    This class utilizes a retrieval process to fetch relevant information from a
    database (or corpus) and then passes it to a generative model for further processing.

    """
    HF_TOKEN = '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'
    MISTRAL_API_KEY =  'dkMKu81kFgJeP7HmIqjztosQTxyiynW6'


    def __init__(
        self,
        generation_model: str,
        role_prompt: str,
        bdd_chunks: BDDChunks,
        max_tokens: int,
        temperature: int,
        top_n: int = 2,
    ) -> None:
        """
        Initializes the SimpleRAG class with the provided parameters.

        Args:
            generation_model (str): The model used for generating responses.
            role_prompt (str): The role of the model as specified by the prompt.
            bdd_chunks (Any): The database or chunks of information used in the retrieval process.
            max_tokens (int): Maximum number of tokens to generate.
            temperature (int): The temperature setting for the generative model.
            top_n (int, optional): The number of top documents to retrieve. Defaults to 2.
        """
        self.llm = generation_model
        self.bdd = bdd_chunks
        self.top_n = top_n
        self.role_prompt = role_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.latency = 0.0
        self.input_tokens = 0
        self.output_tokens = 0
        self.dollor_cost = 0.0

    def get_cosim(self, a: NDArray[np.float32], b: NDArray[np.float32]) -> float:
        """
        Calculates the cosine similarity between two vectors.

        Args:
            a (NDArray[np.float32]): The first vector.
            b (NDArray[np.float32]): The second vector.

        Returns:
            float: The cosine similarity between the two vectors.
        """

        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def get_top_similarity(
            self,
            embedding_query: NDArray[np.float32],
            embedding_chunks: NDArray[np.float32],
            corpus: list[str],
        ) -> list[str]:
            """
            Retrieves the top N most similar documents from the corpus based on the query's embedding.

            Args:
                embedding_query (NDArray[np.float32]): The embedding of the query.
                embedding_chunks (NDArray[np.float32]): A NumPy array of embeddings for the documents in the corpus.
                corpus (List[str]): A list of documents (strings) corresponding to the embeddings in `embedding_chunks`.
                top_n (int, optional): The number of top similar documents to retrieve. Defaults to 5.

            Returns:
                List[str]: A list of the most similar documents from the corpus, ordered by similarity to the query.
            """
            cos_dist_list = np.array(
                [
                    self.get_cosim(embedding_query, embed_doc)
                    for embed_doc in embedding_chunks
                ]
            )
            indices_of_max_values = np.argsort(cos_dist_list)[-self.top_n :][::-1]
            print(indices_of_max_values)
            return [corpus[i] for i in indices_of_max_values]


    def build_prompt(
        self, context: list[str], history: str, query: str
    ) -> list[dict[str, str]]:
        """
        Builds a prompt string for a conversational agent based on the given context and query.

        Args:
            context (str): The context information, typically extracted from books or other sources.
            query (str): The user's query or question.

        Returns:
            list[dict[str, str]]: The RAG prompt in the OpenAI format
        """
        context_joined = "\n".join(context)
        system_prompt = self.role_prompt
        history_prompt = f"""
        # Historique de conversation:
        {history}
        """
        context_prompt = f"""
        Tu disposes de la section "Contexte" pour t'aider à répondre aux questions.
        # Contexte: 
        {context_joined}
        """
        query_prompt = f"""
        # Question:
        {query}

        # Réponse:
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": history_prompt},
            {"role": "system", "content": context_prompt},
            {"role": "user", "content": query_prompt},
        ]



    def _generate(self, prompt_dict: list[dict[str, str]]) -> litellm.ModelResponse:


         

        response = litellm.completion(
            model=f"mistral/{self.llm}",
            messages=prompt_dict,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )  # type: ignore

        return response



    def call_model(self, prompt_dict: list[dict[str, str]]) -> str:
        """
        Calls the LLM with the given prompt and returns the response.

        Args:
            prompt_dict (List[Dict[str, str]]): A list of dictionaries where each dictionary represents
                                                a message prompt with a string key and string value.

        Returns:
            str: The response generated by the LLM.
        """

        start_time = time.process_time()
        chat_response: str = self._generate(prompt_dict=prompt_dict)
        end_time = time.process_time()
        self.latency = end_time - start_time

        self.input_tokens = chat_response.usage.prompt_tokens
        self.output_tokens = chat_response.usage.completion_tokens
    

        dict_response = {
            "response": chat_response.choices[0].message.content,
            "latency": self.latency,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "llm": self.llm,           
        }
        return dict_response
        # return str(chat_response.choices[0].message.content)


    def __call__(self, query: str, history: dict[str, str]) -> str:
        """
        Process a query and return a response based on the provided history and database.

        This method performs the following steps:
        1. Queries the ChromaDB instance to retrieve relevant documents based on the input query.
        2. Constructs a prompt using the retrieved documents, the provided query, and the history.
        3. Sends the prompt to the model for generating a response.

        Args:
            query (str): The user query to be processed.
            history (dict[str, str]): A dictionary containing the conversation history,
                where keys represent user inputs and values represent corresponding responses.

        Returns:
            str: The generated response from the model.
        """
        chunks = self.bdd.chroma_db.query(
            query_texts=[query],
            n_results=self.top_n,
        )
        chunks_list: list[str] = chunks["documents"][0]
        prompt_rag = self.build_prompt(
            context=chunks_list, history=str(history), query=query
        )
        response = self.call_model(prompt_dict=prompt_rag)
        return response


# generation_model = "ministral-8b-latest"
# role_prompt = "Tu es un assistant virtuel qui aide les utilisateurs à répondre à des questions."
# bdd_chunks = BDDChunks(embedding_model="paraphrase-xlm-r-multilingual-v1", path="./")
# max_tokens = 100
# temperature = 0.5

# # Initialize the SimpleRAG instance
# simple_rag = AugmentedRAG(
#     generation_model=generation_model,
#     role_prompt=role_prompt,
#     bdd_chunks=bdd_chunks,
#     max_tokens=max_tokens,
#     temperature=temperature,

# )

# # Define the conversation history
# history = {
#     "user": "Quelle est la capitale de la France ?",
#     "bot": "La capitale de la France est Paris.",
# }

# # Define the user query
# query = "LE RESTAURANT  AVEC LE PLUS DE  COMMENTAIRE "
# bdd_chunks._create_collection(path="./")

# # Generate a response using the SimpleRAG instance
# response = simple_rag(query=query, history=history)
# print(response)
