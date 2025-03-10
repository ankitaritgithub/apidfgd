GROQ_API_KEY="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"
API_TESTING_AGENT_URL="ws://localhost:8006/ws/process_task"
GUI_TESTING_AGENT_URL="http://localhost:8005/run_tests"

DB_HOST=172.16.200.34
DB_USERNAME=agent_qa
DB_PASSWORD=XS%40agent-qa-1
DB_NAME=agent_qa_db
DB_PORT=30901


 i want updation in  dashboared  and chatbotresponse  section basically when response   word limit is more than 500 then the   response will comes under inside the response cards  same like chatgpt4  their is a expand arrow onclick of that arrow that hole response cards gets open and the chat-input and user-message get appear  herecollpse and expand icons   functionality are from chatbotresponse.jsx section do changes accordingly when user click on expand icons the chat-input and the mesage - input layout  mapping will happein  only they will move to tis section section which get active after clicking on it@Dashboard.jsx#L457-563  and response cards get open inside the main-content-grid sction with a flex of 1  do updation and  changes basically conditional rendering and layout mapping  i= i want layout mapping when click on expand icons the user-message and chat-input will shifted to this section@Dashboard.jsx#L455-464  and  the bot- response get open at  the  chat-active -section and  with flex = 1
