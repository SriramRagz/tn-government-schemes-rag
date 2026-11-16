
"""
Tamil Nadu Government Schemes - Knowledge Graph RAG

Architecture:
FAQ.txt -> Python Parser -> Neo4j Knowledge Graph
        -> Graph Search -> LangChain -> OpenAI

Graph structure:
(Topic)-[:HAS_FAQ]->(FAQ)-[:HAS_ANSWER]->(Answer)
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate


# --------------------------------------------------
# STEP 1: Load environment variables
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def validate_environment():
    required_variables = {
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "NEO4J_URI": NEO4J_URI,
        "NEO4J_USERNAME": NEO4J_USERNAME,
        "NEO4J_PASSWORD": NEO4J_PASSWORD,
    }

    missing = [
        name for name, value in required_variables.items()
        if not value or value.startswith("replace_with_")
    ]

    if missing:
        raise ValueError(
            "Missing or incomplete environment variables: "
            + ", ".join(missing)
            + ". Please check your local .env file."
        )


# --------------------------------------------------
# STEP 2: Read and parse FAQ.txt
# --------------------------------------------------

def parse_faq(file_path: str) -> list[dict]:
    """Read Q: and A: pairs from the FAQ text file."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"FAQ file not found: {path}")

    content = path.read_text(encoding="utf-8")
    blocks = content.split("Q:")

    faqs = []

    for block in blocks:
        block = block.strip()

        if not block or "A:" not in block:
            continue

        question, answer = block.split("A:", 1)

        question = question.strip()
        answer = answer.strip()

        if question and answer:
            faqs.append({
                "question": question,
                "answer": answer
            })

    if not faqs:
        raise ValueError(
            "No valid FAQ entries found. "
            "Check that FAQ.txt uses Q: and A: format."
        )

    print(f"Parsed {len(faqs)} FAQ entries.")
    return faqs


# --------------------------------------------------
# STEP 3: Create the Knowledge Graph in Neo4j
# --------------------------------------------------

def extract_topic(question: str) -> str:
    """Extract a simple topic from the question."""

    topic = question.strip()

    for prefix in ["What is an ", "What is a ", "What is "]:
        if topic.lower().startswith(prefix.lower()):
            topic = topic[len(prefix):]
            break

    return topic.rstrip("?").strip()


def push_faqs_to_graph(driver, faqs: list[dict]):
    """
    Create or reuse Topic, FAQ and Answer nodes.

    MERGE prevents duplicate nodes and relationships
    when the same FAQ file is ingested again.
    """

    cypher = """
        MERGE (t:Topic {name: $topic})
        MERGE (q:FAQ {question: $question})
        MERGE (a:Answer {text: $answer})
        MERGE (t)-[:HAS_FAQ]->(q)
        MERGE (q)-[:HAS_ANSWER]->(a)
    """

    with driver.session() as session:
        for faq in faqs:
            topic = extract_topic(faq["question"])

            session.run(
                cypher,
                topic=topic,
                question=faq["question"],
                answer=faq["answer"]
            )

    print(f"Loaded {len(faqs)} FAQs into Neo4j.")


# --------------------------------------------------
# STEP 4: Search the Knowledge Graph
# --------------------------------------------------

