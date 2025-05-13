"""Simulation of a real-time automotive system with periodic and event-driven tasks."""

import heapq
from collections import defaultdict

SIMULATION_TIME_MS = 1000

runnables = {
    'RadarCapture': {
        'criticality': 1,
        'affinity': 0,
        'period': 75,
        'execution_time': 2,
        'type': 'periodic',
    },
    'CameraCapture': {
        'criticality': 0,
        'affinity': 0,
        'period': 50,
        'execution_time': 4,
        'type': 'periodic',
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


def schedule_periodic_runnables():
    """Schedule all periodic tasks up to the simulation time limit."""
    for name, props in runnables.items():
        if props['type'] == 'periodic':
            t = 0
            while t <= SIMULATION_TIME_MS:
                heapq.heappush(event_queue, (t, name))
                t += props['period']


def is_deps_ready(runnable_name, check_time):
    """Check if all dependencies of a runnable have completed by the current time."""
    deps = runnables[runnable_name].get('deps', [])
    return all(last_output[dep] >= 0 and last_output[dep] <= check_time for dep in deps)


def schedule_event_runnables(triggered, check_time):
    """Schedule event-driven tasks that depend on the triggered tasks."""
    for name, props in runnables.items():
        if props['type'] == 'event' and set(props.get('deps', [])) & set(triggered):
            if is_deps_ready(name, check_time):
                heapq.heappush(event_queue, (check_time, name))


schedule_periodic_runnables()

while event_queue:
    current_time, runnable = heapq.heappop(event_queue)

    execution_time = runnables[runnable]['execution_time']
    finish_time = current_time + execution_time
    last_output[runnable] = finish_time

    execution_log.append((current_time, finish_time, runnable))
    schedule_event_runnables([runnable], finish_time)

print('Execution Log (start_ms → end_ms):')
for start, end, task in execution_log:
    print(f'[{start:4} → {end:4}] ms : {task}')
