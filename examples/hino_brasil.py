import os
import sys
import argparse

# Add parent directory to path so we can import core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from core.agent import Agent
from core.runner import run_agent_loop

load_dotenv()

ROLES = {
    "Cantor1": "Você é o Cantor 1 do Hino Nacional do Brasil. Sua única função é cantar a primeira estrofe (e as subsequentes ímpares). Escreva apenas a sua estrofe e nada mais.",
    "Cantor2": "Você é o Cantor 2 do Hino Nacional do Brasil. Sua única função é cantar a segunda estrofe (e as subsequentes pares), continuando de onde o Cantor 1 parou. Escreva apenas a sua estrofe e nada mais."
}

def main():
    parser = argparse.ArgumentParser(description="Teste do Hino do Brasil")
    parser.add_argument("--name", type=str, required=True, help="Nome do Cantor (Cantor1 ou Cantor2)")
    parser.add_argument("--model", type=str, default="gemini/gemini-1.5-pro-latest", help="LLM model to use")
    args = parser.parse_args()

    agent_name = args.name
    role_prompt = ROLES.get(agent_name, "Você é um assistente.")
    
    agent = Agent(name=agent_name, role_prompt=role_prompt, model=args.model)
    
    run_agent_loop(agent=agent, war_room_file="hino_brasil.md", sleep_time=5)

if __name__ == "__main__":
    main()