def search_graph(driver, user_query: str) -> list[dict]:
    """
    Find relevant FAQ entries using keyword matching
    and a simple relevance score.
    """

    stop_words = {
        "what", "is", "a", "an", "the", "how", "does",
        "do", "can", "tell", "me", "about", "explain",
        "define", "i", "want", "to", "know", "of",
        "in", "for", "and", "or", "it", "on", "with",
        "from", "are", "was", "were", "this", "that",
        "which", "who", "when", "where", "why"
    }

    words = re.findall(r"\w+", user_query.lower())

    # Remove common words and very short words.
    keywords = list(dict.fromkeys(
        word for word in words
        if word not in stop_words and len(word) > 2
    ))

    if not keywords:
        return []

    cypher = """
        MATCH (t:Topic)-[:HAS_FAQ]->(q:FAQ)-[:HAS_ANSWER]->(a:Answer)

        WITH t, q, a, $keywords AS keywords

        WITH t, q, a,
             [keyword IN keywords
              WHERE toLower(q.question) CONTAINS keyword
                 OR toLower(t.name) CONTAINS keyword
                 OR toLower(a.text) CONTAINS keyword
             ] AS matched_keywords

        WHERE size(matched_keywords) > 0

        RETURN
            t.name AS topic,
            q.question AS question,
            a.text AS answer,
            size(matched_keywords) AS relevance_score

        ORDER BY relevance_score DESC

        LIMIT 3
    """

    with driver.session() as session:
        records = session.run(cypher, keywords=keywords)

        results = []

        for record in records:
            results.append({
                "topic": record["topic"],
                "question": record["question"],
                "answer": record["answer"],
                "relevance_score": record["relevance_score"]
            })

    return results


# --------------------------------------------------
# STEP 5: Create the LangChain + OpenAI RAG chain
# --------------------------------------------------

def create_rag_chain():
    """Create the language model chain."""

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=OPENAI_API_KEY
    )

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are a helpful Tamil Nadu Government Schemes assistant.

Use ONLY the information provided in the Knowledge Graph context.

Knowledge Graph Context:
{context}

User Question:
{question}

Instructions:
- Answer only using the supplied context.
- Do not invent scheme names, benefits, eligibility or procedures.
- If the context does not contain the answer, clearly say:
  "I don't have this information in my knowledge graph."
- Respond in English.
- Keep the answer clear and concise.

Answer:"""
    )

    return prompt | llm


# --------------------------------------------------
# STEP 6: Retrieve information and generate an answer
# --------------------------------------------------

def ask_question(driver, chain, user_question: str) -> str:
    """Run the complete Knowledge Graph RAG pipeline."""

    results = search_graph(driver, user_question)

    if results:
        context_parts = []

        for result in results:
            context_parts.append(
                f"Topic: {result['topic']}\n"
                f"Question: {result['question']}\n"
                f"Answer: {result['answer']}"
            )

        context = "\n\n".join(context_parts)

    else:
        context = "(No relevant information found in the Knowledge Graph)"

    print(f"\n[Graph Search] Found {len(results)} relevant entries.")

    response = chain.invoke({
        "context": context,
        "question": user_question
    })

    return response.content


# --------------------------------------------------
# STEP 7: Main application
# --------------------------------------------------

def main():

    print("=" * 60)
    print("  Tamil Nadu Government Schemes - Knowledge Graph RAG")
    print("  LangChain + Neo4j + OpenAI")
    print("=" * 60)

    validate_environment()

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )

    try:
        # Connect to Neo4j
        print("\n[1/3] Connecting to Neo4j...")

        driver.verify_connectivity()

        print("Connected successfully!")

        # Load FAQ data
        print("\n[2/3] Loading FAQ.txt into Knowledge Graph...")

        faq_file = PROJECT_DIR / "FAQ.txt"
        faqs = parse_faq(faq_file)

        push_faqs_to_graph(driver, faqs)

        # Create RAG chain
        print("\n[3/3] Setting up LangChain + OpenAI...")

        chain = create_rag_chain()

        print("RAG chain ready!")

        # Interactive chatbot
        print("\n" + "=" * 60)
        print("  Tamil Nadu Government Schemes Assistant")
        print("  Ask questions in English.")
        print("  Type 'quit' or 'exit' to stop.")
        print("=" * 60)

        while True:

            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("\nGoodbye!")
                break

            try:
                answer = ask_question(
                    driver,
                    chain,
                    user_input
                )

                print(f"\nAssistant: {answer}")

            except Exception as error:
                print(f"\nUnable to process your question: {error}")

    except Exception as error:
        print(f"\nApplication error: {error}")

    finally:
        driver.close()
        print("\nNeo4j connection closed.")


if __name__ == "__main__":
    main()
