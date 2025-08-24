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
from math import gcd, inf
from typing import Dict, Iterable, List, Optional, Set, Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


@dataclass
class ScheduleEntry:
    runnable: str
    start_time: int
    finish_time: int
    core: int
    eligible_time: int


def lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b) if a and b else max(a, b)


def lcm_list(vals: Iterable[int]) -> int:
    out = 1
    for v in vals:
        out = lcm(out, v)
    return max(out, 1)


def topology(runnables: Dict[str, Dict]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    successors: Dict[str, List[str]] = {name: [] for name in runnables}
    predecessors: Dict[str, List[str]] = {name: [] for name in runnables}
    for name, props in runnables.items():
        for dep in props.get("deps", []) or []:
            if dep in runnables:
                successors[dep].append(name)
                predecessors[name].append(dep)
    return successors, predecessors


def order_eligible(eligible: List[str], runnables: Dict[str, Dict], eta: Dict[str, int], policy: str) -> List[str]:
    policy = policy.lower()
    if policy == "pas":
        def key_fn(name: str):
            p_i = int(runnables[name].get("criticality", 0))
            return (-p_i, int(eta.get(name, 0)), name)
        return sorted(eligible, key=key_fn)
    # fcfs
    return sorted(eligible, key=lambda n: (int(eta.get(n, 0)), n))


# TODO: Update static allocation
def static_allocation(num_cores: int, p_max: int, p_avg: int) -> Tuple[int, List[int]]:
    c_alloc = max(1, min(num_cores, max(1, p_max), max(1, p_avg)))
    return list(range(c_alloc))  # lowest indices


def dynamic_allocation(idle_cores: List[int], eligible: List[str]) -> Tuple[int, List[int]]:
    c_alloc = min(len(idle_cores), len(eligible))
    return idle_cores[:c_alloc]


def compute_parallelism_bounds(runnables: Dict[str, Dict]) -> Tuple[int, int, int]:
    """Compute (W, T_CP, P_max_approx). Uses a relaxed approximation for P_max: number of sources."""
    successors, predecessors = topology(runnables)
    # Total work W (one instance per node baseline)
    W = sum(int(props.get("execution_time", 0))
            for props in runnables.values())
    # Critical path via longest path DP on DAG of single-shot graph
    # (For periodic tasks, treat as sources with EST=0)
    runnable_path_length: Dict[str, int] = {}
    remaining_runnables = set(runnables.keys())
    while remaining_runnables:
        progressed = False
        for name in list(remaining_runnables):
            if all(p in runnable_path_length for p in predecessors[name]):
                runnable_path_length[name] = max((runnable_path_length[p] + int(runnables[p]["execution_time"])
                                                  for p in predecessors[name]), default=0)
                remaining_runnables.remove(name)
                progressed = True
        if not progressed:
            # Cycles (shouldn't happen in a DAG); break conservatively
            break
    T_CP = max((runnable_path_length[n] + int(runnables[n]["execution_time"])
               for n in runnable_path_length), default=0)
    # Approx P_max: max number of simultaneously ready sources after releases -> count of nodes with no preds

    def calculate_max_parallelism() -> int:
        """Calculate P_max by finding the maximum number of eligible runnables at any time."""
        max_parallelism = 0
        completed = set()
        eligible = set()

        # Initially eligible: tasks with no dependencies or periodic sources
        for name, props in runnables.items():
            deps = props.get("deps", []) or []
            if props.get("type") == "periodic" or len(deps) == 0:
                eligible.add(name)

        max_parallelism = max(max_parallelism, len(eligible))

        while eligible:
            # Execute all eligible tasks simultaneously (unlimited cores)
            tasks_to_execute = list(eligible)
            eligible.clear()
            completed.update(tasks_to_execute)

            # Find new eligible tasks
            newly_eligible = set()
            for task in tasks_to_execute:
                for succ in successors.get(task, []):
                    if succ in completed or succ in newly_eligible:
                        continue
                    preds = runnables.get(succ, {}).get("deps", []) or []
                    if all(p in completed for p in preds):
                        newly_eligible.add(succ)

            eligible.update(newly_eligible)
            max_parallelism = max(max_parallelism, len(eligible))

        return max_parallelism

    p_max = max(1, calculate_max_parallelism())
    return W, T_CP, max(1, p_max)

# Patch: ensure next_rel considers only releases strictly after current tau to avoid stalling
# Re-run the two scenarios

# (Reusing the functions and data already defined above)


def run_main_scheduler(
    runnables: Dict[str, Dict],
    num_cores: int,
    scheduling_policy: str = "fcfs",
    allocation_policy: str = "dynamic",
    T_end: Optional[int] = None,
) -> Tuple[List[ScheduleEntry], int]:
    """Execute the main scheduling algorithm for a finite DAG per iteration.

    Returns a tuple (all_schedules, makespans):
    - all_schedules: list per iteration of ScheduleEntry list
    - makespans: list of iteration total times
    """

    successors, predecessors = topology(runnables)

    periods = [int(props.get("period", 0)) for props in runnables.values(
    ) if props.get("type") == "periodic" and int(props.get("period", 0)) > 0]
    hyperperiod = lcm_list(periods) if periods else 1
    if T_end is None:
        T_end = hyperperiod

    W, T_CP, p_max = compute_parallelism_bounds(runnables)
    p_avg = max(1, W // max(1, T_CP))

    if allocation_policy.lower() == "static":
        available_cores = static_allocation(num_cores, p_max, p_avg)
    else:
        available_cores = list(range(num_cores))

    idle_cores = list(range(num_cores))

    tau = 0
    theta: Dict[str, int] = {}
    next_active = 0
    eta: Dict[str, int] = {}
    start: Dict[str, int] = {}
    running: Dict[Tuple[str, int], Tuple[int, int]] = {}
    schedule: List[ScheduleEntry] = []
    for name, props in runnables.items():
        if props.get("type") == "periodic" and int(props.get("period", 0)) > 0:
            theta[name] = 0
        else:
            eta[name] = 0
            start[name] = 0

    tokens: Dict[Tuple[str, str], int] = {
        (p, n): 0 for n in runnables for p in predecessors[n]}

    def get_periodic_at_tau(t: int) -> List[str]:
        return sorted([n for n in theta if theta[n] == t])

    def get_event_at_tau(t: int) -> List[str]:
        return [n for n, props in runnables.items() if props.get("type") != "periodic"
                and all(tokens[(p, n)] > 0 for p in predecessors[n])
                and start[n] <= t]

    def run_periodic_now(t: int, periodic: List[str], available_cores: List[int]) -> None:
        if not periodic:
            return
        for n in periodic:
            if not available_cores:
                if running:
                    tx = min(finish for finish, _ in running.values()) - t
                else:
                    tx = 0
                start = t + tx
                theta[n] = start
                continue
            assigned_core = min(available_cores)
            available_cores.remove(assigned_core)
            idle_cores.remove(assigned_core)
            t_i = int(runnables[n]["execution_time"])
            start = t
            finish = t + t_i
            running[(n, t)] = (finish, assigned_core)
            schedule.append(ScheduleEntry(
                n, start, finish, assigned_core, eligible_time=t))
            T_i = int(runnables[n].get("period", 0))
            next_active = t + T_i
            if T_i > 0 and next_active < T_end:
                theta[n] = next_active
            else:
                theta.pop(n, None)

    while tau < T_end or running:
        # Admit periodic jobs released at tau
        eligible_event = get_event_at_tau(tau)

        if len(eligible_event) == 0 and len(idle_cores) <= 1:
            tau = next_active

        periodic_at_tau = get_periodic_at_tau(tau)

        ordered_eligible_periodic = order_eligible(periodic_at_tau, runnables, {
            e: tau for e in periodic_at_tau}, scheduling_policy)

        ordered_eligible_event = order_eligible(eligible_event, runnables, {
            e: eta[e] for e in eligible_event}, scheduling_policy)

        eligible = ordered_eligible_periodic + ordered_eligible_event

        if allocation_policy.lower() == 'dynamic':
            available_cores = dynamic_allocation(idle_cores, eligible)

        run_periodic_now(tau, ordered_eligible_periodic, available_cores)

        sorted_available_cores = list(sorted(available_cores))
        for name in ordered_eligible_event:
            start[name] = tau
            if not sorted_available_cores:
                break

            t_i = int(runnables[name]["execution_time"])
            if start[name] + t_i > next_active and start[name] <= tau:
                first_theta_key = min(theta.keys())
                start[name] = next_active + \
                    runnables[first_theta_key]["execution_time"]
            else:
                core = sorted_available_cores.pop(0)
                if core in available_cores:
                    available_cores.remove(core)
                    idle_cores.remove(core)
                running[(name, tau)] = (tau + t_i, core)
                schedule.append(ScheduleEntry(
                    name, tau, tau + t_i, core, eligible_time=tau))
                for p in predecessors[name]:
                    tokens[(p, name)] -= 1

        next_fin = min((fin for (fin, _) in running.values()), default=None)
        # strictly greater than tau
        next_active = min((t for t in theta.values() if t > tau), default=inf)
        next_decision_point = [t for t in [
            next_fin, next_active] if t is not None]
        if not next_decision_point:
            break
        tau_next = min(next_decision_point)

        # Complete any at tau_next
        for (name, eligible_time), (finish_time, core) in list(running.items()):
            if finish_time == tau_next:
                running.pop((name, eligible_time))
                if core not in idle_cores:
                    idle_cores.append(core)
                    idle_cores.sort()
                for s in successors[name]:
                    tokens[(name, s)] = tokens.get((name, s), 0) + 1
                    start[s] = finish_time
                    eta[s] = finish_time

        tau = tau_next

    finish_time = max((e.finish_time for e in schedule), default=0)
    return schedule, finish_time


def plot_schedule(log_data, title, ax):
    base_tasks = sorted(set(task for _, _, task, _, _ in log_data))
    color_palette = plt.cm.get_cmap("tab20", len(base_tasks))
    task_colors = {base_task: color_palette(
        i) for i, base_task in enumerate(base_tasks)}

    cores = list(sorted(set(core for _, _, _, _, core in log_data)))
    y_positions = {core: i for i, core in enumerate(cores)}

    for start, end, task, release, core in log_data:
        ax.barh(y_positions[core], end - start, left=start,
                color=task_colors[task], edgecolor="black")

    ax.set_yticks(range(len(cores)))
    ax.set_yticklabels([f"Core {core}" for core in cores])
    ax.set_xlabel("Time (ms)")
    ax.set_title(title)
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    handles = [mpatches.Patch(color=color, label=base_task)
               for base_task, color in task_colors.items()]
    ax.legend(handles=handles, bbox_to_anchor=(1.05, 1),
              loc='upper left', title="Runnables")


# Example runnables
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

# TODO: Double core

# Re-run
schedule_dyn, finish_dyn = run_main_scheduler(
    runnables, num_cores=2, scheduling_policy="pas", allocation_policy="dynamic", T_end=None)
schedule_static, finish_static = run_main_scheduler(
    runnables, num_cores=4, scheduling_policy="fcfs", allocation_policy="static", T_end=None)


def schedule_to_log_data(schedule: List[ScheduleEntry]):
    return [(e.start_time, e.finish_time, e.runnable, e.eligible_time, e.core) for e in schedule]


fig, axs = plt.subplots(2, 1, figsize=(16, 10), sharex=True)
plot_schedule(schedule_to_log_data(schedule_dyn),
              f"Dynamic Allocation (FCFS), finish @ {finish_dyn} ms", axs[0])
plot_schedule(schedule_to_log_data(schedule_static),
              f"Static Allocation (FCFS), finish @ {finish_static} ms", axs[1])
plt.tight_layout()
plt.show()
