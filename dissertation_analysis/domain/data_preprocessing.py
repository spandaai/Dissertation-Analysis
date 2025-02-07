"""
Text Chunking Utility Module

A simple utility module that provides functions for chunking and word extraction 
from text using LangChain's recursive splitter.

Functions:
1. chunk_text:
  - Splits text into semantic chunks
  - Uses LangChain's RecursiveCharacterTextSplitter
  - Returns chunks with word counts
  - Configurable chunk size

2. get_first_n_words:
  - Extracts first N words from text
  - Simple space-based word splitting
  - Returns concatenated string

Dependencies:
- langchain_text_splitters: For RecursiveCharacterTextSplitter

Note: This is a utility module focused solely on text chunking and word 
extraction operations. Used primarily for preprocessing text before analysis.
"""


from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text, chunk_size=1000):
    """
    Splits text into semantic chunks using LangChain's RecursiveCharacterTextSplitter,
    maintaining similar output format as the original function.
    
    Args:
        text (str): The input text to be chunked
        chunk_size (int): Target size for each chunk in words (approximate)
        
    Returns:
        list: List of tuples (chunk_text, actual_chunk_size)
    """
    # Initialize the text splitter
    # Using average word length of 5 characters + 1 for space to convert words to chars
    chars_per_chunk = chunk_size * 6
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chars_per_chunk,
        chunk_overlap=0,  # Some overlap to maintain context
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    # Split the text
    raw_chunks = text_splitter.split_text(text)
    
    # Convert to required format with word counts
    chunks = []
    for chunk in raw_chunks:
        word_count = len(chunk.split())
        chunks.append((chunk, word_count))
    
    return chunks

def get_first_n_words(text, n):
    # Split the text into words
    words = text.split()
    # Get the first 500 words
    first_n_words = words[:n]
    # Join them back into a string
    return " ".join(first_n_words)
