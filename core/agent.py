import litellm

class Agent:
    def __init__(self, name: str, role_prompt: str, model: str = "gemini/gemini-1.5-pro-latest"):
        self.name = name
        self.role_prompt = role_prompt
        self.model = model

    def think_and_act(self, war_room_context: str) -> str:
        """
        Sends the War Room context to the LLM and gets the agent's next message.
        """
        system_prompt = (
            f"You are {self.name}.\n"
            f"{self.role_prompt}\n"
            "You are participating in a War Room debate via Markdown.\n"
            "Below is the current content of the War Room. Add your thoughts or actions.\n"
            "Do not output markdown headers like '## AgentName', just output your response text directly."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"WAR ROOM CONTEXT:\n{war_room_context}\n\nWhat is your next message?"}
        ]

        print(f"[{self.name}] Thinking...")
        try:
            response = litellm.completion(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[{self.name}] LLM Error: {e}")
            return "I encountered an error trying to think of my next response."
