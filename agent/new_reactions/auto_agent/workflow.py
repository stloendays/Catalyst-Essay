"""Append-only progressive DAG revisions over the existing build stages."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

MANDATORY = {'evidence', 'basis', 'flowsheet', 'model_check', 'interface_check', 'independent_validation', 'report'}
STATUSES = {'planned', 'ready', 'running', 'validated', 'blocked', 'failed', 'skipped'}


def latest(ws):
    paths = list((Path(ws)/'workflow').glob('rev_*.json'))
    if not paths:
        return None
    path = max(paths, key=lambda p: int(p.stem.split('_')[1]))
    return json.loads(path.read_text(encoding='utf-8'))


def validate(nodes, stages):
    from registry import MODULES
    if not isinstance(nodes, list) or not nodes:
        raise ValueError('nodes must be a nonempty list')
    by_id = {}
    for n in nodes:
        for field in ('node_id', 'node_type', 'stage', 'depends_on', 'inputs', 'outputs', 'validation_policy', 'status', 'skip_reason'):
            if field not in n:
                raise ValueError('node missing '+field)
        if not isinstance(n['node_id'], str) or not n['node_id'] or n['node_id'] in by_id:
            raise ValueError('unique nonempty node_id required')
        by_id[n['node_id']] = n
        if n['stage'] not in stages or n['status'] not in STATUSES or not n['validation_policy']:
            raise ValueError('invalid stage/status/validation_policy')
        if not isinstance(n['depends_on'], list) or not isinstance(n['inputs'], dict) or not isinstance(n['outputs'], dict):
            raise ValueError('depends_on list and inputs/outputs mappings required')
        if n.get('module_id'):
            if n['module_id'] not in MODULES or n.get('module_version') != MODULES[n['module_id']]['version']:
                raise ValueError('unknown module/version')
        elif n.get('experimental'):
            from registry import experimental_path
            experimental_path(Path('.'), n['experimental'])
        elif n['node_type'] not in MANDATORY:
            raise ValueError('optional computational node needs module_id/version or experimental name')
        if n['status'] == 'skipped':
            if n['node_type'] in MANDATORY:
                raise ValueError('mandatory node cannot be skipped')
            if len(n['skip_reason'].strip()) < 30:
                raise ValueError('skip_reason must have >=30 characters')
    for kind in MANDATORY:
        if sum(n['node_type'] == kind for n in nodes) != 1:
            raise ValueError('exactly one mandatory node required: '+kind)
    visiting, done = set(), set()
    def visit(key):
        if key not in by_id:
            raise ValueError('dependency missing: '+key)
        if key in visiting:
            raise ValueError('workflow must be a DAG')
        if key in done:
            return
        visiting.add(key)
        n = by_id[key]
        for dep in n['depends_on']:
            visit(dep)
            if n['status'] in ('ready', 'running', 'validated') and by_id[dep]['status'] != 'validated':
                raise ValueError('dependency must be validated: '+dep)
        visiting.remove(key)
        done.add(key)
    for key in by_id:
        visit(key)


def _write(ws, nodes, reason, changes, stages):
    validate(nodes, stages)
    ws = Path(ws)
    root = ws/'workflow'
    root.mkdir(exist_ok=True)
    old = latest(ws)
    number = old['revision']+1 if old else 1
    doc = dict(revision=number, parent_revision=old['revision'] if old else None, reason=reason, nodes=nodes)
    data = json.dumps(doc, ensure_ascii=False, indent=1)+'\n'
    path = root/f'rev_{number}.json'
    with path.open('x', encoding='utf-8') as f:
        f.write(data)
    with (ws/'workflow_events.jsonl').open('a', encoding='utf-8') as f:
        for change in changes:
            f.write(json.dumps(dict(revision=number, reason=reason, change=change,
                                    revision_sha256=hashlib.sha256(data.encode()).hexdigest()), ensure_ascii=False)+'\n')
    return dict(revision=number, nodes=len(nodes), statuses={k:sum(n['status']==k for n in nodes) for k in STATUSES if any(n['status']==k for n in nodes)}, artifact=f'workflow/rev_{number}.json')


def plan(ws, nodes, stages):
    if latest(ws):
        raise ValueError('workflow already exists; use revise_workflow')
    return _write(ws, nodes, 'initial plan', [dict(op='add', node=n) for n in nodes], stages)


def revise(ws, changes, reason, stages):
    if not isinstance(reason, str) or not reason.strip() or not changes:
        raise ValueError('nonempty changes and reason required')
    old = latest(ws)
    if not old:
        raise ValueError('plan_workflow first')
    nodes = {n['node_id']: copy.deepcopy(n) for n in old['nodes']}
    for change in changes:
        op, key = change['op'], change['node_id']
        if op == 'add':
            if key in nodes or change['node']['node_id'] != key:
                raise ValueError('add needs a new matching node_id')
            nodes[key] = change['node']
        elif op == 'update':
            patch = change['fields']
            if 'node_id' in patch or 'node_type' in patch:
                raise ValueError('node identity/type immutable; add a replacement and skip optional old node')
            nodes[key].update(patch)
        elif op == 'remove':
            if nodes[key]['node_type'] in MANDATORY:
                raise ValueError('mandatory node cannot be removed')
            # Preserve the node and its reason in the current revision as well as history.
            nodes[key].update(status='skipped', skip_reason=change.get('skip_reason', ''))
        else:
            raise ValueError('unknown revision operation')
    return _write(ws, list(nodes.values()), reason, changes, stages)


def finish_errors(ws, stages):
    try:
        doc = latest(ws)
        if not doc:
            return ['plan_workflow required']
        validate(doc['nodes'], stages)
        return ['mandatory workflow node not validated: '+n['node_type'] for n in doc['nodes']
                if n['node_type'] in MANDATORY and n['status'] != 'validated']
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return ['invalid workflow: '+str(exc)]
