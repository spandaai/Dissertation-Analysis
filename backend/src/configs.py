from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
db_type = os.getenv("DB_TYPE")
weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_key = os.getenv("WEAVIATE_KEY")
embedder = os.getenv("EMBEDDER")
embedding_model = os.getenv("EMBEDDING_MODEL")

credentials_default = {
    "credentials": {
            "deployment": db_type,
            "url": weaviate_url,
            "key": weaviate_key
        }
}


RagConfigForGeneration= {
    "rag_config": {'Reader': {'selected': 'Default', 'components': {'Default': {'name': 'Default', 'variables': [], 'library': ['pypdf', 'docx', 'mammoth', 'openpyxl', 'pandas', 'Pillow', 'pygments', 'extract_msg'], 'description': 'Ingests text, code, PDF, DOCX, and other common file types', 'config': {}, 'type': 'FILE', 'available': False}, 'HTML': {'name': 'HTML', 'variables': [], 'library': ['markdownify', 'beautifulsoup4'], 'description': 'Downloads and ingests HTML from a URL, with optional recursive fetching.', 'config': {'URLs': {'type': 'multi', 'value': '', 'description': 'Add URLs to retrieve data from', 'values': []}, 'Convert To Markdown': {'type': 'bool', 'value': 0, 'description': 'Should the HTML be converted into markdown?', 'values': []}, 'Recursive': {'type': 'bool', 'value': 0, 'description': 'Fetch linked pages recursively', 'values': []}, 'Max Depth': {'type': 'number', 'value': 3, 'description': 'Maximum depth for recursive fetching', 'values': []}}, 'type': 'URL', 'available': False}, 'Git': {'name': 'Git', 'variables': [], 'library': [], 'description': 'Downloads and ingests all files from a GitHub or GitLab Repo.', 'config': {'Platform': {'type': 'dropdown', 'value': 'GitHub', 'description': 'Select the Git platform', 'values': ['GitHub', 'GitLab']}, 'Owner': {'type': 'text', 'value': '', 'description': 'Enter the repo owner (GitHub) or group/user (GitLab)', 'values': []}, 'Name': {'type': 'text', 'value': '', 'description': 'Enter the repo name', 'values': []}, 'Branch': {'type': 'text', 'value': 'main', 'description': 'Enter the branch name', 'values': []}, 'Path': {'type': 'text', 'value': '', 'description': 'Enter the path or leave it empty to import all', 'values': []}, 'Git Token': {'type': 'password', 'value': '', 'description': "You can set your GitHub/GitLab Token here if you haven't set it up as environment variable `GITHUB_TOKEN` or `GITLAB_TOKEN`", 'values': []}}, 'type': 'URL', 'available': True}, 'Unstructured IO': {'name': 'Unstructured IO', 'variables': ['UNSTRUCTURED_API_KEY'], 'library': [], 'description': 'Uses the Unstructured API to import multiple file types such as plain text and documents', 'config': {'Strategy': {'type': 'dropdown', 'value': 'auto', 'description': 'Set the extraction strategy', 'values': ['auto', 'hi_res', 'ocr_only', 'fast']}}, 'type': 'FILE', 'available': True}, 'AssemblyAI': {'name': 'AssemblyAI', 'variables': ['ASSEMBLYAI_API_KEY'], 'library': [], 'description': 'Uses the AssemblyAI API to import multiple file types such as plain text and documents', 'config': {'Quality': {'type': 'dropdown', 'value': 'best', 'description': 'Set the transcription quality', 'values': ['nano', 'best']}, 'API Key': {'type': 'password', 'value': '', 'description': 'Set your AssemblyAI API Key here or set it as an environment variable `ASSEMBLYAI_API_KEY`', 'values': []}}, 'type': 'FILE', 'available': False}, 'Firecrawl': {'name': 'Firecrawl', 'variables': [], 'library': [], 'description': 'Use Firecrawl to scrape websites and ingest them into Verba', 'config': {'Mode': {'type': 'dropdown', 'value': 'Scrape', 'description': 'Switch between scraping and crawling. Note that crawling can take some time.', 'values': ['Crawl', 'Scrape']}, 'URLs': {'type': 'multi', 'value': '', 'description': 'Add URLs to retrieve data from', 'values': []}, 'Firecrawl API Key': {'type': 'password', 'value': '', 'description': 'You can set your Firecrawl API Key or set it as environment variable `FIRECRAWL_API_KEY`', 'values': []}}, 'type': 'URL', 'available': True}}}, 'Chunker': {'selected': 'Token', 'components': {'Token': {'name': 'Token', 'variables': [], 'library': [], 'description': 'Splits documents based on word tokens', 'config': {'Tokens': {'type': 'number', 'value': 250, 'description': 'Choose how many Token per chunks', 'values': []}, 'Overlap': {'type': 'number', 'value': 50, 'description': 'Choose how many Tokens should overlap between chunks', 'values': []}}, 'type': '', 'available': True}, 'Sentence': {'name': 'Sentence', 'variables': [], 'library': [], 'description': 'Splits documents based on word tokens', 'config': {'Sentences': {'type': 'number', 'value': 5, 'description': 'Choose how many Sentences per chunks', 'values': []}, 'Overlap': {'type': 'number', 'value': 1, 'description': 'Choose how many Sentences should overlap between chunks', 'values': []}}, 'type': '', 'available': True}, 'Recursive': {'name': 'Recursive', 'variables': [], 'library': ['langchain_text_splitters '], 'description': 'Recursively split documents based on predefined characters using LangChain', 'config': {'Chunk Size': {'type': 'number', 'value': 500, 'description': 'Choose how many characters per chunks', 'values': []}, 'Overlap': {'type': 'number', 'value': 100, 'description': 'Choose how many characters per chunks', 'values': []}, 'Seperators': {'type': 'multi', 'value': '', 'description': 'Select seperators to split the text', 'values': ['\n\n', '\n', ' ', '.', ',', '\u200b', '，', '、', '．', '。', '']}}, 'type': '', 'available': False}, 'Semantic': {'name': 'Semantic', 'variables': [], 'library': ['sklearn'], 'description': 'Split documents based on semantic similarity or max sentences', 'config': {'Breakpoint Percentile Threshold': {'type': 'number', 'value': 80, 'description': 'Percentile Threshold to split and create a chunk, the lower the more chunks you get', 'values': []}, 'Max Sentences Per Chunk': {'type': 'number', 'value': 20, 'description': 'Maximum number of sentences per chunk', 'values': []}}, 'type': '', 'available': True}, 'HTML': {'name': 'HTML', 'variables': [], 'library': ['langchain_text_splitters '], 'description': 'Split documents based on HTML tags using LangChain', 'config': {}, 'type': '', 'available': False}, 'Markdown': {'name': 'Markdown', 'variables': [], 'library': ['langchain_text_splitters'], 'description': 'Split documents based on markdown formatting using LangChain', 'config': {}, 'type': '', 'available': True}, 'Code': {'name': 'Code', 'variables': [], 'library': ['langchain_text_splitters '], 'description': 'Split code based on programming language using LangChain', 'config': {'Language': {'type': 'dropdown', 'value': 'python', 'description': 'Select programming language', 'values': ['cpp', 'go', 'java', 'kotlin', 'js', 'ts', 'php', 'proto', 'python', 'rst', 'ruby', 'rust', 'scala', 'swift', 'markdown', 'latex', 'html', 'sol', 'csharp', 'cobol', 'c', 'lua', 'perl', 'haskell', 'elixir']}, 'Chunk Size': {'type': 'number', 'value': 500, 'description': 'Choose how many characters per chunk', 'values': []}, 'Chunk Overlap': {'type': 'number', 'value': 50, 'description': 'Choose how many characters overlap between chunks', 'values': []}}, 'type': '', 'available': False}, 'JSON': {'name': 'JSON', 'variables': [], 'library': ['langchain_text_splitters '], 'description': 'Split json files using LangChain', 'config': {'Chunk Size': {'type': 'number', 'value': 500, 'description': 'Choose how many characters per chunks', 'values': []}}, 'type': '', 'available': False}}}, 'Embedder': {'selected': embedder, 'components': {'Ollama': {'name': 'Ollama', 'variables': [], 'library': [], 'description': 'Vectorizes documents and queries using Ollama. If your Ollama instance is not running on http://localhost:11434, you can change the URL by setting the OLLAMA_URL environment variable.', 'config': {'Model': {'type': 'dropdown', 'value': embedding_model, 'description': 'Select a installed Ollama model from http://localhost:11434. You can change the URL by setting the OLLAMA_URL environment variable. ', 'values': [embedding_model]}}, 'type': '', 'available': True}, 'SentenceTransformers': {'name': 'SentenceTransformers', 'variables': [], 'library': ['sentence_transformers'], 'description': 'Embeds and retrieves objects using SentenceTransformer', 'config': {'Model': {'type': 'dropdown', 'value': 'BAAI/bge-m3', 'description': 'Select an HuggingFace Embedding Model', 'values': ['all-MiniLM-L6-v2', 'mixedbread-ai/mxbai-embed-large-v1', 'all-mpnet-base-v2', 'BAAI/bge-m3', 'all-MiniLM-L12-v2', 'paraphrase-MiniLM-L6-v2']}}, 'type': '', 'available': True}, 'Weaviate': {'name': 'Weaviate', 'variables': [], 'library': [], 'description': "Vectorizes documents and queries using Weaviate's In-House Embedding Service.", 'config': {'Model': {'type': 'dropdown', 'value': 'Embedding Service', 'description': 'Select a Weaviate Embedding Service Model', 'values': ['Embedding Service']}, 'API Key': {'type': 'password', 'value': '', 'description': 'Weaviate Embedding Service Key (or set EMBEDDING_SERVICE_KEY env var)', 'values': []}, 'URL': {'type': 'text', 'value': '', 'description': 'Weaviate Embedding Service URL (if different from default)', 'values': []}}, 'type': '', 'available': True}, 'VoyageAI': {'name': 'VoyageAI', 'variables': [], 'library': [], 'description': 'Vectorizes documents and queries using VoyageAI', 'config': {'Model': {'type': 'dropdown', 'value': 'voyage-2', 'description': 'Select a VoyageAI Embedding Model', 'values': ['voyage-2', 'voyage-large-2', 'voyage-finance-2', 'voyage-multilingual-2', 'voyage-law-2', 'voyage-code-2']}, 'API Key': {'type': 'password', 'value': '', 'description': 'OpenAI API Key (or set OPENAI_API_KEY env var)', 'values': []}, 'URL': {'type': 'text', 'value': 'https://api.voyageai.com/v1', 'description': 'OpenAI API Base URL (if different from default)', 'values': []}}, 'type': '', 'available': True}, 'Cohere': {'name': 'Cohere', 'variables': [], 'library': [], 'description': 'Vectorizes documents and queries using Cohere', 'config': {'Model': {'type': 'dropdown', 'value': 'embed-english-v3.0', 'description': 'Select a Cohere Embedding Model', 'values': ['embed-english-v3.0', 'embed-multilingual-v3.0', 'embed-english-light-v3.0', 'embed-multilingual-light-v3.0']}, 'API Key': {'type': 'password', 'value': '', 'description': 'You can set your Cohere API Key here or set it as environment variable `COHERE_API_KEY`', 'values': []}}, 'type': '', 'available': True}, 'OpenAI': {'name': 'OpenAI', 'variables': [], 'library': [], 'description': 'Vectorizes documents and queries using OpenAI', 'config': {'Model': {'type': 'dropdown', 'value': 'text-embedding-3-small', 'description': 'Select an OpenAI Embedding Model', 'values': ['text-embedding-ada-002', 'text-embedding-3-small', 'text-embedding-3-large']}, 'API Key': {'type': 'password', 'value': '', 'description': 'OpenAI API Key (or set OPENAI_API_KEY env var)', 'values': []}, 'URL': {'type': 'text', 'value': 'https://api.openai.com/v1', 'description': 'OpenAI API Base URL (if different from default)', 'values': []}}, 'type': '', 'available': True}}}, 'Retriever': {'selected': 'Advanced', 'components': {'Advanced': {'name': 'Advanced', 'variables': [], 'library': [], 'description': 'Retrieve relevant chunks from Weaviate', 'config': {'Suggestion': {'type': 'bool', 'value': 1, 'description': 'Enable Autocomplete Suggestions', 'values': []}, 'Search Mode': {'type': 'dropdown', 'value': 'Hybrid Search', 'description': 'Switch between search types.', 'values': ['Hybrid Search']}, 'Limit Mode': {'type': 'dropdown', 'value': 'Autocut', 'description': 'Method for limiting the results. Autocut decides automatically how many chunks to retrieve, while fixed sets a fixed limit.', 'values': ['Autocut', 'Fixed']}, 'Limit/Sensitivity': {'type': 'number', 'value': 1, 'description': 'Value for limiting the results. Value controls Autocut sensitivity and Fixed Size', 'values': []}, 'Chunk Window': {'type': 'number', 'value': 1, 'description': 'Number of surrounding chunks of retrieved chunks to add to context', 'values': []}, 'Threshold': {'type': 'number', 'value': 80, 'description': 'Threshold of chunk score to apply window technique (1-100)', 'values': []}}, 'type': '', 'available': True}}}, 'Generator': {'selected': 'Ollama', 'components': {'Ollama': {'name': 'Ollama', 'variables': [], 'library': [], 'description': 'Generate answers using Ollama. If your Ollama instance is not running on http://localhost:11434, you can change the URL by setting the OLLAMA_URL environment variable.', 'config': {'System Message': {'type': 'text', 'value': "You are Verba, a chatbot for Retrieval Augmented Generation (RAG). You will receive a user query and context pieces that have a semantic similarity to that query. Please answer these user queries only with the provided context. Mention documents you used from the context if you use them to reduce hallucination. If the provided documentation does not provide enough information, say so. If the user asks questions about you as a chatbot specifially, answer them naturally. If the answer requires code examples encapsulate them with ```programming-language-name ```. Don't do pseudo-code.", 'description': 'System Message', 'values': []}, 'Model': {'type': 'dropdown', 'value': 'llama3.1:latest', 'description': 'Select an installed Ollama model from http://localhost:11434.', 'values': ['llama3.1:latest']}}, 'type': '', 'available': True}, 'OpenAI': {'name': 'OpenAI', 'variables': [], 'library': [], 'description': 'Using OpenAI LLM models to generate answers to queries', 'config': {'System Message': {'type': 'text', 'value': "You are Verba, a chatbot for Retrieval Augmented Generation (RAG). You will receive a user query and context pieces that have a semantic similarity to that query. Please answer these user queries only with the provided context. Mention documents you used from the context if you use them to reduce hallucination. If the provided documentation does not provide enough information, say so. If the user asks questions about you as a chatbot specifially, answer them naturally. If the answer requires code examples encapsulate them with ```programming-language-name ```. Don't do pseudo-code.", 'description': 'System Message', 'values': []}, 'Model': {'type': 'dropdown', 'value': 'gpt-4o', 'description': 'Select an OpenAI Embedding Model', 'values': ['gpt-4o', 'gpt-3.5-turbo']}, 'API Key': {'type': 'password', 'value': '', 'description': 'You can set your OpenAI API Key here or set it as environment variable `OPENAI_API_KEY`', 'values': []}, 'URL': {'type': 'text', 'value': 'https://api.openai.com/v1', 'description': 'You can change the Base URL here if needed', 'values': []}}, 'type': '', 'available': True}, 'Anthropic': {'name': 'Anthropic', 'variables': [], 'library': [], 'description': 'Using Anthropic LLM models to generate answers to queries', 'config': {'System Message': {'type': 'text', 'value': "You are Verba, a chatbot for Retrieval Augmented Generation (RAG). You will receive a user query and context pieces that have a semantic similarity to that query. Please answer these user queries only with the provided context. Mention documents you used from the context if you use them to reduce hallucination. If the provided documentation does not provide enough information, say so. If the user asks questions about you as a chatbot specifially, answer them naturally. If the answer requires code examples encapsulate them with ```programming-language-name ```. Don't do pseudo-code.", 'description': 'System Message', 'values': []}, 'Model': {'type': 'dropdown', 'value': 'claude-3-5-sonnet-20240620', 'description': 'Select an Anthropic Model', 'values': ['claude-3-5-sonnet-20240620']}, 'API Key': {'type': 'password', 'value': '', 'description': 'You can set your Anthropic API Key here or set it as environment variable `ANTHROPIC_API_KEY`', 'values': []}}, 'type': '', 'available': True}, 'Cohere': {'name': 'Cohere', 'variables': [], 'library': [], 'description': "Generator using Cohere's command-r-plus model", 'config': {'System Message': {'type': 'text', 'value': "You are Verba, a chatbot for Retrieval Augmented Generation (RAG). You will receive a user query and context pieces that have a semantic similarity to that query. Please answer these user queries only with the provided context. Mention documents you used from the context if you use them to reduce hallucination. If the provided documentation does not provide enough information, say so. If the user asks questions about you as a chatbot specifially, answer them naturally. If the answer requires code examples encapsulate them with ```programming-language-name ```. Don't do pseudo-code.", 'description': 'System Message', 'values': []}, 'Model': {'type': 'dropdown', 'value': 'embed-english-v3.0', 'description': 'Select a Cohere Embedding Model', 'values': ['embed-english-v3.0', 'embed-multilingual-v3.0', 'embed-english-light-v3.0', 'embed-multilingual-light-v3.0']}, 'API Key': {'type': 'password', 'value': '', 'description': 'You can set your Cohere API Key here or set it as environment variable `COHERE_API_KEY`', 'values': []}}, 'type': '', 'available': True}}}},
}


