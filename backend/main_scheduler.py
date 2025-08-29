"""General main scheduling algorithm with FCFS/PAS ordering and static/dynamic
core allocation, following the provided pseudocode.

Data model assumptions for `runnables` input:
- Dict[str, Dict]: each runnable has keys:
  - 'type': 'periodic' or 'event'
  - 'execution_time': int (t_i)
  - 'period': int (T_i) for periodic only (optional for event)
  - 'deps': List[str] (predecessor runnable names), optional
  - 'priority': int used as priority p_i for PAS (default 0)

This scheduler treats a single instance of each runnable per iteration, i.e., a
finite DAG-style schedule. Periodic runnables behave as sources with eta_i = 0.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from math import ceil, inf
from typing import Dict, List, Optional, Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


@dataclass
class ScheduleEntry:
    runnable: str
    start_time: int
    finish_time: int
    core: int
    eligible_time: int


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
            p_i = int(runnables[name].get("priority", 0))
            return (-p_i, int(eta.get(name, 0)), name)
        return sorted(eligible, key=key_fn)
    # fcfs
    return sorted(eligible, key=lambda n: (int(eta.get(n, 0)), n))


def static_allocation(num_cores: int, p_max: int, n_min: int) -> List[int]:
    c_alloc = max(1, min(num_cores, p_max, n_min))
    return list(range(c_alloc))  # lowest indices


def dynamic_allocation(idle_cores: List[int], eligible: List[str]) -> Tuple[int, List[int]]:
    c_alloc = min(len(idle_cores), len(eligible))
    return idle_cores[:c_alloc]


def compute_total_work(runnables: Dict[str, Dict]) -> int:
    return sum(int(props.get("execution_time", 0))
               for props in runnables.values())


def compute_parallelism_bounds(runnables: Dict[str, Dict], num_cores: int) -> Tuple[int, int]:
    """Compute (W, T_CP, P_max_approx). Uses a relaxed approximation for P_max: number of sources."""
    successors, predecessors = topology(runnables)
    # Total work W (one instance per node baseline)
    W = compute_total_work(runnables)
    # Critical path via longest path DP on DAG of single-shot graph
    # (For periodic Runnables, treat as sources with EST=0)
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

        # Initially eligible: Runnables with no dependencies or periodic sources
        for name, props in runnables.items():
            deps = props.get("deps", []) or []
            if props.get("type") == "periodic" or len(deps) == 0:
                eligible.add(name)

        max_parallelism = max(max_parallelism, len(eligible))

        while eligible:
            # Execute all eligible Runnables simultaneously (unlimited cores)
            Runnables_to_execute = list(eligible)
            eligible.clear()
            completed.update(Runnables_to_execute)

            # Find new eligible Runnables
            newly_eligible = set()
            for Runnable in Runnables_to_execute:
                for succ in successors.get(Runnable, []):
                    if succ in completed or succ in newly_eligible:
                        continue
                    preds = runnables.get(succ, {}).get("deps", []) or []
                    if all(p in completed for p in preds):
                        newly_eligible.add(succ)

            eligible.update(newly_eligible)
            max_parallelism = max(max_parallelism, len(eligible))

        return max(max_parallelism, 1)

    p_max = calculate_max_parallelism()

    def calculate_min_core_count(
        num_cores: int,
        total_work: int,
        critical_path: int,
        epsilon: float = 0.9,
    ) -> int:
        """Compute N_min = ceil( (epsilon * p) / (s * (1 - epsilon)) ) per DAG-aware Amdahl's law.

        Handles edge cases: if W == 0 -> allocate 1; if s == 0 -> N_min treated as num_cores.
        """
        # Guard: no work
        if total_work <= 0:
            return 1

        # Compute serial/parallel fractions
        s_fraction = critical_path / total_work
        s_fraction = max(0.0, min(1.0, s_fraction))
        p_fraction = max(0.0, 1.0 - s_fraction)

        # Compute N_min; handle s == 0 (perfect parallelism) by allowing up to available cores
        if s_fraction == 0.0:
            minimal_core_count = num_cores
        else:
            # Avoid division by zero for epsilon extremes
            eps = min(max(epsilon, 1e-9), 1 - 1e-9)
            minimal_core_count = ceil(
                (eps * p_fraction) / (s_fraction * (1.0 - eps)))
            minimal_core_count = max(1, minimal_core_count)

        return minimal_core_count

    n_min = calculate_min_core_count(num_cores, W, T_CP)

    return p_max, n_min

# Patch: ensure next_rel considers only releases strictly after current tau to avoid stalling
# Re-run the two scenarios

# (Reusing the functions and data already defined above)


def run_main_scheduler(
    runnables: Dict[str, Dict],
    num_cores: int,
    scheduling_policy: str = "fcfs",
    allocation_policy: str = "dynamic",
    I: Optional[int] = None,
) -> Tuple[List[ScheduleEntry], int, int]:
    """Execute the main scheduling algorithm for a finite DAG per iteration.

    Returns a tuple (all_schedules, makespans):
    - all_schedules: list per iteration of ScheduleEntry list
    - makespans: list of iteration total times
    """

    successors, predecessors = topology(runnables)

    total_work = compute_total_work(runnables)
    if I is None:
        T_end = 2 * total_work
    else:
        T_end = I * total_work

    p_max, n_min = compute_parallelism_bounds(runnables, num_cores)

    if allocation_policy.lower() == "static":
        available_cores = static_allocation(num_cores, p_max, n_min)
    else:
        available_cores = list(range(num_cores))

    idle_cores = list(range(num_cores))

    tau = 0
    phi: Dict[str, int] = {}
    next_active = 0
    eta: Dict[str, int] = {}
    start: Dict[str, int] = {}
    running: Dict[Tuple[str, int], Tuple[int, int]] = {}
    schedule: List[ScheduleEntry] = []
    for name, props in runnables.items():
        if props.get("type") == "periodic" and int(props.get("period", 0)) > 0:
            phi[name] = 0
        else:
            eta[name] = 0
            start[name] = 0

    tokens: Dict[Tuple[str, str], int] = {
        (p, n): 0 for n in runnables for p in predecessors[n]}

    def get_periodic_at_tau(t: int) -> List[str]:
        return sorted([n for n in phi if phi[n] == t])

    def get_event_at_tau(t: int) -> List[str]:
        return [n for n, props in runnables.items() if props.get("type") != "periodic"
                and all(tokens[(p, n)] > 0 for p in predecessors[n])
                and start[n] <= t]

    def run_periodic_now(t: int, periodic: List[str], available_cores: List[int]) -> None:
        nonlocal total_delay
        if not periodic:
            return
        for n in periodic:
            if not available_cores:
                if running:
                    tx = min(finish for finish, _ in running.values()) - t
                else:
                    tx = 0
                total_delay += tx
                start = t + tx
                phi[n] = start
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
            # print(ScheduleEntry(
            #     n, start, finish, assigned_core, eligible_time=t))
            T_i = int(runnables[n].get("period", 0))
            next_active = t + T_i
            if T_i > 0 and next_active < T_end:
                phi[n] = next_active
            else:
                phi.pop(n, None)

    total_delay = 0
    while tau < T_end:
        # Admit periodic jobs released at tau
        eligible_event = get_event_at_tau(tau)

        if len(eligible_event) == 0 and num_cores <= 1:
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

            if tau + t_i > T_end:
                break

            if phi and start[name] + t_i > next_active and start[name] <= tau:
                first_phi_key = min(phi.keys())
                delayed_start_time = next_active + \
                    runnables[first_phi_key]["execution_time"]
                total_delay += delayed_start_time - start[name]
                start[name] = delayed_start_time
            else:
                core = sorted_available_cores.pop(0)
                if core in available_cores:
                    available_cores.remove(core)
                    idle_cores.remove(core)
                running[(name, tau)] = (tau + t_i, core)
                schedule.append(ScheduleEntry(
                    name, tau, tau + t_i, core, eligible_time=tau))
                # print(ScheduleEntry(
                #     name, tau, tau + t_i, core, eligible_time=tau))
                for p in predecessors[name]:
                    tokens[(p, name)] -= 1

        next_fin = min((fin for (fin, _) in running.values()), default=None)
        # strictly greater than tau
        next_active = min((t for t in phi.values() if t > tau), default=inf)
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
                if allocation_policy.lower() == "static":
                    available_cores.append(core)
                    available_cores.sort()
                for s in successors[name]:
                    tokens[(name, s)] = tokens.get((name, s), 0) + 1
                    start[s] = finish_time
                    eta[s] = finish_time

        tau = tau_next

    finish_time = max((e.finish_time for e in schedule), default=0)
    return schedule, finish_time, total_delay


def plot_schedule(log_data, title, ax, color_mapping=None, total_cores=None):
    base_Runnables = sorted(set(Runnable for _, _, Runnable, _, _ in log_data))

    if color_mapping is None:
        color_palette = plt.cm.get_cmap("tab20", len(base_Runnables))
        color_mapping = {base_Runnable: color_palette(
            i) for i, base_Runnable in enumerate(base_Runnables)}

    # Always include all cores if total_cores provided; otherwise, only used cores
    cores = list(range(total_cores)) if total_cores is not None else \
        list(sorted(set(core for _, _, _, _, core in log_data)))

    y_positions = {core: i for i, core in enumerate(cores)}

    for start, end, Runnable, release, core in log_data:
        ax.barh(y_positions[core], end - start, left=start,
                color=color_mapping[Runnable], edgecolor="black")

    ax.set_yticks(range(len(cores)))
    ax.set_yticklabels([f"Core {core}" for core in cores], fontsize=14)
    ax.set_ylim(-0.5, len(cores) - 0.5)
    ax.set_xlabel("Time (ms)", fontsize=14)
    ax.set_title(title, fontsize=18)
    ax.tick_params(axis='both', labelsize=14)
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)

    def transform_label(label):
        if label.startswith('Runnable'):
            try:
                number = int(label[8:])
                return f"runnable {number}"
            except:
                return label
        return label

    def get_runnable_number(runnable):
        if runnable.startswith('Runnable'):
            try:
                return int(runnable[8:])
            except:
                return float('inf')
        return float('inf')

    sorted_runnables = sorted(base_Runnables, key=get_runnable_number)
    handles = [mpatches.Patch(color=color_mapping[runnable], label=transform_label(runnable))
               for runnable in sorted_runnables]
    ax.legend(handles=handles, bbox_to_anchor=(1.05, 1),
              loc='upper left', title="Runnables", fontsize=14, title_fontsize=18)

    return color_mapping


# Example runnables
runnables = {
    'RadarCapture': {
        'priority': 1,
        'period': 75,
        'execution_time': 2,
        'type': 'periodic',
        'deps': []
    },
    'CameraCapture': {
        'priority': 0,
        'period': 50,
        'execution_time': 7,
        'type': 'periodic',
        'deps': []
    },
    'SensorFusion': {
        'priority': 1,
        'execution_time': 6,
        'type': 'event',
        'deps': ['RadarCapture', 'CameraCapture'],
    },
    'ObjectDetection': {
        'priority': 1,
        'execution_time': 15,
        'type': 'event',
        'deps': ['SensorFusion'],
    },
    'TrajectoryPrediction': {
        'priority': 1,
        'execution_time': 8,
        'type': 'event',
        'deps': ['ObjectDetection'],
    },
    'CollisionRiskAssessment': {
        'priority': 2,
        'execution_time': 3,
        'type': 'event',
        'deps': ['TrajectoryPrediction'],
    },
    'EmergencyBrakeDecision': {
        'priority': 2,
        'execution_time': 2,
        'type': 'event',
        'deps': ['CollisionRiskAssessment'],
    },
    'ActuatorControl': {
        'priority': 2,
        'execution_time': 1,
        'type': 'event',
        'deps': ['EmergencyBrakeDecision'],
    },
    'LaneMarkingDetection': {
        'priority': 1,
        'execution_time': 6,
        'type': 'event',
        'deps': ['CameraCapture'],
    },
    'VehiclePositionEstimation': {
        'priority': 1,
        'execution_time': 4,
        'type': 'event',
        'deps': ['LaneMarkingDetection'],
    },
    'LaneDepartureWarning': {
        'priority': 1,
        'execution_time': 2,
        'type': 'event',
        'deps': ['VehiclePositionEstimation'],
    },
    'SteeringAngleCalculation': {
        'priority': 1,
        'execution_time': 2,
        'type': 'event',
        'deps': ['VehiclePositionEstimation'],
    },
    'SteeringActuatorControl': {
        'priority': 2,
        'execution_time': 1,
        'type': 'event',
        'deps': ['LaneDepartureWarning', 'SteeringAngleCalculation'],
    },

    # 'DistanceEstimation': {
    #     'priority': 1,
    #     'execution_time': 5,
    #     'type': 'event',
    #     'deps': ['ObjectDetection'],
    # },
    # 'RelativeSpeedEstimation': {
    #     'priority': 1,
    #     'execution_time': 4,
    #     'type': 'event',
    #     'deps': ['ObjectDetection'],
    # },
    # 'AdaptiveCruiseControlDecision': {
    #     'priority': 2,
    #     'execution_time': 6,
    #     'type': 'event',
    #     'deps': ['DistanceEstimation', 'RelativeSpeedEstimation'],
    # },
    # 'ThrottleControl': {
    #     'priority': 2,
    #     'execution_time': 2,
    #     'type': 'event',
    #     'deps': ['AdaptiveCruiseControlDecision'],
    # },
    # 'BrakeControl': {
    #     'priority': 2,
    #     'execution_time': 2,
    #     'type': 'event',
    #     'deps': ['AdaptiveCruiseControlDecision'],
    # },
}

runnables_long_path = {
    'Runnable1':  {'priority': 1, 'execution_time': 15, 'type': 'periodic', 'period': 100, 'deps': []},
    'Runnable2':  {'priority': 2, 'execution_time': 20, 'type': 'periodic', 'period': 180, 'deps': []},

    'Runnable3':  {'priority': 1, 'execution_time': 25, 'type': 'event', 'deps': ['Runnable1']},
    'Runnable4':  {'priority': 4, 'execution_time': 30, 'type': 'event', 'deps': ['Runnable3']},
    'Runnable5':  {'priority': 3, 'execution_time': 20, 'type': 'event', 'deps': ['Runnable4']},
    'Runnable6':  {'priority': 1, 'execution_time': 35, 'type': 'event', 'deps': ['Runnable5']},

    'Runnable7':  {'priority': 2, 'execution_time': 40, 'type': 'event', 'deps': ['Runnable6']},
    'Runnable8':  {'priority': 1, 'execution_time': 25, 'type': 'event', 'deps': ['Runnable7']},
    'Runnable9':  {'priority': 0, 'execution_time': 30, 'type': 'event', 'deps': ['Runnable8']},
    'Runnable10': {'priority': 4, 'execution_time': 20, 'type': 'event', 'deps': ['Runnable9']},

    'Runnable11': {'priority': 2, 'execution_time': 45, 'type': 'event', 'deps': ['Runnable10']},
    'Runnable12': {'priority': 0, 'execution_time': 30, 'type': 'event', 'deps': ['Runnable11']},
    'Runnable13': {'priority': 3, 'execution_time': 35, 'type': 'event', 'deps': ['Runnable12']},

    'Runnable14': {'priority': 1, 'execution_time': 25, 'type': 'event', 'deps': ['Runnable13']},
    'Runnable15': {'priority': 3, 'execution_time': 40, 'type': 'event', 'deps': ['Runnable14']},
    'Runnable16': {'priority': 3, 'execution_time': 20, 'type': 'event', 'deps': ['Runnable15']},

    'Runnable17': {'priority': 4, 'execution_time': 50, 'type': 'event', 'deps': ['Runnable16']},
    'Runnable18': {'priority': 1, 'execution_time': 25, 'type': 'event', 'deps': ['Runnable17']},

    'Runnable19': {'priority': 4, 'execution_time': 35, 'type': 'event', 'deps': ['Runnable18']},
    'Runnable20': {'priority': 2, 'execution_time': 30, 'type': 'event', 'deps': ['Runnable19']},
}

runnables_balanced = {
    'Runnable1':  {'priority': 1, 'execution_time': 15, 'type': 'periodic', 'period': 100, 'deps': []},
    'Runnable2':  {'priority': 2, 'execution_time': 20, 'type': 'periodic', 'period': 180, 'deps': []},

    'Runnable3':  {'priority': 1, 'execution_time': 25, 'type': 'event', 'deps': ['Runnable1']},
    'Runnable4':  {'priority': 4, 'execution_time': 30, 'type': 'event', 'deps': ['Runnable1']},
    'Runnable5':  {'priority': 3, 'execution_time': 20, 'type': 'event', 'deps': ['Runnable2']},
    'Runnable6':  {'priority': 1, 'execution_time': 35, 'type': 'event', 'deps': ['Runnable2']},

    'Runnable7':  {'priority': 2, 'execution_time': 40, 'type': 'event', 'deps': ['Runnable3', 'Runnable4']},
    'Runnable8':  {'priority': 1, 'execution_time': 25, 'type': 'event', 'deps': ['Runnable5', 'Runnable6']},
    'Runnable9':  {'priority': 0, 'execution_time': 30, 'type': 'event', 'deps': ['Runnable3']},
    'Runnable10': {'priority': 4, 'execution_time': 20, 'type': 'event', 'deps': ['Runnable4']},

    'Runnable11': {'priority': 2, 'execution_time': 45, 'type': 'event', 'deps': ['Runnable7']},
    'Runnable12': {'priority': 0, 'execution_time': 30, 'type': 'event', 'deps': ['Runnable8']},
    'Runnable13': {'priority': 3, 'execution_time': 35, 'type': 'event', 'deps': ['Runnable9', 'Runnable10']},

    'Runnable14': {'priority': 1, 'execution_time': 25, 'type': 'event', 'deps': ['Runnable11']},
    'Runnable15': {'priority': 3, 'execution_time': 40, 'type': 'event', 'deps': ['Runnable12']},
    'Runnable16': {'priority': 3, 'execution_time': 20, 'type': 'event', 'deps': ['Runnable13']},

    'Runnable17': {'priority': 4, 'execution_time': 50, 'type': 'event', 'deps': ['Runnable14', 'Runnable15']},
    'Runnable18': {'priority': 1, 'execution_time': 25, 'type': 'event', 'deps': ['Runnable16']},

    'Runnable19': {'priority': 4, 'execution_time': 35, 'type': 'event', 'deps': ['Runnable17', 'Runnable18']},
    'Runnable20': {'priority': 2, 'execution_time': 30, 'type': 'event', 'deps': ['Runnable19']},
}

testing_runnables = runnables_balanced

# Re-run (disabled to only show sweep plots later)
schedule_dyn, finish_dyn, wait_extra_dyn = run_main_scheduler(
    testing_runnables, num_cores=6, scheduling_policy="fcf  s", allocation_policy="dynamic", I=3)
schedule_static, finish_static, wait_extra_static = run_main_scheduler(
    testing_runnables, num_cores=6, scheduling_policy="fcfs", allocation_policy="static", I=3)


def schedule_to_log_data(schedule: List[ScheduleEntry]):
    return [(e.start_time, e.finish_time, e.runnable, e.eligible_time, e.core) for e in schedule]


# Create consistent color mapping
all_runnables = set()
for runnable in runnables_long_path.keys():
    all_runnables.add(runnable)
all_runnables = sorted(all_runnables, key=lambda x: int(
    x[8:]) if x.startswith('Runnable') else float('inf'))

color_palette = plt.cm.get_cmap("tab20", len(all_runnables))
consistent_color_mapping = {runnable: color_palette(
    i) for i, runnable in enumerate(all_runnables)}

# Plot dynamic schedule (disabled; we will show only sweep plots)
fig_dyn, ax_dyn = plt.subplots(1, 1, figsize=(19.20, 10.80), sharex=True)
plot_schedule(schedule_to_log_data(schedule_dyn),
              f"Dynamic Allocation (PAS), finish @ {finish_dyn} ms",
              ax_dyn, consistent_color_mapping, total_cores=6)
fig_dyn.subplots_adjust(left=0.08, right=0.78, top=0.90, bottom=0.12)
plt.show()

# Plot static schedule (disabled; we will show only sweep plots)
fig_static, ax_static = plt.subplots(
    1, 1, figsize=(19.20, 10.80), sharex=True)
plot_schedule(schedule_to_log_data(schedule_static),
              f"Static Allocation (PAS), finish @ {finish_static} ms",
              ax_static, consistent_color_mapping, total_cores=6)
fig_static.subplots_adjust(left=0.08, right=0.78, top=0.90, bottom=0.12)
plt.show()

# Count total runnables executed


def count_executed_runnables(schedule):
    return len(schedule)  # Each entry in schedule is one execution

    # After your scheduling calls
total_dyn = count_executed_runnables(schedule_dyn)
total_static = count_executed_runnables(schedule_static)

print(f"Total runnable executions (Dynamic): {total_dyn}")
print(f"Total runnable executions (Static): {total_static}")


def print_core_utilization(schedule: List[ScheduleEntry], finish_time: int, total_cores: int):
    exec_time = {c: 0 for c in range(total_cores)}
    for e in schedule:
        exec_time[e.core] += (e.finish_time - e.start_time)

    for c in range(total_cores):
        util = (exec_time[c] / finish_time * 100) if finish_time > 0 else 0.0
        print(
            f"Core {c}: total execution time = {exec_time[c]} ms, utilization = {util:.2f}%")

    avg_exec = sum(exec_time.values()) / total_cores
    avg_util = (avg_exec / finish_time * 100) if finish_time > 0 else 0.0
    print(f"Average execution time per core = {avg_exec:.2f} ms")
    print(f"Average utilization = {avg_util:.2f}%")

    print("\nDynamic run core utilization:")
    print_core_utilization(schedule_dyn, finish_dyn, total_cores=6)
    print("\nStatic run core utilization:")
    print_core_utilization(schedule_static, finish_static, total_cores=6)


def total_wait_time(schedule: List[ScheduleEntry]) -> int:
    # Sum waiting over all executions (repetitions included)
    return sum(max(0, e.start_time - e.eligible_time) for e in schedule)


def average_wait_per_execution(schedule: List[ScheduleEntry], extra_wait: int = 0) -> float:
    total_execs = len(schedule)
    total_wait = total_wait_time(schedule) + extra_wait
    return (total_wait / total_execs) if total_execs > 0 else 0.0

    # After computing schedules and getting wait_extra_dyn/static
avg_wait_dyn = average_wait_per_execution(schedule_dyn, wait_extra_dyn)
avg_wait_static = average_wait_per_execution(
    schedule_static, wait_extra_static)

print(
    f"Average waiting time per execution (Dynamic): {avg_wait_dyn:.2f} ms")
print(
    f"Average waiting time per execution (Static): {avg_wait_static:.2f} ms")

print(
    f"Total waiting time (Dynamic): {total_wait_time(schedule_dyn) + wait_extra_dyn} ms")
print(
    f"Total waiting time (Static): {total_wait_time(schedule_static) + wait_extra_static} ms")


def average_execution_time(schedule: List[ScheduleEntry]) -> float:
    if not schedule:
        return 0.0
    total_exec_time = sum(e.finish_time - e.start_time for e in schedule)
    return total_exec_time / len(schedule)


    # After computing schedules
avg_exec_dyn = average_execution_time(schedule_dyn)
avg_exec_static = average_execution_time(schedule_static)

print(
    f"Average execution time per runnable (Dynamic): {avg_exec_dyn:.2f} ms")
print(
    f"Average execution time per runnable (Static): {avg_exec_static:.2f} ms")


# Ensure output directory exists (match existing pattern ../../Images/backend/)
output_dir = os.path.normpath(os.path.join(
    os.path.dirname(__file__), '../../Images/backend'))
os.makedirs(output_dir, exist_ok=True)
