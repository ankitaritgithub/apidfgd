import ast
import asyncio
import json
import os
from autogen import ChatResult
import requests
import websockets
from utils.logger import logger
from agent.agent import general_agent
from dotenv import load_dotenv

load_dotenv()

def extract_content_from_chat_result(chat_result):
    """
    Extracts the user message, assistant message, and download URL from the chat result.
    
    Args:
        chat_result: The raw chat result from the agent.
    
    Returns:
        dict: A dictionary containing the extracted content.
    """
    if isinstance(chat_result, ChatResult):
        chat_history = chat_result.chat_history
        summary = chat_result.summary

        user_message = None
        assistant_message = None
        download_url = None

        # Process the chat history in reverse order to get the most recent user-assistant pair
        for msg in reversed(chat_history):
            # Skip tool calls, we don't want them in the final assistant message
            if "tool_calls" in msg:
                continue

            if msg.get('role') == 'user' and not user_message:
                user_message = msg.get('content', None)
            elif msg.get('role') == 'assistant' and not assistant_message:
                assistant_message = msg.get('content', None)

                # If the assistant's message contains a download URL, capture it
                if isinstance(assistant_message, dict) and "download_url" in assistant_message:
                    download_url = assistant_message["download_url"]

            # If both messages have been captured, exit the loop
            if user_message and assistant_message:
                break

        if user_message and assistant_message:
            return {
                "user_message": user_message,
                "assistant_message": assistant_message,
                "download_url": download_url
            }
        else:
            logger.warning("User or assistant message not found in chat history.")
            return {"error": "Messages not found in chat history."}

    # Handle the case where chat_result is a string or dict
    elif isinstance(chat_result, str):
        try:
            chat_result = ast.literal_eval(chat_result)
        except (ValueError, SyntaxError) as e:
            logger.error(f"Failed to parse chat result: {e}")
            return {"error": "Failed to parse chat result"}

        if isinstance(chat_result, dict):
            chat_history = chat_result.get('chat_history', [])
            if isinstance(chat_history, list):
                user_message = None
                assistant_message = None
                download_url = None

                # Process the chat history in reverse order to get the most recent user-assistant pair
                for msg in reversed(chat_history):
                    # Skip tool calls
                    if "tool_calls" in msg:
                        continue
                    
                    if msg.get('role') == 'user' and not user_message:
                        user_message = msg.get('content', None)
                    elif msg.get('role') == 'assistant' and not assistant_message:
                        assistant_message = msg.get('content', None)

                        # Extract the download URL if present
                        if isinstance(assistant_message, dict) and "download_url" in assistant_message:
                            download_url = assistant_message["download_url"]

                    if user_message and assistant_message:
                        break

                if user_message and assistant_message:
                    return {
                        "user_message": user_message,
                        "assistant_message": assistant_message,
                        "download_url": download_url
                    }
                else:
                    logger.warning("User or assistant message not found in chat history.")
                    return {"error": "Messages not found in chat history."}

            logger.warning("Chat history is missing or not in the expected structure.")
            return {"error": "No valid chat history found."}

    logger.error("Unexpected structure encountered: Neither string nor dict.")
    return {"error": "Unexpected response structure."}

# Function to send data via WebSocket to another FastAPI service (APITestingAgent, GUITestingAgent)
async def send_websocket_request(data: dict, uri: str) -> str:
    """Sends WebSocket data to the specified endpoint and returns the response."""
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(data))  # Send JSON payload
            
            # Log to verify if we are connected
            logger.debug(f"Connected to {uri}, sending data...")
            
            # Receive response from WebSocket server
            response = await websocket.recv()
            return response
    except Exception as e:
        logger.debug(f"Error during WebSocket request: {e}")
        return f"Error during WebSocket request: {e}"

