# Retention OS 

## Problem Statement
Early Risk Detection & Customer Prioritization:
Identify high-value customers showing early disengagement and
focus on those most likely to be retained.

Causal Uplift Segmentation & AI-Guided Actions:
Segment customers into stay, leave, and persuadable groups, then
select the most effective and resource-efficient intervention
for each customer.

## Overview
IDEA / SOLUTION:
RetentionOS is an AI-driven predictive customer
outreach platform that uses churn prediction, causal
uplift modeling, and profit-aware decision intelligence
to automatically identify persuadable customers and
execute personalized retention strategies.

Main Points of Interest -
• Built for Customer-Driven Industries: Banks, telecom,
subscription platforms, and digital services to detect
churn early and protect customer lifetime value.

• Automated Intelligent Retention: Identifies high-value
at-risk customers (LTV + churn), selects the best intervention strategy (uplifting models), and executes outreach across multiple channels. (agentic AI + web-hooks)

Unique Value Proposition (UVP)

RetentionOS moves beyond traditional churn prediction by
identifying persuadable customers and executing
profit-optimized retention actions using causal uplift
intelligence and AI-driven strategy decisions.

## Goals

1. Financial & Risk Intelligence:
    LTV-Based customer eligibility filtering with ML-driven churn risk detection
2. Casual Uplift Intelligence
    identifies customers who can actually be influenced by retention interventions
3. AI Strategy Decision Engine
    Agent-Baed reasoning selects the best retention strategy using churn risk, uplift score, and customer value
4. Context & Network Intelligence
    Uses knowesge graphs and influence modeling to detect hidden churn risks
5. Profit Guardrails & Market Awareness
    Ensures ROI-positive actions, using policy monitoring, and strategy simulation
6. Personalized Multi-Channel Outreach
    Automates targeted engagement via email, SMS, app notifications, or calls.


## Core User Flow

-No authorization for now only one company who streams its data 
2. The data that is streamed is procced and displayed.
3. actionable insights is given based on this data.
4. custom itervention strategy is given for user to accept and send that to that customer.
5. results is agian shown to user.


## Features

### Data Streaming

- continous data is streamed
- the proccessing of the stream data is shown live on web
- agents that are working is shown ive on web

### Financial & Risk Intelligence (LTV & CHURN)

-the data that is being stream is of customer who are doing various activities on the internet who are subscribed to bank subscriptions
-based on that thier LTV and churn are calculated
- to save computer power first ltv is calculated if user avg ltv is above a particualr level then only further processing of the user is done
- The ltv pipline gives avg ltv by historical ltv  and predictive ltv (using predictive ltv model) 
-if user above a partcicular ltv are shortlisted they go for further proccesing
-that user goes through churn prediction model 

### Casual Uplift Intelligence - Persudable intervention (VIMP)

- If user with high ltv and churn risk then they are sent to uplift model
- user with particular churn risk (moderate to high) are sent in this model
- we are using meta: x-leaener #multitreament model to predict the upliftment score 
of user in 5%,10%,15% and 20% 
- then after this the json output is given to Treatment Optmizer
- so the formula I used [Expected Profit=(uplift×CLV)−treatment cost] 
-pseudo code
-this happens in treatment optmizer 


```python
best_profit = -999999
best_treatment = None

for treatment in treatments:
    profit = uplift[treatment] * clv - cost[treatment]

    if profit > best_profit:
        best_profit = profit
        best_treatment = treatment

print("Best Treatment:", best_treatment)
print("Expected Profit:", best_profit)
```

- output 
```python
{
  "best_treatment": "discount_12",
  "expected_profit": 1420
}

```

## Intervention strategy

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

### Future feature- n8n like canvas

- n8n like canvas
- in which user can make custom n8n like automation with our models and spin custom agents
-uses crew a.i

## Should Follow

### Frontend - all to 2026
 - nextjs- latest
 -shadcn-latest all shadcn compoenents will be availabe locally use that onyly has base varient and improvise on that
 -tailwind css -latest
 - best frontend strategies and method
 -components breakdown

### Backend -
- python - 3.10 - most stable
- fastapi -latest 2026
-langchain - latest
-langgraph  -latest
-inngest - latest

### Db
postgress sql- supabase
redis-any free version but important app should be fast 


## Success Criteria

1. agents working and personal message is reaching to end user\
2. mmodel predicting accurately 
3. functional and scalble (optmistic u.i)
