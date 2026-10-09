import argparse
from dotenv import load_dotenv
from core.agent import Agent
from core.runner import run_agent_loop

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
    parser.add_argument("--room", type=str, default="war_room.md", help="The markdown file for IPC")
    args = parser.parse_args()

    agent_name = args.name
    role_prompt = ROLES.get(agent_name, "You are a helpful AI assistant.")
    
    agent = Agent(name=agent_name, role_prompt=role_prompt, model=args.model)
    
    run_agent_loop(agent=agent, war_room_file=args.room, sleep_time=args.sleep)

if __name__ == "__main__":
    main()