# Function to classify and route task based on message content (direct routing, no orchestrator)
async def route_task_to_agent(message: str, message_data: dict, agent_name: str):
    """Route the task directly to the appropriate agent."""
    
    # Check for keywords to decide which agent should handle the task
    # if "API" in message or "Swagger" in message:  # API testing task
    if agent_name == 'api':
        logger.debug("API agent")

        # WebSocket URL for API testing agent
        API_TESTING_AGENT = os.getenv("API_TESTING_AGENT_URL")

        logger.debug(f"API_TESTING_AGENT_URL -> {API_TESTING_AGENT}")

        try:
            # Connect to the WebSocket server with custom ping interval (to keep the connection alive)
            async with websockets.connect(API_TESTING_AGENT, ping_interval=30, ping_timeout=20) as websocket:
                logger.debug("WebSocket connection established")

                # Send message data as JSON
                await websocket.send(json.dumps(message_data))

                # Now continuously receive messages in a loop
                while True:
                    try:
                        # This awaits and receives the response from the agent
                        response = await asyncio.wait_for(websocket.recv(), timeout=60)
                        logger.debug("---------Response from agent API testing----------")
                        logger.debug(response)
                        logger.debug("---------Response from agent API testing----------")

                        return response, "APITestingAgent"
                    except asyncio.TimeoutError:
                        logger.error("Timeout: No response received from agent API testing in time")
                        return "Timeout Error: No response", "APITestingAgent"
                    except websockets.exceptions.ConnectionClosed:
                        logger.error("Connection closed unexpectedly")
                        return "Connection closed unexpectedly", "APITestingAgent"

        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            return f"WebSocket error: {e}", "APITestingAgent"

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"Unexpected error: {e}", "APITestingAgent"
        
    elif agent_name == 'gui':  # GUI testing task
        # selected_agent = guitesting_agent

        logger.debug("GUI agent")
        # URL of your local FastAPI endpoint
        GUI_TESTING_AGENT = os.getenv("GUI_TESTING_AGENT_URL")
        
        # Example request body (TestRequest)
        request_data = {
            "prompt": f"{message_data}"  # Your test message prompt
        }
        
        logger.debug("Request ->>>>>>>>>>>>>>>>>>>>>>>>>> ")
        logger.debug(request_data)
        logger.debug("Request ->>>>>>>>>>>>>>>>>>>>>>>>>> ")

        # Make the POST request with the JSON data
        response = requests.post(GUI_TESTING_AGENT, json=request_data)
        
        logger.debug("Response ->>>>>>>>>>>>>>>>>>>>>>>>>> ")
        logger.debug(response.json())
        logger.debug("Response ->>>>>>>>>>>>>>>>>>>>>>>>>> ")

        # Check if the response is successful (status code 200)
        if response.status_code == 200:

            response = response.json()
            logger.debug("Response from /run_tests:", response)
        else:
            logger.debug("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ Not 200 response")
            logger.debug(f"Failed to make the request. Status code: {response.status_code}")
            logger.debug("Response text:", response.text)

        return response, "GUITestingAgent"

    else:  # General task or unknown task
        # selected_agent = general_agent
        result = general_agent.initiate_chat(
            general_agent, 
            message=message,  # Pass the message for general task
            max_turns=1,
            clear_history=False
        )
        # Extract and validate the response from the agent
        response_data = extract_content_from_chat_result(result)
        
        # Logging the extracted content
        logger.debug("----------------------------look down------------------------------------")
        logger.debug(response_data)
        logger.debug("----------------------------look up------------------------------------")
        if "error" in response_data:
            # Send error response back to the client
            await websocket.send_text(json.dumps({"error": response_data["error"]}))
            return

        # Return result and agent name
        return response_data, "GeneralAgent"
    
def parse_json_to_structure(data):
    # Initialize variables to store the latest assistant message and its index
    latest_assistant_message = None
    latest_assistant_index = -1
    
    # Iterate through the messages to find the latest 'assistant' message
    for index, message in enumerate(data.get('messages', [])):
        if message.get('role') == 'assistant':
            latest_assistant_message = message
            latest_assistant_index = index
    
    # If no 'assistant' message is found, return None
    if latest_assistant_message is None:
        return None
    
    # Prepare the chat history with the latest assistant message
    chat_history = data['messages'][:latest_assistant_index + 1]
    
    # Construct the final response structure
    response = {
        'chat_id': data.get('thread_id'),
        'chat_history': chat_history,
        'download_url': data.get('download_url')
    }
    
    return response
