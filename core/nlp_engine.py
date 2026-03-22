# core/nlp_engine.py
# Analytiq — Plain English → SQL → Answer (Groq)

import os
import pandas as pd
import sqlalchemy
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY") or "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"


def load_data_to_sqlite(csv_path: str, table_name: str = "data"):
    df     = pd.read_csv(csv_path)
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    df.to_sql(table_name, engine, index=False, if_exists="replace")
    return engine, df.columns.tolist()


def english_to_sql(question: str, schema: str) -> str:
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=GROQ_KEY)
    prompt = f"""You are an expert SQL analyst. Convert the question to a valid SQLite query.

Schema:
{schema}

Rules:
- Return ONLY raw SQL, no markdown, no backticks, no explanation.
- Use SQLite syntax.
- Use meaningful column aliases when aggregating.
- Limit to 20 rows unless asked otherwise.

Question: {question}

SQL:"""
    response = llm.invoke(prompt)
    sql = response.content.strip()
    if "```" in sql:
        sql = sql.split("```")[1]
        if sql.startswith("sql"): sql = sql[3:]
    return sql.strip()


def results_to_english(question: str, sql: str, results: pd.DataFrame) -> str:
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3, api_key=GROQ_KEY)
    results_str = results.to_string(index=False) if len(results) <= 20 else results.head(20).to_string(index=False)
    prompt = f"""You are a business analyst presenting findings to a non-technical executive.

Question: {question}
SQL: {sql}
Results:
{results_str}

Write a clear, concise, professional 2-3 sentence answer in plain English.
Focus on the business insight, not technical details."""
    response = llm.invoke(prompt)
    return response.content.strip()


def query(question: str, csv_path: str) -> dict:
    engine, columns = load_data_to_sqlite(csv_path)
    schema_desc     = f"Table: data\nColumns: {', '.join(columns)}"
    sql             = english_to_sql(question, schema_desc)
    try:
        with engine.connect() as conn:
            results = pd.read_sql_query(sqlalchemy.text(sql), conn)
        answer = results_to_english(question, sql, results)
        return {"question": question, "sql": sql, "results": results, "answer": answer, "error": None}
    except Exception as e:
        return {"question": question, "sql": sql, "results": None, "answer": None, "error": str(e)}
