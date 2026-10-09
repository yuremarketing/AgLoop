import os
import re

class WarRoom:
    def __init__(self, filepath: str = "war_room.md"):
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            # Initialize empty war room if not exists
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write("# AgLoop War Room\n\nThis is the IPC communication channel for agents.\n\n")

    def read_all(self) -> str:
        """Reads the entire war room content."""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def append_message(self, agent_name: str, message: str):
        """Appends a message to the war room."""
        with open(self.filepath, 'a', encoding='utf-8') as f:
            f.write(f"\n## {agent_name}\n\n{message}\n")

    def get_last_speaker(self) -> str:
        """
        Parses the file to find who spoke last. 
        Looks for the last '## AgentName' header.
        """
        content = self.read_all()
        # Find all ## Headers
        matches = re.findall(r'^##\s+(.+)$', content, flags=re.MULTILINE)
        if matches:
            return matches[-1].strip()
        return None
