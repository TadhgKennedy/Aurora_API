# Aurora_API
Aurora application API

# Constraints
- I was only able to make use of free resource and LLMs so he models are more basic and I run out of calls quickly. This is not as thoroughly tested as I would like.
- I wasn't able to find a way to achieve the 2 second latency. I would be very interested to see how someone achieved this!

# System Architecture
The architecture is very basic for now.

The API takes the question as input, and LLM extracts the person from the sentence.

The identified person's name is used to pull all the messages for that person from the messages.
- For now I've had to pull all of it from the API and store it in a csv because I kept getting hit with pay walls or bad URL error when I did it on the fly
- Ideally I would improve the messages API to take the name as input so it would just return the necessary messages instead of a bulk and then filter because it's wasting time

Then I take all the messages and the question and feed it into the LLM to extract the correct info.
- Definitely improvements to be made to this approach but I'm limits by using free resources so other options like embedding the questions and messages and only extracting messages that a similar to avoid extraneous tokens weren't possible

# Improvements
- Longer term I would definitely be looking at a more agentic approach but this tends to take longer and as speed was a goal here I opted not to pursue for now
- Name extractions might be possible in other ways with reliability, I'd also need to implement something which accounts for duplicate names and decide how to address this (split query per possible name, ask for clarity etc.)

# Scaling System
- I think the main thing for scaling for me would be to move away from a system like this entirely, as time goes on the messages per user and number of users would make this impractical long term.
- I would look at storing the data in different ways, so options I would consider would be:
-   user profiles which could be updated via batch jobs and then recent messages used in combination the better answer the question
-   Storing the data in a graph so we could have both locations, users, types of events and the events themselves stored to more quickly shrink the possible answers.
