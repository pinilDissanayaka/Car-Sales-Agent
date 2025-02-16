import os
from dotenv import load_dotenv
from langchain_groq.chat_models import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from typing_extensions import TypedDict, Annotated, Union
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_openai.chat_models import ChatOpenAI


load_dotenv()


llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.78,

)



