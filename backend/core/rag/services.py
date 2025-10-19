from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from django.conf import settings
import openai

from ..models import Video

CHROMA_DATA_PATH = "chroma_data/"
CHROMA_COLLECTION_NAME = "seahawks_transcripts"

def create_video_embeddings(video_id: int):
    """
    Develops a set of embeddings that wrap around the video transcript text.
    """

    try:
        video = Video.objects.get(id=video_id)
        if not video.transcript_data or 'segments' not in video.transcript_data:
            print(f"RAG Service: Video {video_id} has no transcript data. Skipping embedding.")
            return

        # Combine all text segments into a single block of text.
        full_transcript_text = " ".join(seg['text'].strip() for seg in video.transcript_data['segments'] if seg['text'])

        if not full_transcript_text:
            print(f"RAG Service: Transcript for Video {video_id} is empty. Skipping embedding.")
            return

        # Chunk the text using LangChain's text splitter.
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,      # The size of each chunk in characters.
            chunk_overlap=200,    # The number of characters to overlap between chunks.
            length_function=len
        )
        chunks = text_splitter.split_text(full_transcript_text)
        print(f"RAG Service: Split transcript for Video {video_id} into {len(chunks)} chunks.")

        # Load the free, local embedding model from HuggingFace. It's crucial to use the
        # exact same model for indexing and querying.
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        embedding_model = HuggingFaceEmbeddings(model_name=model_name)

        # Generate vector embeddings and populate ChromaDB accordingly.
        vector_store = Chroma.from_texts(texts=chunks, embedding=embedding_model, 
                                         metadatas=[{"video_id": video_id} for _ in chunks],
                                         persist_directory=CHROMA_DATA_PATH,
                                         collection_name=CHROMA_COLLECTION_NAME)
        vector_store.persist()
        print(f"RAG Service (Chroma): Successfully saved {len(chunks)} chunks to ChromaDB.")

    except Video.DoesNotExist:
        print(f"ERROR: Video with ID {video_id} not found.")
    except Exception as e:
        print(f"ERROR: An unexpected RAG Error occurred for Video ID {video_id}: {e}!")


def answer_question(question: str) -> dict:
    """
    Performs the full RAG pipeline to answer a user's question.
    1. Embeds the user's question into a vector.
    2. Retrieves the most relevant transcript chunks from the database using vector similarity search.
    3. Augments a prompt with the retrieved context.
    4. Generates a final, synthesized answer using a powerful LLM.
    """

    print(f"RAG Service: Received question: '{question}'")

    # Use the exact same embedding model as in the indexing step.
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    
    # Load the persisted Chroma database from disk, now we have context from the DB!
    vector_store = Chroma(
        persist_directory=CHROMA_DATA_PATH, 
        embedding_function=embedding_model,
        collection_name=CHROMA_COLLECTION_NAME
    )

    # Perform a semantic search to load relevant sources/chunks.
    relevant_chunks = vector_store.similarity_search(question, k=3)
    if not relevant_chunks:
        return {"answer": "I couldn't find any relevant information to answer that.", "sources": []}
    
    context = "\n\n---\n\n".join([doc.page_content for doc in relevant_chunks])
    
    # Extract the video IDs from the metadata we stored; this helps us clarify our sources.
    source_video_ids = sorted(list(set([doc.metadata.get('video_id', 'Unknown') for doc in relevant_chunks])))
    sources = [f"Video ID: {vid}" for vid in source_video_ids]
    
    prompt = f"""
    You are an expert AI assistant and sports analyst for the Seattle Seahawks. Your task is to answer the user's 
    question in a natural, conversational tone, based ONLY on the provided context from press conference transcripts. 

    ---

    Context:
    {context}
    
    Question:
    {question}

    ---

    INSTRUCTIONS:
    1.  Synthesize a clear and concise answer from the provided context.
    2.  DO NOT say "According to the context," "Based on the information provided," or any similar phrases. 
        Just answer the question directly!
    3.  If the answer is not found in the context, you MUST respond with: "I couldn't find specific information 
        about that in the press conferences."
    """
    
    # Craft a final coherent answer with an LLM call.
    client = openai.OpenAI(api_key=settings.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    response = client.chat.completions.create(model="llama-3.3-70b-versatile", 
                                              messages=[{"role": "user", "content": prompt}])
    answer = response.choices[0].message.content

    # Return the RAG work in JSON format.
    return {"answer": answer, "sources": sources}
