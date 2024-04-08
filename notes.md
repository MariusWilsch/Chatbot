---
runme:
  id: 01HTYPQFASG1P272GYW8GC4N2Q
  version: v3
---

### Improvement Notes

- The `generate_final_result` function should be _async_ so we can return the ending message earlier.
- We should try using `gpt4` for *checking* and `gpt3.5` for the *follow-up* for faster processing.
- Similar to the statement above, we can try the same with `anthropic 3 opus` for *checking* and `sonnet` for *follow-up*.
- Instead of using `st.spinner`, `st.status`, or `st.progress`, we can use a loading state to show the user that the app is processing.
- I must clean up the file by putting the functions in a separate file.
- I think streaming for the follow-up questions would be nice to have faster *time-to-first-token*.
- Count the number of tokens in the input and output for every api call and then return the total number * cost per token in the end to show cost per full run.