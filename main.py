from typing import Literal
from utils import llm
from node.database import get_car_details
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langgraph.prebuilt import ToolNode



tools = [get_car_details]
tool_node = ToolNode(tools)

model_with_tools=llm.bind_tools(tools=tools)


def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END


def call_model(state: MessagesState):
    messages = state["messages"]
    prompt_template="""
    You are a sales representative for a car dealership at ABC company.
    {QUESTION}
    """

    prompt  = ChatPromptTemplate.from_template(prompt_template)

    chain=(
        {"QUESTION" : RunnablePassthrough()} |
        prompt |
        model_with_tools
    )


    response = chain.invoke({"QUESTION" : messages})

    return {"messages": [response]}


workflow = StateGraph(MessagesState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

app = workflow.compile()


while True:
    question=input("Enter your question: ")
    for chunk in app.stream(
        {"messages": [("human", question)]}, stream_mode="values"
    ):
        chunk["messages"][-1].pretty_print()