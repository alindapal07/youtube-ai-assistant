# ============================================================
# STEP 1: IMPORT REQUIRED LIBRARIES
# ============================================================

# Import the os module to access environment variables.
import os

# Import load_dotenv to load variables from a .env file.
from dotenv import load_dotenv

# Import YouTubeTranscriptApi to fetch YouTube video transcripts.
from youtube_transcript_api import YouTubeTranscriptApi

# Import exceptions to handle specific YouTube transcript errors.
from youtube_transcript_api._errors import (
    TranscriptsDisabled,  # Raised when transcripts are disabled.
    NoTranscriptFound,  # Raised when the requested transcript is unavailable.
    VideoUnavailable,  # Raised when the video is unavailable.
)

# Import Document to store text and associated metadata.
from langchain_core.documents import Document

# Import RecursiveCharacterTextSplitter to divide text into smaller chunks.
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import HuggingFaceEmbeddings to convert text into numerical vectors.
from langchain_huggingface import HuggingFaceEmbeddings

# Import FAISS to create a searchable vector store.
from langchain_community.vectorstores import FAISS

# Import ChatGroq to interact with a Groq-hosted language model.
from langchain_groq import ChatGroq

# Import ChatPromptTemplate to create a reusable prompt template.
from langchain_core.prompts import ChatPromptTemplate

# Import StrOutputParser to convert the model output into a string.
from langchain_core.output_parsers import StrOutputParser

# ============================================================
# STEP 2: LOAD ENVIRONMENT VARIABLES
# ============================================================

# Load variables defined in the .env file into the environment.
load_dotenv()

# Retrieve the Groq API key from the environment.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Stop execution if the API key is missing.
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Add it to your .env file.")


# ============================================================
# STEP 3: DEFINE THE YOUTUBE VIDEO ID
# ============================================================

# Store the unique ID of the YouTube video.
video_id = "Gfr50f6ZBvo"

# Construct the complete YouTube video URL using the video ID.
video_url = f"https://www.youtube.com/watch?v={video_id}"


# ============================================================
# STEP 4: FETCH THE YOUTUBE TRANSCRIPT
# ============================================================


def load_youtube_transcript(video_id: str) -> Document:
    """
    Fetch the English transcript of a YouTube video.

    Args:
        video_id: The unique identifier of the YouTube video.

    Returns:
        A LangChain Document containing the transcript and metadata.
    """

    # Create an instance of the YouTube Transcript API client.
    api = YouTubeTranscriptApi()

    try:
        # Fetch the transcript, preferring English.
        # The result contains individual transcript snippets.
        transcript_list = api.fetch(video_id, languages=["en"])

        # Extract the text from every snippet.
        # Join the snippets into one continuous string.
        transcript_text = " ".join(snippet.text for snippet in transcript_list)

        # Check whether the resulting transcript contains text.
        if not transcript_text.strip():
            raise ValueError("The fetched transcript is empty.")

        # Display a success message after fetching the transcript.
        print("Transcript fetched successfully!")

        # Create a LangChain Document from the transcript text.
        document = Document(
            # Store the complete transcript in page_content.
            page_content=transcript_text,
            # Store information that identifies the source video.
            metadata={
                "video_id": video_id,
                "source": video_url,
            },
        )

        # Return the document to the calling function.
        return document

    # Handle videos whose transcripts are disabled.
    except TranscriptsDisabled as e:
        raise RuntimeError("Transcripts are disabled for this video.") from e

    # Handle cases where no matching English transcript is available.
    except NoTranscriptFound as e:
        raise RuntimeError("No English transcript was found for this video.") from e

    # Handle videos that cannot be accessed.
    except VideoUnavailable as e:
        raise RuntimeError("The YouTube video is unavailable.") from e


# ============================================================
# STEP 5: LOAD THE TRANSCRIPT DOCUMENT
# ============================================================

try:
    # Call the function to fetch the transcript and create a Document.
    document = load_youtube_transcript(video_id)

    # Put the document inside a list.
    # LangChain document splitters and vector stores accept lists
    # of Document objects.
    documents = [document]

# Handle transcript-loading errors before continuing.
except Exception as e:
    # Print the error message for troubleshooting.
    print(f"Error loading transcript: {e}")

    # Stop the program because the transcript is required for RAG.
    raise SystemExit(1)


# ============================================================
# STEP 6: SPLIT THE DOCUMENT INTO SMALLER CHUNKS
# ============================================================

# Create a text splitter to divide long text into manageable pieces.
splitter = RecursiveCharacterTextSplitter(
    # Set the approximate maximum size of each chunk in characters.
    chunk_size=1000,
    # Preserve 200 characters between consecutive chunks.
    # This helps retain context across chunk boundaries.
    chunk_overlap=200,
)

# Split the document into multiple smaller Document objects.
# The metadata is preserved in the resulting chunks.
splitted_text = splitter.split_documents(documents)

# Stop if splitting produced no chunks.
if not splitted_text:
    raise SystemExit("No text chunks were created.")

# Display the number of chunks created.
print(f"Total chunks created: {len(splitted_text)}")


# ============================================================
# STEP 7: INITIALIZE THE HUGGING FACE EMBEDDING MODEL
# ============================================================

# Display a message while the embedding model is being loaded.
print("\nLoading Hugging Face embedding model...")

