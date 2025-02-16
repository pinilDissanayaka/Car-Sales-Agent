from database.database import Base, engine
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from schema import ChatRequest, ChatResponse
from agent import graph
from utils import config


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        responses = []

        async for chunk in graph.astream(
            {
                "messages": [("human", request.message)],
            },
            stream_mode="values",
            config=config,
        ):
            if chunk["messages"]:
                responses.append(chunk["messages"][-1].content)
        
        # Get final response
        final_response = responses[-1] if responses else "Please Try again later"
        

        return ChatResponse(
            response=final_response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/health")
async def health_check():
    return {"status": "healthy"}



if __name__ == "__main__":
    Base.metadata.create_all(engine)
    uvicorn.run(app, port=8000)