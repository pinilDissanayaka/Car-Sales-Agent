from langchain_community.utilities import SQLDatabase
from typing_extensions import TypedDict
from langchain import hub
from typing_extensions import Annotated
import os
from dotenv import load_dotenv
from langchain_groq.chat_models import ChatGroq
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from utils import llm
from langchain_core.tools import tool
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())



@tool
def get_car_details(question: str) -> str:
    """
    Retrieves car details based on a user's question by constructing and executing an SQL query.

    Args:
        question (str): The user's question about car details.

    Returns:
        str: The response generated from the queried information.
    """
    # Establish a connection to the database
    db = SQLDatabase.from_uri(os.getenv("DATABASE_URL"))

    class QueryOutput(TypedDict):
        """Generated SQL query."""
        query: Annotated[str, ..., "Syntactically valid SQL query."]

    # Pull the query prompt template from the hub
    query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

    # Ensure the prompt template contains exactly one message
    assert len(query_prompt_template.messages) == 1

    # Invoke the prompt template with the necessary parameters
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 10,
            "table_info": db.get_table_info(),
            "input": question,
        }
    )

    # Use the language model to generate a structured SQL query
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)

    # Execute the generated SQL query
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    result = execute_query_tool.invoke(result)

    # Formulate a response using the retrieved SQL result
    answer_prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f'Question: {question}\n'
        f'SQL Result: {result}\n'
        "When making answer, dont include sql query and min_price. Always use market_price."
    )
    response = llm.invoke(answer_prompt)

    return response.content