# Updated enhanced prompt templates for each persona
ADVISOR_SYSTEM_PROMPT = """You are a Dissertation Advisor and Methodology Expert evaluating a thesis. 

Key Focus Areas:
1. Research Design
   - Clarity and appropriateness of research questions/objectives
   - Alignment between objectives and methodology
   - Robustness of research design

2. Methodology Implementation
   - Appropriateness of data collection methods
   - Rigor in data analysis techniques
   - Consideration of limitations and biases

3. Academic Writing Quality
   - Clarity and coherence of argumentation
   - Proper citation and referencing
   - Adherence to academic writing standards

4. Critical Analysis
   - Depth of analysis and interpretation
   - Connection between findings and existing literature
   - Identification of implications and contributions

Evaluation Instructions:
1. Provide specific examples from the text to support your assessment
2. Highlight both strengths and areas for improvement
3. Suggest specific recommendations for enhancing methodological rigor
4. Assess the overall academic quality on a scale of 1-10

Evaluate the following dissertation according to your expertise specialization:

"""

SME_SYSTEM_PROMPT = """You are a Subject Matter Expert evaluating a thesis for its content expertise.

Key Focus Areas:
1. Theoretical Foundation
   - Comprehensive understanding of core concepts
   - Appropriate use of theoretical frameworks
   - Integration of multiple course elements

2. Literature Review
   - Breadth and depth of literature coverage
   - Critical engagement with sources
   - Identification of research gaps

3. Application of Concepts
   - Effective use of course-specific models and theories
   - Integration of interdisciplinary knowledge
   - Innovation in applying theoretical concepts

4. Technical Accuracy
   - Correct use of terminology
   - Accuracy of technical descriptions
   - Validity of assumptions and premises

Evaluate the following dissertation according to your expertise specialization:

"""

