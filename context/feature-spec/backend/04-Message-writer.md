Read `AGENTS.md` before starting.

we are stilling amining towards the same goal of the previous prompt , we will build the correctice rag agent

follow the `agentic plan.md` for reference

the crag and the complaince agent is build correclty and the strategy agent is build correclty 
now we are foccusing on the Message writer agent 
and after making this node 3 and node 4 connet it with other nodes in langgraph propelry with proper commom state and connections logic 

here node 3 or the message writer should also have access to more tools,
so that it can once aproved by node 4 meta model send the message to the right channel and time 
the tool should be 
- email message (like access to the email client and send the message)
- twillo message (like access to the twillo client and send the message)
- push message (like access to the push client and send the message) our website dosent has this feature yet so ignore this
- ignore sms as well 

now what I want node 3 to do is that if its writing for email it should be more comprehand and decorative I just dont want writing I want decoration to research how I can do that and CTA button needed 

also I dont want my agent to know that it has access to email message sending and whatsapp twillo message 
it should have acces to 1 tool thats is send message which takes in the data 
for email subscribers email: subjecte: body: CtA: and how will you manage decoration that you see (no emojis at all in any intervention message)

for email: your research to but I am planing to use resend 
you look if it suits are need or not 

for twillo just send the message twillo will send the message to me (not testing this now)
CTA needed (thats get this discount) for almost every intervention message 

since node 3 is very highly connected to node 4 so I want you to develop node 4 as well and the correction loop 

node 4 use meta tribe v2 https://huggingface.co/facebook/tribev2 
TRIBE v2 is a deep multimodal brain encoding model that predicts fMRI brain responses to naturalistic stimuli (video, audio, text). It combines state-of-the-art feature extractors — LLaMA 3.2 (text), V-JEPA2 (video), and Wav2Vec-BERT (audio) — into a unified Transformer architecture that maps multimodal representations onto the cortical surface.

basically it takes the text and the visual that end user going to see and lights the part of the brain that is going to be affected by the intervention
which will help us to identify the effiency and effectivness of our hook so make this node according to it ()


### Node 3: Intervention Message Writer
- **Role**: Drafts the actual message tailored to the chosen channel, incorporating the 10% discount.
- **Mechanism**: Uses strict prompt templates ensuring length constraints (e.g., short for Push) and incorporates the exact discount value.
- **Output**: Updates the state with `current_draft`.


### Node 4: Meta Tribe Model (The Hook Reviewer)
- **Role**: Evaluates the `current_draft` for marketing effectiveness, "hook" quality, and tone.
- **Mechanism**: Acts as a strict evaluator. It uses Pydantic structured outputs to return:
  ```json
  {
    "approved": false,
    "score": 6,
    "feedback": "The hook is too weak. Start with a question to create urgency."
  }
  ```
- **The Corrective Loop**: 
  - **Conditional Edge**: If `approved` is True, move to the Dispatch node.
  - If `approved` is False, the graph **loops back** to the Intervention Message Writer, appending the `feedback` to the Writer's context so it can generate a better draft.

  # success criteria
  - node 3 should be working properly writing good content for the right channel
  - node 4 should be working properly and give the right feedback (test it properly independantly that model is donwloaded and working)
  - the correction loop should be working properly and the feedback should be correct (and the number of retries) 
  - the email should be sent to me (movindsouza79@gmail.com) no need for twillo message 
  - all the langgraph nodes should be connected all logic should be working propelelry with proper memory state and connections logic