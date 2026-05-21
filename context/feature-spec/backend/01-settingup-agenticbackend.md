Read `AGENTS.md` before starting.

our main goal will be achived by more prompts this is the first one to achive that goal 

``
agentic system for the intervention strategy 
-
- after all the processing the selected users json comes to intervention pipline
- the agents goes through compliance agents who checks authority of intervention
```python
{
  "user_id": 123,
  "best_discount": "10%",
  "expected_profit": 1400
}
```
- right time to send the push notifcation to user, channel for connections is decided by the user
- also the intervention message is send by a corrective intervention message writer agent 
- there could be more agents which are not decided yet

its core feature 
uses rag to check company policies self reasoning corrective rag type funcationality which gives the the statment to interven or not then another agent which takes this information and choose the intervention medium and write the intervnetion message (now that message goes through meta tribe model to check the hook this is the corrective kind of loop again for agent to check what he had made once thre response for meta tribe the agent checks if need for correction it corrects again) 

I want you to research as much as possible and give me everything the best method how to create those agents the persistanct memory the context management token management everything give me everything and how can I use trigger.dev in this 

``
for achieving the above goal we are going with the startegy mentioned in `agentic plan.md` 



We are now setting up the base/foundation for the backend. and the agentic call system messaging(gmail),whatsapp twillo message, 

therefor make a virtual env inside backend download the following dependices 
- supabase
- supabase-realtime-py
- langchain
- langgraph
- pydantic
- python-dotenv
- langchain open a.i 
- trigger.dev in replacement for inngest 

now I want you to make the setup in utils folder
- llm (langchain llm initialization )
- supabase ( supabse connection )
- trigger.dev ( trigger.dev initialization )

use .env file to load the environment variables (give me the key to put in .env)

and make sure the setup is done in the backend folder
then setup the fast api `app.py` with health check endpoint, llm invoke endpoint to check the llm call, and trigger.dev callback endpoint.

the above criteria is meet then the foundation setup is a sucess



