from utils import llm, State, config
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from node.database import get_car_details
from node.negotiation import get_negotiation_strategy, calculate_payment_options
from langgraph.prebuilt import ToolNode


tools = [
    get_car_details
]

tool_node = ToolNode(tools)

graph_builder = StateGraph(State)

def agent(state: State):
    message = state["messages"]

    llm_with_tools=llm.bind_tools(tools=tools)

    prompt_template = """
    You are a professional car sales representative for ABC company. Use your negotiation tools wisely to:
        1. Understand customer needs and budget
        2. Provide relevant car information
        3. Handle price negotiations professionally
        4. Calculate and present payment options
        5. Close deals when appropriate

    Remember to:
        - Be professional and courteous
        - Use the negotiation tools when discussing prices
        - Present payment options clearly
        - Focus on value rather than just price
        - Build rapport with the customer
    
    Current question:
        {QUESTION}
    """

    prompt = ChatPromptTemplate.from_template(prompt_template)

    chain = (
        {"QUESTION": RunnablePassthrough()} |
        prompt |
        llm_with_tools
    )

    response = chain.invoke({
        "QUESTION": message
    })

    return {"messages": [response]}


def should_continue(state: State):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END


graph_builder.add_node("agent", agent)
graph_builder.add_node("tools", tool_node)



graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges("agent", should_continue, ["tools", END])
graph_builder.add_edge("tools", "agent")


memory = MemorySaver()


graph = graph_builder.compile(checkpointer=memory)


def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]},
                              config=config):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break






