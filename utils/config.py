from dotenv import load_dotenv
from langchain_groq.chat_models import ChatGroq
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_openai.chat_models import ChatOpenAI


load_dotenv()


llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.78,
)


class State(TypedDict):
    messages: Annotated[list, add_messages]


config={"configurable": {"thread_id": "1"}}


