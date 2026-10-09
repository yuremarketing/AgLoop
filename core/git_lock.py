import time
import os
from git import Repo
from git.exc import GitCommandError

class GitLock:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
        self.origin = self.repo.remotes.origin

    def pull(self) -> bool:
        """
        Pulls from remote using rebase to avoid merge commits.
        Returns True if successful, False if there's a conflict or error.
        """
        try:
            self.origin.fetch()
            # We assume we are on the main branch. Let's make sure.
            current_branch = self.repo.active_branch.name
            
            # Use rebase to keep history linear
            # git pull --rebase origin <branch>
            self.repo.git.pull('--rebase', 'origin', current_branch)
            return True
        except GitCommandError as e:
            print(f"Git pull error: {e}")
            # If rebase fails, we should probably abort it to clean state
            try:
                self.repo.git.rebase('--abort')
            except GitCommandError:
                pass
            return False

    def has_uncommitted_changes(self) -> bool:
        """Checks if there are any modified or untracked files."""
        return self.repo.is_dirty(untracked_files=True)

    def commit(self, message: str) -> bool:
        """
        Stages all changes and commits.
        """
        try:
            self.repo.git.add(A=True)
            if not self.has_uncommitted_changes():
                # Nothing to commit
                return True
            self.repo.index.commit(message)
            return True
        except GitCommandError as e:
            print(f"Git commit error: {e}")
            return False

    def push(self) -> bool:
        """
        Pushes to the remote. If it fails, it means another agent pushed
        first (lock collision).
        """
        try:
            current_branch = self.repo.active_branch.name
            self.origin.push(current_branch)
            return True
        except GitCommandError as e:
            print(f"Git push collision/error: {e}")
            # If push fails, we didn't get the lock. 
            # We must drop our commit to retry cleanly.
            # git reset --hard HEAD~1
            self.repo.git.reset('--hard', 'HEAD~1')
            return False

    def acquire_lock_and_push(self, action_callback, message: str) -> bool:
        """
        A high-level wrapper:
        1. pull()
        2. Execute action_callback() which modifies files
        3. commit()
        4. push() -> if true, we won the lock!
        """
        if not self.pull():
            return False
            
        # Perform the actual file modifications
        action_callback()
        
        # If nothing changed, we can just return True (no push needed)
        if not self.has_uncommitted_changes():
            return True
            
        if not self.commit(message):
            return False
            
        return self.push()
