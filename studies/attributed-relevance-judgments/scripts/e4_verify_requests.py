"""Assert that a repeat run's frozen requests are identical to the reference arm. Exit non-zero on any drift."""
import json
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
REFERENCE = {'joint': 'clinical-v1', 'decide': 'clinical-decide-only-v1'}


def verify(run_dir, arm):
    ref = json.loads((STUDY / 'runs' / REFERENCE[arm] / 'stage-a-requests.json').read_text())
    new = json.loads((Path(run_dir) / 'stage-a-requests.json').read_text())
    if len(ref) != len(new):
        raise ValueError('Request count differs: %d vs %d' % (len(ref), len(new)))
    for i, (a, b) in enumerate(zip(ref, new)):
        if a['id'] != b['id'] or a['topic'] != b['topic'] or a['model'] != b['model'] or a['req'] != b['req']:
            raise ValueError('Request %d differs from reference %s' % (i, REFERENCE[arm]))
    return len(new)


if __name__ == '__main__':
    name, arm = sys.argv[1], sys.argv[2]
    n = verify(STUDY / 'runs' / name, arm)
    print(json.dumps({'run': name, 'arm': arm, 'identical_requests': n, 'reference': REFERENCE[arm]}))
