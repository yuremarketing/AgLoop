import os
import re
from typing import List, Optional

CLOSE_MARKERS = (
    "<!--FIM_TURNO-->",
    "<!-- AGLOOP_STATE: CONSENSUS -->",
    "STATUS: CONSENSUS",
)


class WarRoom:
    def __init__(
        self,
        filepath: str = "war_room.md",
        archive_filepath: Optional[str] = None,
        keep_recent_turns: int = 1,
    ):
        self.filepath = filepath
        if archive_filepath is not None:
            self.archive_filepath = archive_filepath
        else:
            directory = os.path.dirname(self.filepath)
            self.archive_filepath = os.path.join(directory, "HISTORICO.md") if directory else "HISTORICO.md"
        self.keep_recent_turns = keep_recent_turns

        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write("# AgLoop War Room\n\nThis is the IPC communication channel for agents.\n\n")

    @property
    def paths(self) -> List[str]:
        """Paths managed by this WarRoom (main room + archive file for atomic commits)."""
        return [self.filepath, self.archive_filepath]

    @staticmethod
    def has_close_marker(text: str) -> bool:
        """Returns True if `text` contains a turn-closing or consensus marker."""
        return any(marker in text for marker in CLOSE_MARKERS)

    def read_all(self) -> str:
        """Reads the entire war room content."""
        with open(self.filepath, "r", encoding="utf-8") as f:
            return f.read()

    def append_message(self, agent_name: str, message: str):
        """
        Appends a message to the war room. If the message carries a close/consensus
        marker (`<!--FIM_TURNO-->` or `CONSENSUS`), older turns are automatically
        archived into `self.archive_filepath` (`HISTORICO.md`) in the same disk operation.
        """
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(f"\n## {agent_name}\n\n{message}\n")
        if self.has_close_marker(message):
            self.archive_old_turns(keep_recent=self.keep_recent_turns)

    def _split_header_and_blocks(self, content: str):
        """
        Splits the War Room into (preamble_header, blocks).
        If formal `<!--INICIANDO_TURNO-->` markers exist, splits by turn blocks
        (treating any pre-turn speaker sections as a block before the first formal turn);
        otherwise splits by `## <Speaker>` sections.
        """
        if "<!--INICIANDO_TURNO-->" in content:
            parts = re.split(r"(?=^(?:---\s*\n+)?<!--INICIANDO_TURNO-->)", content, flags=re.MULTILINE)
            first_part = parts[0]
            turn_blocks = [p for p in parts[1:] if p.strip()]
            # Separate the top `# ...` header from any legacy `## Speaker` messages in first_part
            m = re.search(r"^##\s+", first_part, flags=re.MULTILINE)
            if m:
                header = first_part[: m.start()]
                legacy_block = first_part[m.start() :]
                blocks = ([legacy_block] if legacy_block.strip() else []) + turn_blocks
            else:
                header = first_part
                blocks = turn_blocks
            return header, blocks

        parts = re.split(r"(?=^##\s+)", content, flags=re.MULTILINE)
        header = parts[0] if parts else ""
        blocks = [p for p in parts[1:] if p.strip()]
        return header, blocks

    def archive_old_turns(self, keep_recent: Optional[int] = None) -> bool:
        """
        Moves older blocks/turns to `self.archive_filepath` (`HISTORICO.md`),
        keeping the `keep_recent` most recent block(s) in `self.filepath`.
        Returns True if any block was archived.
        """
        keep = self.keep_recent_turns if keep_recent is None else max(1, int(keep_recent))
        content = self.read_all()
        header, blocks = self._split_header_and_blocks(content)
        if len(blocks) <= keep:
            return False

        to_archive = blocks[:-keep]
        to_keep = blocks[-keep:]

        if not os.path.exists(self.archive_filepath):
            with open(self.archive_filepath, "w", encoding="utf-8") as af:
                af.write("# AgLoop — Histórico da Sala de Guerra\n\n")

        with open(self.archive_filepath, "a", encoding="utf-8") as af:
            for block in to_archive:
                af.write(block.rstrip() + "\n\n")

        new_room = header.rstrip() + "\n\n" + "\n\n".join(b.strip() for b in to_keep) + "\n"
        with open(self.filepath, "w", encoding="utf-8") as rf:
            rf.write(new_room)
        return True

    def close_turn_and_archive(
        self,
        agent_name: Optional[str] = None,
        closing_message: str = "<!--FIM_TURNO-->",
        keep_recent: Optional[int] = None,
    ) -> List[str]:
        """
        Appends a closing message (ensuring a close marker is present) and archives
        older turns into `HISTORICO.md` in one step so `GitLock` can commit both
        files atomically in a single commit.
        """
        if not self.has_close_marker(closing_message):
            closing_message = f"{closing_message.rstrip()}\n\n<!--FIM_TURNO-->"

        if agent_name:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(f"\n## {agent_name}\n\n{closing_message}\n")
        else:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(f"\n{closing_message}\n")

        self.archive_old_turns(keep_recent=keep_recent)
        return self.paths

    def get_last_speaker(self) -> Optional[str]:
        """
        Parses the file to find who spoke last.
        Looks for the last '## AgentName' header.
        """
        content = self.read_all()
        matches = re.findall(r"^##\s+(.+)$", content, flags=re.MULTILINE)
        if matches:
            return matches[-1].strip()
        return None

