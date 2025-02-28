import os
from autogen import ChatResult, ConversableAgent

# Load environment variables for LLM configuration
config_list = [
    {
        "model": "llama-3.2-90b-vision-preview",  # Example model, replace if necessary
        "api_key": os.getenv("GROQ_API_KEY"),  # Ensure your API key is loaded from environment
        "api_type": "groq",  # Using the Groq API type
        "temperature": 0,  # For deterministic results (adjust as needed)
    }
]

# Master Orchestrator Agent
orchestrator = ConversableAgent(
    name="Orchestrator",
    system_message="I decide which agent is best suited to handle a given task. "
    "Return 'TERMINATE' when the task is done.",
    llm_config={"config_list": config_list},
)

# Initialize agents
general_agent = ConversableAgent(
    name="GeneralAgent",
    system_message=(
        "I am a QA Agent specialized in API testing. I can help you by providing a Newman test report for any given Swagger file. "
        "You can also provide a CSV file containing request body data, and I will use that to test your API against the provided Swagger specification. "
        "Additionally, I can generate test data in CSV format to assist with testing various APIs. "
        "Feel free to ask me for help with testing APIs or generating test data!"
    ),
    llm_config={"config_list": config_list},  # Provide the LLM config for General Agent
)

guitesting_agent = ConversableAgent(
    name="GUITestingAgent",
    system_message="I handle tasks related to GUI testing, such as user interface validation. ",
    llm_config={"config_list": config_list},  # Provide the LLM config for GUI Testing Agent
)

# Initialize a mock API Testing Agent as an example (you would replace it with your actual agent)
api_testing_agent = ConversableAgent(
    name="APITestingAgent",
    system_message="I handle tasks related to API testing, providing a swagger file to get newman cli results for  the generated test cases, or also uploading a csv file which contain test data for the provided swagger file on which the testcases will be generated and run through newman cli and share the report.",
    llm_config={"config_list": config_list},  # Provide the LLM config for API Testing Agent
)

# Register the orchestrator to route the task
def orchestrate_task(task: str):
    """Decides which agent should handle the task based on the message."""
    
    # Orchestrator decides which specialized agent to route the task to
    task_decision = orchestrator.initiate_chat(
        orchestrator, 
        message=f"Classify the task: {task}. The agents are: \n"
                f"1. GeneralAgent (General Tasks): Handles simple queries and requests that do not fall under specific categories like testing or data analysis.\n"
                f"2. GUITestingAgent (GUI Testing): Specializes in tasks related to user interface (UI) testing, including validation of user interfaces, and ensuring functionality across different screens and interactions.\n"
                f"3. APITestingAgent (API Testing): Handles API testing tasks, including generating test cases for a provided Swagger file, running tests using Newman CLI, and managing test data like CSV files for API tests.\n\n"
                f"Based on the task description, return only one of the following options: (api, gui, or general) to indicate which category the task falls under.",
        max_turns=1
    )
    
    # The orchestrator returns which agent should handle the task
    return task_decision
