from __future__ import annotations

import random
from typing import Dict, List


BASE_RUNNABLES_BALANCED: Dict[str, Dict] = {
    'Runnable1':  {'priority': 1, 'execution_time': 15, 'type': 'periodic', 'period': 100, 'deps': []},
    'Runnable2':  {'priority': 2, 'execution_time': 20, 'type': 'periodic', 'period': 180, 'deps': []},

    'Runnable3':  {'priority': 1, 'execution_time': 25, 'type': 'event', 'period': 0, 'deps': ['Runnable1']},
    'Runnable4':  {'priority': 4, 'execution_time': 30, 'type': 'event', 'period': 0, 'deps': ['Runnable1']},
    'Runnable5':  {'priority': 3, 'execution_time': 20, 'type': 'event', 'period': 0, 'deps': ['Runnable2']},
    'Runnable6':  {'priority': 1, 'execution_time': 35, 'type': 'event', 'period': 0, 'deps': ['Runnable2']},

    'Runnable7':  {'priority': 2, 'execution_time': 40, 'type': 'event', 'period': 0, 'deps': ['Runnable3', 'Runnable4']},
    'Runnable8':  {'priority': 1, 'execution_time': 25, 'type': 'event', 'period': 0, 'deps': ['Runnable5', 'Runnable6']},
    'Runnable9':  {'priority': 0, 'execution_time': 30, 'type': 'event', 'period': 0, 'deps': ['Runnable3']},
    'Runnable10': {'priority': 4, 'execution_time': 20, 'type': 'event', 'period': 0, 'deps': ['Runnable4']},

    'Runnable11': {'priority': 2, 'execution_time': 45, 'type': 'event', 'period': 0, 'deps': ['Runnable7']},
    'Runnable12': {'priority': 0, 'execution_time': 30, 'type': 'event', 'period': 0, 'deps': ['Runnable8']},
    'Runnable13': {'priority': 3, 'execution_time': 35, 'type': 'event', 'period': 0, 'deps': ['Runnable9', 'Runnable10']},

    'Runnable14': {'priority': 1, 'execution_time': 25, 'type': 'event', 'period': 0, 'deps': ['Runnable11']},
    'Runnable15': {'priority': 3, 'execution_time': 40, 'type': 'event', 'period': 0, 'deps': ['Runnable12']},
    'Runnable16': {'priority': 3, 'execution_time': 20, 'type': 'event', 'period': 0, 'deps': ['Runnable13']},

    'Runnable17': {'priority': 4, 'execution_time': 50, 'type': 'event', 'period': 0, 'deps': ['Runnable14', 'Runnable15']},
    'Runnable18': {'priority': 1, 'execution_time': 25, 'type': 'event', 'period': 0, 'deps': ['Runnable16']},

    'Runnable19': {'priority': 4, 'execution_time': 35, 'type': 'event', 'period': 0, 'deps': ['Runnable17', 'Runnable18']},
    'Runnable20': {'priority': 2, 'execution_time': 30, 'type': 'event', 'period': 0, 'deps': ['Runnable19']},
}


def _topological_name_order(names: List[str]) -> List[str]:
    # Ensure natural order Runnable1..Runnable20 if available
    def key_fn(n: str) -> int:
        if n.startswith('Runnable'):
            try:
                return int(n[8:])
            except Exception:
                return 10**9
        return 10**9
    return sorted(names, key=key_fn)


def generate_dependency_sets(
    base: Dict[str, Dict],
    num_sets: int = 50,
    seed: int = 2025,
) -> List[Dict[str, Dict]]:
    rnd = random.Random(seed)
    ordered_names = _topological_name_order(list(base.keys()))

    sets: List[Dict[str, Dict]] = []
    for k in range(num_sets):
        current: Dict[str, Dict] = {}
        for name in ordered_names:
            props = base[name]
            new_entry = {
                'priority': int(props.get('priority', 0)),
                'execution_time': int(props.get('execution_time', 0)),
                'type': props.get('type'),
                # keep period if present, else 0 for events to match format
                'period': int(props.get('period', 0)),
                'deps': []
            }

            if new_entry['type'] == 'periodic':
                # periodic sources have no deps
                new_entry['deps'] = []
            else:
                # choose 0-2 deps from earlier names to guarantee DAG
                earlier = [n for n in ordered_names if _topological_name_order([n, name])[
                    0] == n and n != name]
                # filter to those already added
                earlier = [n for n in earlier if n in current]
                max_deps = 2
                dep_count = rnd.choice([0, 1, 2]) if earlier else 0
                dep_count = min(dep_count, max_deps, len(earlier))
                deps = rnd.sample(earlier, dep_count)
                new_entry['deps'] = deps

            current[name] = new_entry

        sets.append(current)
        # advance RNG state a bit for distinct structures
        _ = [rnd.random() for _ in range(5 + k % 7)]

    # ensure sets are all different; if any duplicates, perturb with new seeds
    seen = set()
    unique_sets: List[Dict[str, Dict]] = []
    for idx, s in enumerate(sets):
        key = tuple((n, tuple(s[n]['deps'])) for n in ordered_names)
        if key in seen:
            # mutate by toggling an optional dep if possible
            rnd2 = random.Random(seed + 1000 + idx)
            name = rnd2.choice(
                [n for n in ordered_names if s[n]['type'] == 'event'])
            earlier = [n for n in ordered_names if _topological_name_order([n, name])[
                0] == n and n != name]
            earlier = [n for n in earlier if n in s]
            if earlier:
                choice = rnd2.choice(earlier)
                deps = set(s[name]['deps'])
                if choice in deps:
                    deps.remove(choice)
                else:
                    if len(deps) < 2:
                        deps.add(choice)
                s[name]['deps'] = list(deps)
            key = tuple((n, tuple(s[n]['deps'])) for n in ordered_names)
        seen.add(key)
        unique_sets.append(s)

    return unique_sets


# Public: 50 sets ready to import
RUNNABLE_SETS_50: List[Dict[str, Dict]] = generate_dependency_sets(
    BASE_RUNNABLES_BALANCED, 50, seed=2025)
