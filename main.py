from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from typing import Literal
from utils import llm
from node.database import get_car_details
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langgraph.prebuilt import ToolNode
from datetime import datetime
import uuid
from node.negotiation import get_negotiation_strategy, calculate_payment_options

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: str

class Message(BaseModel):
    role: str
    content: str
    timestamp: str

class Conversation(BaseModel):
    messages: List[Message]

# In-memory storage for chat histories
chat_histories: Dict[str, List[Message]] = {}

# Initialize the workflow
tools = [
    get_car_details,
    get_negotiation_strategy,
    calculate_payment_options
]

tool_node = ToolNode(tools)
model_with_tools = llm.bind_tools(tools=tools)

def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

def call_model(state: MessagesState):
    messages = state["messages"]
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
    
    Previous conversation:
    {HISTORY}
    
    Current question:
    {QUESTION}
    """

    prompt = ChatPromptTemplate.from_template(prompt_template)

    chain = (
        {"QUESTION": RunnablePassthrough(), "HISTORY": RunnablePassthrough()} |
        prompt |
        model_with_tools
    )

    response = chain.invoke({
        "QUESTION": messages,
        "HISTORY": state.get("history", "No previous conversation")
    })
    return {"messages": [response]}

# Initialize workflow graph
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

app_workflow = workflow.compile()

def get_conversation_history(conversation_id: str) -> str:
    """Format conversation history for the model."""
    if conversation_id not in chat_histories:
        return ""
    
    history = chat_histories[conversation_id]
    formatted_history = "\n".join([
        f"{msg.role}: {msg.content}"
        for msg in history
    ])
    return formatted_history

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Generate new conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Initialize conversation history if it doesn't exist
        if conversation_id not in chat_histories:
            chat_histories[conversation_id] = []
        
        # Add user message to history
        timestamp = datetime.now().isoformat()
        chat_histories[conversation_id].append(
            Message(
                role="user",
                content=request.message,
                timestamp=timestamp
            )
        )
        
        # Get formatted history for context
        history = get_conversation_history(conversation_id)
        
        # Process the message through the workflow
        responses = []
        async for chunk in app_workflow.astream(
            {
                "messages": [("human", request.message)],
                "history": history
            },
            stream_mode="values"
        ):
            if chunk["messages"]:
                responses.append(chunk["messages"][-1].content)
        
        # Get final response
        final_response = responses[-1] if responses else "No response generated"
        
        # Add assistant response to history
        chat_histories[conversation_id].append(
            Message(
                role="assistant",
                content=final_response,
                timestamp=datetime.now().isoformat()
            )
        )
        
        return ChatResponse(
            response=final_response,
            conversation_id=conversation_id,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)