# Capturing intent in Translator users
Controlled user interaction with Translator tool.

We propose here a tool that controls browser interaction with user and triggers feedback accordingly. The feedback is then inserted in a JSON template to feed test assets automatically. 


## Objectives
- Generate more test assets, faster
- Capture more variance in rating results for the QA pairs
- Collect data on user interaction with Translator given several scenarii (e.g. PASS/FAIL, scoring, ordering…etc)
- Model data to:
-   Characterize users as personas
-   Analyze interaction temporal dynamics
-   Determine key players in predicting the way they will interact with Translator in function of their persona

## Hypothesis
We hypothesize that there is a significant change in the way people interact with the tool while exploring the results of a query that is predictive of their intent given who they are.

## Proposal
We will capture user interaction with the tool and researcher type data to attempt to measure the change in interaction with the tool during a session. 

## Method/start up material
    - Before interaction (baseline measure)
    - A “user-Translator dialog tool” (this repo)
    - After interaction

## Limitations
### Software-wise
The tool operates on the html UI page directly controlling the page and injecting scripts to allow the user to give feedback in function on what they do. Currently the only action supported is clicking on a result expander.
### Methodologically
Currently the “user-Translator dialog tool” is very primitive. It does not support:
### Logging user metadata
Logging temporal interaction is incomplete
Constrained with the unique scenario (PASS/FAIL with 1 type of action : click on the result expander) and not investigation of scoring or grouping (other types of actions - moving result expander…etc.)
### Test asset changes to fill new requirements

