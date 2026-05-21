Read `AGENTS.md` before starting.

we are stilling amining towards the same goal of the previous prompt , we will build the correctice rag agent

follow the `agentic plan.md` for reference

the crag and the complaince agent is build correclty  
now we are foccusing on the startegy agent 


### Node 2: Strategy Agent (Channel & Timing)
- **Role**: Determines how (SMS, Email, Push) and when to send the message.
- **Mechanism (Strategy Agent)**: 
  1. Queries Supabase for the user's past interaction history and preferences.
  2. Uses an LLM to decide the most effective channel and the highest-conversion time of day.
  3. Updates the state with channel (e.g., "Push Notification") and scheduled_time (e.g., "2026-05-22T18:00:00Z").
- **Outcome**: Updates the state with channel (e.g., "Push Notification") and scheduled_time (e.g., "2026-05-22T18:00:00Z").    

now I want you to write down the implementation plan for just this agent 
full proof plan of what this agent do and creation of this agent 

how it taakes use of the langgraph nodes and states how it updates and adds the state to the graph and the reponse it gives to the other user 

the code should be wrriten in the same manner logic and core in servives folder prompts folder and models folder 

you will be creating migration db for the user table for this therefore go through context again and check what else thus my entire backend requires all model and everything and make 1 proper user table accordingly (if your are creating this)

success criteria
- the logic should start from  the rag pipeline
- check the state and info of rag is retreived proeprly from node 1 then check if data is fetch propely from supabase and 
- then the startegy its returning and its validity 