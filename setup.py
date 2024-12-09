from setuptools import setup, find_packages

setup(
    name='spanda_dissertation_analysis',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'fastapi==0.115.0',
        'uvicorn==0.31.0',
        'httpx==0.27.2',
        'asyncio',
        'pydantic==2.9.2',
        'langchain-core==0.3.6',
        'langchain==0.3.1',
        'langchain-ollama==0.2.0',
        'PyMuPDF==1.24.10',
        'python-docx==1.1.2',  # Updated to correct library
        'pytesseract==0.3.13',
        'Pillow==10.4.0',
        'requests==2.32.3',
        "python-dotenv",
        "PyPDF2",
        "websockets",
        "python-multipart",
        "python-docx",
        "pdf2image",
        "sqlalchemy",
        "pymysql",
        "aiokafka",
        "kafka-python",
        "psycopg2",
        "pymysql",
        "mysql-connector-python",
        "cryptography",
    ],
    entry_points={
        'console_scripts': [
            "da-start = backend.src.main:main"  # Use the new run_server function
        ],
    },
)
