"""Priority-based message scheduling with task deduplication."""
import heapq
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from driving_mock import runnables

SIMULATION_TIME_MS = 400

# Priority queue for tasks, using (priority, time, task) as key
event_queue = []
heapq.heapify(event_queue)

# Track execution state
core_time = [0, 0]
execution_log_core = {0: [], 1: []}
completed_instances = defaultdict(int)
event_task_instance_counter = defaultdict(int)

# Track task priorities and deduplication
task_priorities: Dict[str, int] = {name: props['criticality'] for name, props in runnables.items()}
task_duplicates: Dict[str, Set[int]] = defaultdict(set)  # Track duplicate instances
task_last_execution: Dict[str, int] = defaultdict(int)  # Track last execution time
STARVATION_THRESHOLD = 100  # Time threshold for starvation detection


def is_task_starving(task: str, current_time: int) -> bool:
    """Check if a task is starving based on its last execution time."""
    return current_time - task_last_execution[task] > STARVATION_THRESHOLD


def handle_duplicate_task(task: str, instance: int, current_time: int) -> bool:
    """Handle duplicate task detection and priority adjustment.
    Returns True if task should be executed, False if it should be dropped."""
    if instance in task_duplicates[task]:
        # Task is a duplicate, check if it should be dropped
        if not is_task_starving(task, current_time):
            return False
        # If task is starving, boost its priority
        task_priorities[task] = max(task_priorities.values()) + 1
    else:
        task_duplicates[task].add(instance)
    return True


def schedule_periodic_runnables():
    """Schedule all periodic runnables up to the simulation time limit."""
    for name, props in runnables.items():
        if props["type"] == "periodic":
            time = 0
            counter = 0
            while time < SIMULATION_TIME_MS:
                # Use negative priority for heapq (higher priority = lower number)
                heapq.heappush(event_queue, (
                    -task_priorities[name],  # Priority (negative for max heap)
                    time,                    # Time
                    name,                    # Task name
                    props["execution_time"], # Execution time
                    counter                  # Instance number
                ))
                time += props["period"]
                counter += 1


def schedule_event_runnables(triggered_tasks: List[str], current_time: int):
    """Schedule event-based tasks with deduplication and priority handling."""
    for name, props in runnables.items():
        if props["type"] != "event":
            continue

        if not set(props["deps"]) & set(triggered_tasks):
            continue

        if all(completed_instances[dep] > event_task_instance_counter[name]
               for dep in props["deps"]):
            current_instance = event_task_instance_counter[name]
            
            # Check for duplicates and handle priority
            if not handle_duplicate_task(name, current_instance, current_time):
                continue

            # Schedule task with current priority
            heapq.heappush(event_queue, (
                -task_priorities[name],  # Priority (negative for max heap)
                current_time,           # Time
                name,                   # Task name
                props["execution_time"], # Execution time
                current_instance        # Instance number
            ))
            event_task_instance_counter[name] += 1


def execute_task(task: str, instance: int, start_time: int, execution_time: int) -> int:
    """Execute a task and return its finish time."""
    affinity = runnables[task]["affinity"]
    actual_start = max(core_time[affinity], start_time)
    finish_time = actual_start + execution_time
    
    # Update execution state
    core_time[affinity] = finish_time
    execution_log_core[affinity].append((actual_start, finish_time, task, instance))
    completed_instances[task] = instance + 1
    task_last_execution[task] = finish_time
    
    return finish_time


# Main execution loop
schedule_periodic_runnables()

while event_queue:
    # Unpack task information
    priority, scheduled_time, task, execution_time, instance = heapq.heappop(event_queue)
    
    # Execute task and get finish time
    finish_time = execute_task(task, instance, scheduled_time, execution_time)
    
    # Schedule dependent tasks
    schedule_event_runnables([task], finish_time)

# Print execution results
print("\nCore 0 Schedule:")
for start, end, task, inst in execution_log_core[0]:
    print(f"[{start:4} → {end:4}] ms : {task} (instance {inst})")

print("\nCore 1 Schedule:")
for start, end, task, inst in execution_log_core[1]:
    print(f"[{start:4} → {end:4}] ms : {task} (instance {inst})")

print(f"\nTotal Execution Time: {max(core_time)} ms")
