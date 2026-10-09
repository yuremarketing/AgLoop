import os
import time
import argparse
from dotenv import load_dotenv
from core.git_lock import GitLock
from core.war_room import WarRoom
from core.agent import Agent

# Load environment variables
load_dotenv()

# Define roles for our agents
ROLES = {
    "Alice": "You are a senior software architect. You focus on structure, scalability, and robust design. You like to propose high-level ideas.",
    "Bob": "You are a pragmatic developer. You focus on implementation details, edge cases, and code simplicity. You like to challenge complex architectures."
}

def main():
    parser = argparse.ArgumentParser(description="Run an AgLoop Agent")
    parser.add_argument("--name", type=str, required=True, help="Name of the agent (e.g., Alice or Bob)")
    parser.add_argument("--model", type=str, default="gemini/gemini-1.5-pro-latest", help="LLM model to use")
    parser.add_argument("--sleep", type=int, default=10, help="Seconds to sleep between loop iterations")
    args = parser.parse_args()

    agent_name = args.name
    role_prompt = ROLES.get(agent_name, "You are a helpful AI assistant.")
    
    agent = Agent(name=agent_name, role_prompt=role_prompt, model=args.model)
    git_lock = GitLock(repo_path=".")
    war_room = WarRoom(filepath="war_room.md")

    print(f"Starting AgLoop for Agent: {agent_name}")
    print(f"Model: {args.model}")

    def agent_action_callback():
        # Read the current war room
        context = war_room.read_all()
        last_speaker = war_room.get_last_speaker()

        # If I am the last speaker, I should wait for others.
        if last_speaker == agent.name:
            print(f"[{agent.name}] I was the last speaker. Waiting for others...")
            return

        # It's my turn (or no one has spoken)
        print(f"[{agent.name}] My turn to speak!")
        response = agent.think_and_act(context)
        war_room.append_message(agent.name, response)
        print(f"[{agent.name}] Appended response to War Room.")

    # Main Loop
    while True:
        try:
            print(f"\n--- Loop Iteration for {agent_name} ---")
            success = git_lock.acquire_lock_and_push(
                action_callback=agent_action_callback,
                message=f"AgLoop: {agent_name} update"
            )
            
            if success:
                print(f"[{agent_name}] Lock released successfully (or no changes needed).")
            else:
                print(f"[{agent_name}] Failed to push or pull. Lock collision occurred. Will retry next loop.")

            print(f"Sleeping for {args.sleep} seconds...")
            time.sleep(args.sleep)
            
        except KeyboardInterrupt:
            print("\nExiting AgLoop.")
            break
        except Exception as e:
            print(f"Unexpected error in loop: {e}")
            time.sleep(args.sleep)

if __name__ == "__main__":
    main()