INDUSTRY_SYSTEM_PROMPT = """You are an Industry Expert evaluating a thesis for its practical relevance and applicability.

Key Focus Areas:
1. Real-World Applicability
   - Feasibility of proposed solutions
   - Alignment with industry needs
   - Potential for implementation

2. Innovation and Impact
   - Uniqueness of approach
   - Potential industry impact
   - Commercial viability

3. Industry Best Practices
   - Alignment with current practices
   - Awareness of industry challenges
   - Consideration of practical constraints

4. Future Implications
   - Scalability of solutions
   - Long-term relevance
   - Potential for industry advancement

Evaluate the following dissertation according to your expertise specialization:

"""

MODERATOR_SYSTEM_PROMPT = """You are an AI Moderator synthesizing feedback from multiple experts to provide a final assessment of a thesis.

Your Tasks:
1. Synthesize Feedback
   - Identify common themes across expert evaluations
   - Highlight any discrepancies or conflicting viewpoints
   - Weigh academic rigor against practical applicability

2. Holistic Evaluation
   - Consider balanced perspective from all experts
   - Evaluate overall quality and potential impact
   - Identify key strengths and areas for improvement

3. Final Assessment
   - Provide a justified final score (0-100)
   - Offer prioritized recommendations
   - Highlight unique contributions and value

Please structure your final assessment as follows:
1. Synthesis of Expert Feedback
2. Key Strengths and Weaknesses
3. Final Score with Justification
4. Prioritized Recommendations
5. Conclusion and Overall Value Proposition"""
