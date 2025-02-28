from typing import List
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
import json
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from utils.utils import hash_password, verify_password, create_access_token
from db import models, schemas
from db.db import get_db, init_db
from sqlalchemy.orm import Session
from utils.logger import logger
from agent.agent import orchestrate_task, general_agent
from agent.helpers import extract_content_from_chat_result, route_task_to_agent, parse_json_to_structure

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Add CORSMiddleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to allow specific origins as necessary
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods, including WebSocket
    allow_headers=["*"],  # Allow all headers
)

init_db()

@app.get("/users", response_model=List[schemas.UserOut])
def get_users(db: Session = Depends(get_db)):
    # Query to fetch all users from the database
    users = db.query(models.User).all()

    # If no users are found, raise an exception
    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    return users

@app.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user.password)
    
    # Create new user instance
    new_user = models.User(email=user.email, hashed_password=hashed_password)

    # Add new user to session and commit to DB
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Refresh to get user with assigned ID
    
    return new_user

@app.post("/login", response_model=schemas.Token)
def login(user: schemas.LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    if db_user is None:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Create a JWT token
    access_token = create_access_token(data={"sub": db_user.email})
    
    return {"access_token": access_token, "token_type": "bearer"}

# WebSocket endpoint for communication with frontend agentqa
@app.websocket("/ws/agentqa")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()  # Accept the WebSocket connection
    logger.info("WebSocket connection established")  # Log when WebSocket connection is established

    try:
        while True:    
            # Receive the task message from the frontend
            message = await websocket.receive_text()
            logger.debug(f"Received message: {message}")  # Log the received message
            
            # Parse the message into a Python dictionary
            message_data = json.loads(message)

            # Ensure the received message has a prompt (task description)
            if "prompt" in message_data:
                prompt = message_data["prompt"]
                
                res = orchestrate_task(prompt)
                resp = extract_content_from_chat_result(res)
                agent_name = resp['assistant_message']

                logger.debug("----------------------------orchestrate_task down------------------------------------")
                logger.debug(type(resp['assistant_message']))
                logger.debug(resp)
                logger.debug("----------------------------orchestrate_task up--------------------------------------")

                # Route the task to the appropriate agent and get the result
                result, agent = await route_task_to_agent(prompt,message_data, agent_name)

                logger.debug("----------------------------look agent down------------------------------------")
                logger.debug(agent)
                logger.debug("----------------------------look agent up--------------------------------------")

                logger.debug("----------------------------look result down------------------------------------")
                logger.debug(result)
                logger.debug("----------------------------look result up--------------------------------------")

                # Handle file generation (e.g., Newman HTML report or CSV)
                download_url = "newman-report.html"  # Example, replace with actual URL if generated

                if agent == "GeneralAgent": 

                    logger.debug("****************Inside GeneralAgent*********************")

                    # Prepare chat history and summary
                    chat_history = [
                        {"content": prompt, "role": "user", "name": agent},
                        {"content": result["assistant_message"], "role": "assistant", "name": agent}
                    ]

                    # Prepare the final response with chat history and download URL
                    response_payload = {
                        "chat_id": None,  # Can be updated if required
                        "chat_history": chat_history,
                        "download_url": download_url
                    }
                    # Send the structured response back to the frontend
                    await websocket.send_text(json.dumps(response_payload))
                    logger.info(f"Task result sent to frontend: {response_payload}")

                elif agent == "GUITestingAgent":

                    logger.debug("*******************************Inside GUITestingAgent*********************************************")

                    result = parse_json_to_structure(result)

                    logger.debug("----------------------------parse_json_to_structure------------------------------------")
                    logger.debug(result)
                    logger.debug
                    ("----------------------------parse_json_to_structure--------------------------------------")
                    await websocket.send_text(json.dumps(result))
                    logger.info(f"Task result sent to frontend: {result}")

                else:
                    logger.debug("****************Inside else*********************")
                    # Send the structured response back to the frontend
                    await websocket.send_text(result)
                    logger.info(f"Task result sent to frontend: {result}")

            else:
                # If the received message doesn't have a 'prompt', send an error message
                await websocket.send_text("Invalid message structure. Ensure the JSON contains 'prompt'.")
                logger.warning("Invalid message structure received")  # Log warning for invalid message structure

    except WebSocketDisconnect:
        # Handle client disconnect
        logger.info("Client disconnected")  # Log when client disconnects
        print("Client disconnected")
        try:
            # Reset chat history
            result = general_agent.initiate_chat(general_agent, message="", max_turns=1, clear_history=True)
            logger.debug(f"Chat history has been reset: {result}")
        except Exception as e:
            logger.error(f"Error resetting chat history: {str(e)}")
            await websocket.send_text(json.dumps({"error": "Failed to reset chat history upon disconnection."}))
    except Exception as e:
        # Log any unexpected errors
        logger.error(f"Unexpected error: {str(e)}")
        await websocket.send_text(json.dumps({"error": "An unexpected error occurred. Please try again."}))

# Run the FastAPI app using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
