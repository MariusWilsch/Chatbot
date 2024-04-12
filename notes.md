---
runme:
  id: 01HTYPQFASG1P272GYW8GC4N2Q
  version: v3
---

### Improvement Notes

- The `generate_final_result` function should be _async_ so we can return the ending message earlier.

> Right now I can just try to move the generate_final_result function below the follow ending text so the user can see the ending message while the function is still running.

- We should try using `gpt4` for *checking* and `gpt3.5` for the *follow-up* for faster processing.
- Similar to the statement above, we can try the same with `anthropic 3 opus` for *checking* and `sonnet` for *follow-up*.
- Instead of using `st.spinner`, `st.status`, or `st.progress`, we can use a loading state to show the user that the app is processing.
- (__DONE__) ~~I must clean up the file by putting the functions in a separate file.~~
- I think streaming for the follow-up questions would be nice to have faster *time-to-first-token*.
- (__DONE__) ~~Count the number of tokens in the input and output for every api call and then return the total number * cost per token in the end to show cost per full run.~~
- (__DONE__) ~~Generate a summary of the result json and asks the user if the data is correct. If not then ask the user to provide the corrections.~~

   - Describe the situation
   - Describe the situation date
   - Describe the consequences
   - Describe if the case data is right

- 

### Problems

- __FIXME__: Right now we pass the chat_history directly into the message parameter of the llm call and also when adding the result_output_json to the user message. These are __uncessary__ input tokens. We must remove that redundancy.
- __FIXME__: If the user says something the case started couple of x before the accident the model will still only take the current date in consideration and not count the couple of x before the accident. We must fix this.
   - _Example_: I started a legal case on the 24 of June 2024. The surgery started a couple of months before
- __FIXME__: If the user says something I need a lwayer something not realted to an accident dispute or siutation return an gneric explination of purpose of this.