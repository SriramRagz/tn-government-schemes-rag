# Tamil Nadu Government Schemes – Knowledge Graph RAG Assistant

An AI-powered question-answering prototype that uses a Neo4j Knowledge Graph and Retrieval-Augmented Generation (RAG) to answer questions about Tamil Nadu government schemes.

The application retrieves relevant information from a structured FAQ knowledge base and uses OpenAI to generate answers grounded in the retrieved content.

## Project Overview

This project demonstrates how Knowledge Graph RAG can be used to make government scheme information easier to access through natural-language questions.

Users can ask questions in English about the information available in the knowledge base.

## Technology Stack

- Python 3.13
- Neo4j Aura – Graph database
- LangChain – LLM integration and prompt management
- OpenAI GPT-4o-mini – Answer generation
- Neo4j Python Driver
- python-dotenv – Environment configuration

## Architecture

The application follows this workflow:

1. FAQ data is loaded from `FAQ.txt`.
2. Questions, answers and topics are stored in Neo4j as graph nodes and relationships.
3. A user's question is processed using keyword-based graph retrieval.
4. Relevant FAQ information is retrieved from Neo4j.
5. The retrieved information is passed to OpenAI through LangChain.
6. The chatbot generates an answer using the available context.

### Knowledge Graph Structure

- Topic → FAQ → Answer
- `HAS_FAQ` relationship connects Topic and FAQ.
- `HAS_ANSWER` relationship connects FAQ and Answer.

## Project Structure

```text
TN_Government_Schemes_RAG/
│
├── FAQ.txt
├── kg_rag.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
├── ingestion/
│   └── discover_departments.py
│
└── data/
    ├── raw/
    └── processed/
```

## Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/SriramRagz/tn-government-schemes-rag.git
cd tn-government-schemes-rag
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create your local environment file:

```bash
cp .env.example .env
```

Add your own OpenAI API key and Neo4j Aura credentials to `.env`.

Required variables:

- `OPENAI_API_KEY`
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`

Never upload `.env` or share your API keys and database passwords.

### 5. Run the application

```bash
python kg_rag.py
```

Ask questions in English through the terminal.

Type `quit` or `exit` to close the application.

## Current Capabilities

- FAQ-based government scheme information retrieval.
- Knowledge Graph creation using Neo4j.
- Topic, FAQ and Answer relationships.
- Keyword-based graph retrieval.
- Context-grounded AI answer generation.
- Basic handling of questions for which information is unavailable.

## Current Limitations

This is a working prototype, not a complete government scheme advisory platform.

- The knowledge base contains a limited set of manually prepared FAQs.
- Retrieval currently uses keyword matching, not vector similarity.
- The application supports English questions and answers only.
- Automated web scraping and live government data updates are not implemented.
- Scheme eligibility and application details should be verified with the relevant government department.

## Data Sources

The FAQ knowledge base uses information prepared from official Tamil Nadu Government agriculture department and district administration sources.

Users should verify current scheme guidelines, eligibility, benefits and application requirements with the relevant government department.

## Reference Implementation

This project follows the basic Knowledge Graph RAG approach demonstrated in:

[KG-rag-mac – Knowledge Graph RAG](https://github.com/manojkanur/KG-rag-mac)

## Project Status

Working prototype – core Knowledge Graph ingestion, retrieval and AI answer generation have been implemented and tested.

## License

No license has been selected yet. Refer to the source implementation and data-source terms before redistributing third-party material.
