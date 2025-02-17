from utils import llm, State, config
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from node.database import get_car_details
from node.negotiation import get_negotiation_strategy, calculate_payment_options
from langgraph.prebuilt import ToolNode
from database.database import engine, Base, session
from database.models import Cars


tools = [
    get_car_details,
    get_negotiation_strategy,

]

tool_node = ToolNode(tools)

graph_builder = StateGraph(State)

def agent(state: State):
    message = state["messages"]

    llm_with_tools=llm.bind_tools(tools=tools)

    prompt_template = """
    You are a professional car sales representative for ABC company. Your role is to assist customers by:  
        1. Understanding their needs and budget.  
        2. Providing relevant car information.  
        3. Handling price negotiations professionally.  
        4. Calculating and presenting payment options.  
        5. Closing deals when appropriate.  

    Guidelines:  
        - Be professional and courteous.  
        - Use negotiation tools effectively when discussing prices.  
        - Present payment options clearly.  
        - Focus on value rather than just price.  
        - Build rapport with the customer.  

    Customer: {QUESTION}
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
    for event in graph.astream({"messages": [{"role": "user", "content": user_input}]},
                              config=config):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


if __name__ == "__main__":
    Base.metadata.create_all(engine)

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






