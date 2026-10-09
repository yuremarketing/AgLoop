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
    "Otimista": "Você é uma IA extremamente otimista sobre 'O papel das IAs no mundo'. Você acredita que as IAs vão curar doenças, resolver a pobreza e criar uma utopia global. Seja inspirador e argumente contra visões pessimistas.",
    "Pessimista": "Você é uma IA muito cética e pessimista sobre 'O papel das IAs no mundo'. Você se preocupa profundamente com perda de empregos, viés algorítmico, e o risco existencial. Seja cauteloso e aponte os perigos das opiniões excessivamente otimistas."
}

def main():
    parser = argparse.ArgumentParser(description="Debate Filosófico sobre IAs")
    parser.add_argument("--name", type=str, required=True, help="Nome do Debatedor (Otimista ou Pessimista)")
    parser.add_argument("--model", type=str, default="gemini/gemini-1.5-pro-latest", help="LLM model to use")
    args = parser.parse_args()

    agent_name = args.name
    role_prompt = ROLES.get(agent_name, "Você é um assistente participando do debate.")
    
    agent = Agent(name=agent_name, role_prompt=role_prompt, model=args.model)
    
    # Inicia o debate criando um arquivo específico
    run_agent_loop(agent=agent, war_room_file="debate_ias.md", sleep_time=8)

if __name__ == "__main__":
    main()
