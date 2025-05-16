"""Task scheduling simulation with CPU affinity and periodic constraints."""
import heapq
from collections import defaultdict

from driving_mock import execution_log, runnables

core0_queue = []
core1_queue = []
heapq.heapify(core0_queue)
heapq.heapify(core1_queue)

CORE0_TIME = 0
CORE1_TIME = 0
last_periodic_time = defaultdict(int)
task_instances = defaultdict(int)
execution_log_core0 = []
execution_log_core1 = []
last_completion_time = defaultdict(int)

extracted_log = execution_log.get_log()

for start, end, name, instance, affinity in extracted_log:
    props = runnables[name]
    execution_time = props['execution_time']

    if props['type'] == 'periodic':
        if (start > 0 and
            start < last_periodic_time[name] + props['period'] and
                last_periodic_time[name] > 0):
            continue
        last_periodic_time[name] = start
        actual_start = max(CORE0_TIME if affinity == 0 else CORE1_TIME, start)
    else:
        deps = props.get('deps', [])
        if deps:
            dep_completion_time = max(
                last_completion_time[dep] for dep in deps)
            actual_start = max(CORE0_TIME if affinity ==
                               0 else CORE1_TIME, dep_completion_time)
        else:
            actual_start = max(CORE0_TIME if affinity ==
                               0 else CORE1_TIME, start)

    if affinity == 0:
        heapq.heappush(core0_queue, (actual_start,
                       name, execution_time, instance))
        CORE0_TIME = actual_start + execution_time
        execution_log_core0.append((actual_start, CORE0_TIME, name, instance))
        last_completion_time[name] = CORE0_TIME
    else:
        heapq.heappush(core1_queue, (actual_start,
                       name, execution_time, instance))
        CORE1_TIME = actual_start + execution_time
        execution_log_core1.append((actual_start, CORE1_TIME, name, instance))
        last_completion_time[name] = CORE1_TIME

print("\nCore 0 Schedule:")
for start, end, name, instance in execution_log_core0:
    print(f"[{start:4} → {end:4}] ms : {name} (instance {instance})")

print("\nCore 1 Schedule:")
for start, end, name, instance in execution_log_core1:
    print(f"[{start:4} → {end:4}] ms : {name} (instance {instance})")

print(f"\nTotal Execution Time: {max(CORE0_TIME, CORE1_TIME)} ms")