# Initialize a sentence-transformer embedding model.
# This model converts text into numerical vectors.
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Confirm that the embedding model has been initialized.
print("Embedding model loaded successfully!")


# ============================================================
# STEP 8: CREATE THE FAISS VECTOR STORE
# ============================================================

# Display a message before generating embeddings and building the index.
print("\nCreating FAISS vector store...")

# Convert the text chunks into embeddings and index them using FAISS.
vector_store = FAISS.from_documents(
    # Supply the list of transcript chunks.
    documents=splitted_text,
    # Supply the embedding model used to vectorize each chunk.
    embedding=embeddings,
)

# Confirm that the vector store has been created.
print("FAISS vector store created successfully!")

# Display the number of vectors stored in the FAISS index.
print(f"Total vectors stored: {vector_store.index.ntotal}")


# ============================================================
# STEP 9: CREATE A RETRIEVER
# ============================================================

# Convert the vector store into a retriever.
# A retriever searches for transcript chunks relevant to a question.
retriever = vector_store.as_retriever(
    # Use Maximal Marginal Relevance to balance relevance and diversity.
    search_type="mmr",
    # Configure the retriever's search behavior.
    search_kwargs={
        # Return four selected chunks to provide context to the LLM.
        "k": 4,
        # Consider up to 20 candidate chunks during retrieval.
        "fetch_k": 20,
        # Balance similarity to the query with diversity.
        # 0.5 gives equal weight to both objectives.
        "lambda_mult": 0.5,
    },
)

# Confirm that the retriever is ready.
print("Retriever created successfully!")


# ============================================================
# STEP 10: CONFIGURE THE GROQ LANGUAGE MODEL
# ============================================================

# Initialize the Groq chat model.
llm = ChatGroq(
    # Specify the model to use.
    # Confirm that this model is available to your Groq account.
    model="openai/gpt-oss-20b",
    # Set temperature to zero for more consistent responses.
    temperature=0,
    # Provide the API key loaded from the .env file.
    api_key=GROQ_API_KEY,
)


# ============================================================
# STEP 11: CREATE THE RAG PROMPT TEMPLATE
# ============================================================

# Define the instructions that will be sent to the language model.
prompt = ChatPromptTemplate.from_template("""
    You are a YouTube video assistant.

    Answer the user's question using only the provided
    transcript context.

    Instructions:
    - Give accurate and relevant answers.
    - Do not invent information that is absent from the context.
    - If the context does not contain enough information,
      clearly state that the transcript does not provide the answer.
    - Explain technical concepts clearly when relevant.

    Transcript Context:
    {context}

    Question:
    {question}

    Answer:
    """)

# The {context} placeholder will receive retrieved transcript chunks.
# The {question} placeholder will receive the user's question.


# ============================================================
# STEP 12: BUILD THE RAG CHAIN
# ============================================================

# Connect the prompt, language model, and output parser.
# The pipe operator (|) passes the output of each component
# into the next component.
chain = prompt | llm | StrOutputParser()

# The resulting workflow is:
# Question + Context -> Prompt -> Groq LLM -> String Answer


# ============================================================
# STEP 13: CREATE THE QUESTION-ANSWERING FUNCTION
# ============================================================


def answer_question(question: str) -> str:
    """
    Answer a question using the YouTube transcript.

    Args:
        question: The user's question about the video.

    Returns:
        The language model's answer as a string.
    """

    # Search the FAISS vector store for relevant transcript chunks.
    # The retriever returns a list of LangChain Document objects.
    relevant_docs = retriever.invoke(question)

    # Check whether any relevant documents were retrieved.
    if not relevant_docs:
        return "No relevant transcript content was found."

    # Extract the text from the retrieved documents.
    # Combine the chunks into one context string.
    context = "\n\n".join(doc.page_content for doc in relevant_docs)

    # Send the retrieved context and user question through the RAG chain.
    answer = chain.invoke(
        {
            # Supply the transcript context to the prompt.
            "context": context,
            # Supply the user's question to the prompt.
            "question": question,
        }
    )

    # Return the generated answer.
    return answer


# ============================================================
# STEP 14: CREATE AN INTERACTIVE CHAT LOOP
# ============================================================

# Print a heading when the chatbot is ready.
print("\n" + "=" * 50)
print("YouTube Video RAG Chatbot is Ready!")
print("=" * 50)

# Display the source video.
print(f"Video URL: {video_url}")

# Explain how to interact with the chatbot.
print("Ask questions about the video.")
print("Type 'exit' or 'quit' to stop the chatbot.")


# Continue accepting questions until the user exits.
while True:

    # Read a question from the terminal.
    # strip() removes unnecessary spaces at the beginning and end.
    question = input("\nAsk a question about the video: ").strip()

    # Exit the loop when the user enters an exit command.
    if question.lower() in {"exit", "quit"}:
        print("Chatbot closed. Goodbye!")
        break

    # Do not process empty questions.
    if not question:
        print("Please enter a question.")
        continue

    try:
        # Retrieve context and generate the answer.
        answer = answer_question(question)

        # Display the answer.
        print("\nAnswer:")
        print(answer)

    # Handle errors during retrieval or answer generation.
    except Exception as e:
        # Print the error without terminating the entire chat loop.
        print(f"\nError generating answer: {e}")
