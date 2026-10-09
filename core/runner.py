import time
from core.git_lock import GitLock
from core.war_room import WarRoom

def run_agent_loop(agent, war_room_file="war_room.md", sleep_time=10):
    git_lock = GitLock(repo_path=".")
    war_room = WarRoom(filepath=war_room_file)
    
    print(f"Starting AgLoop for Agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"War Room File: {war_room_file}")

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
            print(f"\n--- Loop Iteration for {agent.name} ---")
            success = git_lock.acquire_lock_and_push(
                action_callback=agent_action_callback,
                message=f"AgLoop: {agent.name} update in {war_room_file}"
            )
            
            if success:
                print(f"[{agent.name}] Lock released successfully (or no changes needed).")
            else:
                print(f"[{agent.name}] Failed to push or pull. Lock collision occurred. Will retry next loop.")

            print(f"Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            print("\nExiting AgLoop.")
            break
        except Exception as e:
            print(f"Unexpected error in loop: {e}")
            time.sleep(sleep_time)
