"""General main scheduling algorithm with FCFS/PAS ordering and static/dynamic
core allocation, following the provided pseudocode.

Data model assumptions for `runnables` input:
- Dict[str, Dict]: each runnable has keys:
  - 'type': 'periodic' or 'event'
  - 'execution_time': int (t_i)
  - 'period': int (T_i) for periodic only (optional for event)
  - 'deps': List[str] (predecessor runnable names), optional
  - 'criticality': int used as priority p_i for PAS (default 0)

This scheduler treats a single instance of each runnable per iteration, i.e., a
finite DAG-style schedule. Periodic runnables behave as sources with eta_i = 0.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


@dataclass
class ScheduleEntry:
    runnable: str
    start: int
    finish: int
    core: int


def _topology(runnables: Dict[str, Dict]) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    successors: Dict[str, List[str]] = {name: [] for name in runnables}
    dependency_count: Dict[str, int] = {name: 0 for name in runnables}
    for name, props in runnables.items():
        for dep in props.get('deps', []) or []:
            if dep not in successors:
                continue
            successors[dep].append(name)
            dependency_count[name] += 1
    return successors, dependency_count


def _order_eligible(eligible: List[str], runnables: Dict[str, Dict], eta: Dict[str, int], policy: str) -> List[str]:
    if policy.lower() == 'pas':
        # Higher p_i first, then lower eta, then name
        def key_fn(name: str):
            p_i = int(runnables.get(name, {}).get('criticality', 0))
            return (-p_i, int(eta.get(name, 0)), name)
        return sorted(eligible, key=key_fn)
    # FCFS: order by (eta_i, id)
    return sorted(eligible, key=lambda n: (int(eta.get(n, 0)), n))


def _static_allocation(num_cores: int, p_max: int, p_avg: int) -> Tuple[int, List[int]]:
    c_alloc = min(num_cores, max(0, p_max), max(0, p_avg))
    idle = list(range(c_alloc))
    return c_alloc, idle


def _dynamic_allocation(idle_cores: List[int], eligible: List[str]) -> Tuple[int, List[int]]:
    alloc = min(len(idle_cores), len(eligible))
    return alloc, idle_cores[:alloc]


def _calculate_iteration_period(runnables: Dict[str, Dict]) -> int:
    """Calculate the minimum period for iteration boundaries."""
    periods = []
    for name, props in runnables.items():
        if props.get('type') == 'periodic':
            period = props.get('period', 0)
            if period > 0:
                periods.append(period)

    if not periods:
        return 1  # Default if no periodic runnables

    # Return the minimum period (most frequent activation)
    return min(periods)


def run_main_scheduler(
    runnables: Dict[str, Dict],
    num_cores: int,
    scheduling_policy: str = 'fcfs',
    allocation_policy: str = 'dynamic',
    iterations: int = 1,
) -> Tuple[List[List[ScheduleEntry]], List[int]]:
    """Execute the main scheduling algorithm for a finite DAG per iteration.

    Returns a tuple (all_schedules, makespans):
    - all_schedules: list per iteration of ScheduleEntry list
    - makespans: list of iteration total times
    """

    successors, dependency_count = _topology(runnables)

    # Calculate maximum parallelism by simulating the execution
    def calculate_max_parallelism():
        """Calculate P_max by finding the maximum number of eligible runnables at any time."""
        max_parallelism = 0
        completed = set()
        eligible = set()

        # Initialize eligible set with tasks that have no dependencies
        for name, props in runnables.items():
            deps = props.get('deps', []) or []
            if props.get('type') == 'periodic' or len(deps) == 0:
                eligible.add(name)

        max_parallelism = max(max_parallelism, len(eligible))

        # Simulate execution to find maximum parallelism
        while eligible:
            # Execute all eligible tasks simultaneously (since we have unlimited cores)
            tasks_to_execute = list(eligible)
            for task in tasks_to_execute:
                eligible.remove(task)
                completed.add(task)

            # Add newly eligible tasks after all current tasks complete
            newly_eligible = set()
            for task in tasks_to_execute:
                for succ in successors.get(task, []):
                    if succ in completed or succ in newly_eligible:
                        continue
                    # Check if all dependencies are completed
                    preds = runnables.get(succ, {}).get('deps', []) or []
                    if all(p in completed for p in preds):
                        newly_eligible.add(succ)

            eligible.update(newly_eligible)
            max_parallelism = max(max_parallelism, len(eligible))

        return max_parallelism

    p_max = max(1, calculate_max_parallelism())

    # Calculate average parallelism: P_avg = floor(W / T_CP)
    def calculate_critical_path_length():
        """Calculate T_CP by finding the longest path from any source to any sink."""
        # Calculate earliest start times for all tasks
        earliest_start = {}

        # Initialize with tasks that have no dependencies
        for name, props in runnables.items():
            deps = props.get('deps', []) or []
            if props.get('type') == 'periodic' or len(deps) == 0:
                earliest_start[name] = 0

        # Process tasks in topological order
        processed = set()
        while len(processed) < len(runnables):
            for name, props in runnables.items():
                if name in processed:
                    continue

                deps = props.get('deps', []) or []
                if all(dep in earliest_start for dep in deps):
                    # All dependencies have been processed
                    max_pred_finish = 0
                    for dep in deps:
                        dep_finish = earliest_start[dep] + \
                            runnables[dep]['execution_time']
                        max_pred_finish = max(max_pred_finish, dep_finish)

                    earliest_start[name] = max_pred_finish
                    processed.add(name)

        # Find the maximum finish time (critical path length)
        max_finish = 0
        for name, props in runnables.items():
            finish_time = earliest_start[name] + props['execution_time']
            max_finish = max(max_finish, finish_time)

        return max_finish

    def calculate_total_work():
        """Calculate W = sum of all execution times."""
        return sum(props['execution_time'] for props in runnables.values())

    T_CP = calculate_critical_path_length()
    W = calculate_total_work()
    p_avg = max(1, W // T_CP)  # floor division

    all_iterations: List[List[ScheduleEntry]] = []
    makespans: List[int] = []
    cumulative_offset = 0

    # Calculate iteration period (minimum period) for iteration boundaries
    iteration_period = _calculate_iteration_period(runnables)
    print(f"Calculated iteration period: {iteration_period}ms")

    for _k in range(max(1, iterations)):
        # TODO: tau should not get reset to 0 every iteration
        tau = 0
        completed: Set[str] = set()
        running: Dict[str, Tuple[int, int]] = {}  # name -> (finish, core)

        # Per-core next activation time for periodic tasks
        theta: Dict[Tuple[str, int], int] = {}

        # Activation times (eta_i)
        eta: Dict[str, int] = {name: 0 for name in runnables}

        # Eligible set initialization
        eligible: Dict[str, Tuple[int, int]] = {}  # name -> (eta, iteration)
        for name, props in runnables.items():
            deps = props.get('deps', []) or []
            if props.get('type') == 'periodic' or len(deps) == 0:
                # TODO: eta.get(name, tau) ? / eta.get(name, eta))
                eligible[name] = (eta.get(name, 0), _k +
                                  1)  # Current iteration

        # Idle cores
        if allocation_policy.lower() == 'static':
            c_alloc, idle_cores = _static_allocation(num_cores, p_max, p_avg)
        else:
            c_alloc, idle_cores = 0, list(range(num_cores))

        schedule_out: List[ScheduleEntry] = []

        while len(completed) < len(runnables):
            # Filter eligible: remove completed/running only for current iteration runnables
            eligible = {
                name: (eta_val, iteration) for name, (eta_val, iteration) in eligible.items()
                if (iteration == _k + 1 and name not in completed and name not in running) or (iteration != _k + 1)
            }
            ordered = _order_eligible(
                list(eligible), runnables, eta, scheduling_policy)

            # Dynamic allocation if requested
            available_cores = idle_cores
            if allocation_policy.lower() == 'dynamic':
                c_alloc, available_cores = _dynamic_allocation(
                    idle_cores, ordered)

            # TODO: only consider ordered for current iteration runnables
            ready = ordered[:c_alloc] if c_alloc > 0 else []

            # Dispatch ready
            for name in ready:
                if name in running:
                    continue
                props = runnables[name]
                t_i = int(props.get('execution_time', 0))
                T_i = int(props.get('period', 0)) if props.get(
                    'type') == 'periodic' else 0

                eligible.pop(name)

                # Select a core
                assigned_core: Optional[int] = None
                if props.get('type') == 'periodic' and int(eta.get(name, 0)) == tau and available_cores:
                    assigned_core = min(available_cores)
                    available_cores.remove(assigned_core)
                    idle_cores.remove(assigned_core)
                    if T_i > 0:
                        theta[(name, assigned_core)] = tau + T_i
                    start_i = tau
                    finish_i = tau + t_i
                    # Add next activation time to eligible
                    eta[name] = start_i + T_i
                    # Next iteration for periodic runnables
                    eligible[name] = (eta[name], _k + 2)
                else:
                    # Try to find a core that satisfies strict periodicity guard for periodic; events always ok
                    for c in list(available_cores):
                        safe = True
                        if props.get('type') == 'periodic' and T_i > 0:
                            next_act = theta.get((name, c), tau + T_i)
                            safe = (tau + t_i) <= next_act
                        if safe:
                            assigned_core = c
                            available_cores.remove(c)
                            idle_cores.remove(c)
                            start_i = tau
                            finish_i = tau + t_i
                            break
                    # If none safe, skip dispatching this task in this round
                    if assigned_core is None:
                        continue

                running[name] = (finish_i, assigned_core)
                schedule_out.append(ScheduleEntry(
                    name, start_i, finish_i, assigned_core))

            if not running:
                # Nothing could be dispatched; advance time to next activation or break to avoid infinite loop
                # Attempt to advance to the smallest eta among remaining eligible
                if eligible:
                    tau = min(eta_val for eta_val, _ in eligible.values())
                    continue
                else:
                    break

            # Advance time to the next finish
            min_finish = min(fin for fin, _ in running.values())

            # Get minimum activation time of periodic runnables in eligible set
            periodic_eligible = [n for n in eligible.keys() if runnables.get(
                n, {}).get('type') == 'periodic']

            # If eligible set contains only periodic runnables, consider their activation times
            if len(periodic_eligible) == len(eligible) and len(eligible) > 0:
                # Find the periodic runnable with minimum eta
                min_eta_runnable = min(
                    periodic_eligible, key=lambda n: eligible[n][0])
                min_eta_iteration = eligible[min_eta_runnable][1]

                # Only consider periodic activation times if the min eta runnable has same iteration
                if min_eta_iteration == _k + 1:
                    # Get eta value from tuple
                    min_eligible = min(eligible[n][0]
                                       for n in periodic_eligible)
                    tau = max(min_finish, min_eligible)
                else:
                    # If min eta runnable is from different iteration, just advance to next finish
                    tau = min_finish
            else:
                # If there are non-periodic runnables, just advance to next finish
                tau = min_finish

            # Complete tasks finishing at tau
            just_finished = [n for n, (fin, _) in list(
                running.items()) if fin == tau]
            for name in just_finished:
                fin, core = running.pop(name)
                completed.add(name)
                # Release core
                if core not in idle_cores:
                    idle_cores.append(core)
                    idle_cores.sort()
                # Propagate to successors
                for succ in successors.get(name, []):
                    if succ in completed:
                        continue
                    eta[succ] = tau
                    if succ not in eligible and succ not in running:
                        # Check if all preds of succ are completed
                        preds = runnables.get(succ, {}).get('deps', []) or []
                        if all(p in completed for p in preds):
                            # Current iteration
                            eligible[succ] = (eta[succ], _k + 1)

        # Adjust start and finish times to be cumulative
        for entry in schedule_out:
            entry.start += cumulative_offset
            entry.finish += cumulative_offset

        all_iterations.append(schedule_out)
        # Makespan is the iteration period (since next iteration starts at this boundary)
        makespans.append(iteration_period)
        # Next iteration starts at iteration period boundary
        cumulative_offset += iteration_period

    print(f"Makespan: {sum(makespans)}")
    print(f"All schedule entries:")
    # Flatten all iterations into one list
    all_entries = []
    for schedule in all_iterations:
        all_entries.extend(schedule)
    # Print each entry on its own line
    for entry in all_entries:
        print(f"  {entry}")

    return all_iterations, makespans


def plot_schedule(log_data, title, ax):
    """Plot schedule data as a Gantt chart."""
    # Extract base task names (remove _iter suffix for legend)
    base_tasks = sorted(
        set(task.split('_iter')[0] for _, _, task, _, _ in log_data))
    color_palette = plt.cm.get_cmap("tab20", len(base_tasks))
    task_colors = {base_task: color_palette(
        i) for i, base_task in enumerate(base_tasks)}

    cores = list(sorted(set(core for _, _, _, _, core in log_data), key=str))
    y_positions = {core: i for i, core in enumerate(cores)}

    for start, end, task, instance, core in log_data:
        base_task = task.split('_iter')[0]  # Get base task name for color
        ax.barh(y_positions[core], end - start, left=start,
                color=task_colors[base_task], edgecolor="black")

    ax.set_yticks(range(len(cores)))
    ax.set_yticklabels([f"Core {core}" for core in cores])
    ax.set_xlabel("Time (ms)")
    ax.set_title(title)
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    handles = [mpatches.Patch(color=color, label=base_task)
               for base_task, color in task_colors.items()]
    ax.legend(handles=handles, bbox_to_anchor=(1.05, 1),
              loc='upper left', title="Runnables")


# Use case: Automotive system runnables
runnables = {
    'RadarCapture': {
        'criticality': 1,
        'period': 75,
        'execution_time': 2,
        'type': 'periodic',
        'deps': []
    },
    'CameraCapture': {
        'criticality': 0,
        'period': 50,
        'execution_time': 7,
        'type': 'periodic',
        'deps': []
    },
    'SensorFusion': {
        'criticality': 1,
        'execution_time': 6,
        'type': 'event',
        'deps': ['RadarCapture', 'CameraCapture'],
    },
    'ObjectDetection': {
        'criticality': 1,
        'execution_time': 15,
        'type': 'event',
        'deps': ['SensorFusion'],
    },
    'TrajectoryPrediction': {
        'criticality': 1,
        'execution_time': 8,
        'type': 'event',
        'deps': ['ObjectDetection'],
    },
    'CollisionRiskAssessment': {
        'criticality': 2,
        'execution_time': 3,
        'type': 'event',
        'deps': ['TrajectoryPrediction'],
    },
    'EmergencyBrakeDecision': {
        'criticality': 2,
        'execution_time': 2,
        'type': 'event',
        'deps': ['CollisionRiskAssessment'],
    },
    'ActuatorControl': {
        'criticality': 2,
        'execution_time': 1,
        'type': 'event',
        'deps': ['EmergencyBrakeDecision'],
    },
    'LaneMarkingDetection': {
        'criticality': 1,
        'execution_time': 6,
        'type': 'event',
        'deps': ['CameraCapture'],
    },
    'VehiclePositionEstimation': {
        'criticality': 1,
        'execution_time': 4,
        'type': 'event',
        'deps': ['LaneMarkingDetection'],
    },
    'LaneDepartureWarning': {
        'criticality': 1,
        'execution_time': 2,
        'type': 'event',
        'deps': ['VehiclePositionEstimation'],
    },
    'SteeringAngleCalculation': {
        'criticality': 1,
        'execution_time': 2,
        'type': 'event',
        'deps': ['VehiclePositionEstimation'],
    },
    'SteeringActuatorControl': {
        'criticality': 2,
        'execution_time': 1,
        'type': 'event',
        'deps': ['LaneDepartureWarning', 'SteeringAngleCalculation'],
    },
}

# Run the main scheduler with specified parameters
num_cores = 6
iterations = 6
scheduling_policy = "pas"
allocation_policy = "dynamic"

print(f"Running main scheduler with:")
print(f"  Cores: {num_cores}")
print(f"  Iterations: {iterations}")
print(f"  Scheduling Policy: {scheduling_policy}")
print(f"  Allocation Policy: {allocation_policy}")
print()

all_schedules, makespans = run_main_scheduler(
    runnables,
    num_cores,
    scheduling_policy,
    allocation_policy,
    iterations
)

# Visualization
print("\n" + "="*60)
print("VISUALIZATION")
print("="*60)

# Convert ScheduleEntry objects to log format for visualization


def schedule_to_log_data(schedule_entries):
    """Convert ScheduleEntry objects to log data format for plotting."""
    return [(entry.start, entry.finish, entry.runnable, 0, entry.core)
            for entry in schedule_entries]


# Plot all iterations in a single cumulative figure
plt.figure(figsize=(16, 8))
ax = plt.gca()

# Flatten all iterations into one continuous schedule
all_log_data = []
for i, schedule in enumerate(all_schedules):
    log_data = schedule_to_log_data(schedule)
    # Tasks are already cumulative from the scheduler, just add iteration labels
    offset_log_data = [(start, end, f"{task}_iter{i+1}", 0, core)
                       for start, end, task, _, core in log_data]
    all_log_data.extend(offset_log_data)

plot_schedule(
    all_log_data,
    f"Main Scheduler - All {len(all_schedules)} Iterations (FCFS, Dynamic Allocation, {num_cores} Cores)",
    # f"Main Scheduler - All {len(all_schedules)} Iterations (PAS, {num_cores} Core)",
    ax
)
plt.tight_layout()
plt.show()
