"""Simulation of a real-time automotive system with periodic and event-driven tasks."""

import heapq
from collections import defaultdict

SIMULATION_TIME_MS = 400

runnables = {
    'RadarCapture': {
        'criticality': 1,
        'affinity': 0,
        'period': 75,
        'execution_time': 2,
        'type': 'periodic',
        'deps': []
    },
    'CameraCapture': {
        'criticality': 0,
        'affinity': 0,
        'period': 50,
        'execution_time': 4,
        'type': 'periodic',
        'deps': []
    },
    'SensorFusion': {
        'criticality': 1,
        'affinity': 1,
        'execution_time': 5,
        'type': 'event',
        'deps': ['RadarCapture', 'CameraCapture'],
    },
    'ObjectDetection': {
        'criticality': 1,
        'affinity': 1,
        'execution_time': 6,
        'type': 'event',
        'deps': ['SensorFusion'],
    },
    'TrajectoryPrediction': {
        'criticality': 1,
        'affinity': 1,
        'execution_time': 4,
        'type': 'event',
        'deps': ['ObjectDetection'],
    },
    'CollisionRiskAssessment': {
        'criticality': 2,
        'affinity': 1,
        'execution_time': 3,
        'type': 'event',
        'deps': ['TrajectoryPrediction'],
    },
    'EmergencyBrakeDecision': {
        'criticality': 2,
        'affinity': 1,
        'execution_time': 2,
        'type': 'event',
        'deps': ['CollisionRiskAssessment'],
    },
    'ActuatorControl': {
        'criticality': 2,
        'affinity': 0,
        'execution_time': 1,
        'type': 'event',
        'deps': ['EmergencyBrakeDecision'],
    },
    'LaneMarkingDetection': {
        'criticality': 1,
        'affinity': 1,
        'execution_time': 5,
        'type': 'event',
        'deps': ['CameraCapture'],
    },
    'VehiclePositionEstimation': {
        'criticality': 1,
        'affinity': 1,
        'execution_time': 3,
        'type': 'event',
        'deps': ['LaneMarkingDetection'],
    },
    'LaneDepartureWarning': {
        'criticality': 1,
        'affinity': 1,
        'execution_time': 2,
        'type': 'event',
        'deps': ['VehiclePositionEstimation'],
    },
    'SteeringAngleCalculation': {
        'criticality': 1,
        'affinity': 1,
        'execution_time': 2,
        'type': 'event',
        'deps': ['VehiclePositionEstimation'],
    },
    'SteeringActuatorControl': {
        'criticality': 2,
        'affinity': 0,
        'execution_time': 1,
        'type': 'event',
        'deps': ['LaneDepartureWarning', 'SteeringAngleCalculation'],
    },
}

event_queue = []
heapq.heapify(event_queue)

last_output = defaultdict(lambda: -1)
execution_log = []

cpu_free_time = 0


def schedule_periodic_runnables():
    """Schedule all periodic runnables up to the simulation time limit,
    ensuring sequential execution."""
    for name, props in runnables.items():
        if props['type'] == 'periodic':
            time = 0
            while time <= SIMULATION_TIME_MS:
                heapq.heappush(event_queue, (time, 0, name))
                time += props['period']


def is_dependencies_ready(runnable, current_time):
    """Check if all dependencies of a runnable have completed by the current time."""
    deps = runnables[runnable].get('deps', [])
    return all(last_output[dep] >= 0 and last_output[dep] <= current_time for dep in deps)


def schedule_event_runnables(triggered, current_time):
    """Schedule all event-based tasks that are triggered by the given events."""
    for name, props in runnables.items():
        if props['type'] == 'event' and set(props.get('deps', [])) & set(triggered):
            if is_dependencies_ready(name, current_time):
                heapq.heappush(event_queue, (current_time, 1, name))


schedule_periodic_runnables()

while event_queue:
    scheduled_time, priority, task = heapq.heappop(event_queue)

    actual_start_time = max(cpu_free_time, scheduled_time)
    execution_time = runnables[task]['execution_time']
    finish_time = actual_start_time + execution_time
    cpu_free_time = finish_time

    last_output[task] = finish_time
    execution_log.append((actual_start_time, finish_time, task))

    schedule_event_runnables([task], finish_time)

print('Execution Log (start → end ms):')
for start, end, task in execution_log:
    print(f'[{start:4} → {end:4}] ms : {task}')
