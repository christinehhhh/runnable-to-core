from shared_log import SharedExecutionLog
import heapq
from collections import defaultdict
import io
import base64
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


app = Flask(__name__)
CORS(app)


def run_scheduling(runnables, num_cores, simulation_time_ms=400):
    """Run the scheduling algorithm with given runnables and number of cores."""

    event_queue = []
    heapq.heapify(event_queue)

    last_output = defaultdict(lambda: (-1, -1))
    execution_log = SharedExecutionLog()
    task_instance_counter = defaultdict(int)
    dependency_instance = defaultdict(lambda: defaultdict(int))
    completed_instances = defaultdict(int)
    event_task_instance_counter = defaultdict(int)

    CPU_FREE_TIME = 0

    def schedule_periodic_runnables():
        """Schedule all periodic runnables up to the simulation time limit."""
        for name, props in runnables.items():
            if props['type'] == 'periodic':
                time = 0
                counter = 0
                while time <= simulation_time_ms:
                    heapq.heappush(
                        event_queue, (time, name, props['execution_time'], counter))
                    time += props['period']
                    counter += 1

    def is_dependencies_ready(runnable, current_instance):
        """Check if all dependencies of a runnable have completed by the current time."""
        deps = runnables[runnable].get('deps', [])
        return all(completed_instances[dep] > current_instance for dep in deps)

    def schedule_event_runnables(triggered, current_time):
        """Schedule all event-based tasks that are triggered by the given events."""
        for name, props in runnables.items():
            if props['type'] != 'event':
                continue

            if not set(props.get('deps', [])) & set(triggered):
                continue

            available_instances = [completed_instances[dep]
                                   for dep in props['deps']]
            min_completed = min(available_instances)
            current_count = event_task_instance_counter[name]

            if min_completed > current_count:
                current_instance = current_count
                total_delay = sum(exec_time for sched_time, _, exec_time,
                                  _ in event_queue if sched_time < current_time)
                heapq.heappush(event_queue, (current_time + total_delay,
                               name, props['execution_time'], current_instance))
                event_task_instance_counter[name] += 1

                for dep in props['deps']:
                    dependency_instance[name][dep] = completed_instances[dep] - 1

    # Run the scheduling
    schedule_periodic_runnables()

    while event_queue and CPU_FREE_TIME < simulation_time_ms:
        scheduled_time, task, execution_time, instance = heapq.heappop(
            event_queue)

        actual_start_time = max(CPU_FREE_TIME, scheduled_time)
        finish_time = actual_start_time + execution_time
        CPU_FREE_TIME = finish_time

        last_output[task] = (finish_time, instance)
        completed_instances[task] = instance + 1
        execution_log.append(
            (actual_start_time, finish_time, task, instance, runnables[task]['affinity']))

        schedule_event_runnables([task], finish_time)

    return execution_log, CPU_FREE_TIME


def create_gantt_chart(execution_log, title="Gantt Chart of Runnable Execution Schedule"):
    """Create a Gantt chart from the execution log and return as base64 string."""
    filtered_log = [(start, end, task, instance)
                    for start, end, task, instance, _ in execution_log.get_log()]

    if not filtered_log:
        return None

    task_colors = {}
    color_palette = plt.cm.get_cmap("tab20", len(
        set(task for _, _, task, _ in filtered_log)))
    for i, task in enumerate(sorted(set(task for _, _, task, _ in filtered_log))):
        task_colors[task] = color_palette(i)

    fig, ax = plt.subplots(figsize=(12, 6))

    for i, (start, end, task, instance) in enumerate(filtered_log):
        ax.barh(task, end - start, left=start, color=task_colors[task])

    ax.set_xlabel("Time (ms)")
    ax.set_title(title)
    ax.grid(True)

    handles = [plt.Rectangle((0, 0), 1, 1, color=color, label=task)
               for task, color in task_colors.items()]
    ax.legend(handles=handles, bbox_to_anchor=(
        1.05, 1), loc='upper left', title="Tasks")

    plt.tight_layout()

    # Convert plot to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=300)
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return plot_url


@app.route('/api/schedule', methods=['POST'])
def schedule():
    """API endpoint to run scheduling with given runnables and number of cores."""
    try:
        data = request.get_json()
        runnables = data.get('runnables', {})
        num_cores = data.get('numCores', 1)
        simulation_time = data.get('simulationTime', 400)

        if not runnables:
            return jsonify({'error': 'No runnables provided'}), 400

        # Run the scheduling algorithm
        execution_log, total_execution_time = run_scheduling(
            runnables, num_cores, simulation_time)

        # Create visualization
        plot_data = create_gantt_chart(execution_log)

        # Prepare execution log data
        log_entries = []
        for start, end, task, instance, affinity in execution_log.get_log():
            log_entries.append({
                'start': start,
                'end': end,
                'task': task,
                'instance': instance,
                'affinity': affinity
            })

        return jsonify({
            'success': True,
            'totalExecutionTime': total_execution_time,
            'executionLog': log_entries,
            'ganttChart': plot_data
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
