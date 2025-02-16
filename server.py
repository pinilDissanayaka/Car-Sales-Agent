from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        question = await websocket.receive_text()  # Receive message from client
        response = 
        await websocket.send_text(response)  # Send response back to client