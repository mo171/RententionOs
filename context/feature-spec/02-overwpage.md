# RetentionOS Overview Page 

### read the `AGENTS.md` first

## Objective

Build the `/overview` page for RetentionOS.

The final UI must visually match the reference image provided ain the chat as closely as possible.

This is an enterprise AI operating dashboard for retention intelligence, autonomous customer interventions, and live operational monitoring.

Do not redesign or reinterpret the UI.
Replicate layout hierarchy, spacing, proportions, component structure, and interaction behavior from the reference image.

## The architect
- I want the sidebar to be fixed and not scrollable. and seprate component and the active state thing should be done by routing driven u.i state determintic sidebar checks for active path and the highlights work accordingly used the best approch possible for it.
- I want the top navbar to be fixed and not scrollable. and seprate component for it.do not add search bar in it
- I want the main dashboard to be scrollable.
- I want the main dashboard to be split into 2 columns.
    - Left column: KPI cards
    - Right column: Revenue Flow Graph and Alert Center Panel
- you can also break into more compoenents if you want 

the alert center should have a fixed hight should not expand when no of list grows should render only 3 and on click more it should a tab on the same page showing all the list 

- the data that will be shown will be live updated so work accordingly make a startegy to handle that for furure when we will add the live data path and mention in project-overview pending tab 

- the animations should be good and should feel premium