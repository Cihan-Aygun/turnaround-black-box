"""Deterministic resource-constrained turnaround model; minutes after 09:00."""
from dataclasses import dataclass, replace, asdict
import random

@dataclass(frozen=True)
class Task:
    id: str
    flight: str
    label: str
    duration: int
    release: int
    resource: str
    deps: tuple = ()

FLIGHTS = {'TB101': {'arrival': 0, 'target': 55, 'route': 'ADB → SAW'},
           'TB203': {'arrival': 12, 'target': 67, 'route': 'AYT → SAW'},
           'TB305': {'arrival': 24, 'target': 79, 'route': 'ESB → SAW'}}

def tasks():
    result = []
    for flight, data in FLIGHTS.items():
        a = data['arrival']
        spec = [('unload','Unload bags',12,'baggage',()),
                ('clean','Cabin cleaning',16,'cleaning',()),
                ('fuel','Fuel service',18,flight+'-fuel',()),
                ('cater','Catering',12,flight+'-cater',()),
                ('load','Load bags',16,'baggage',('unload',)),
                ('board','Boarding',20,flight+'-boarding',('clean','cater','fuel'))]
        for name,label,duration,resource,deps in spec:
            result.append(Task(f'{flight}-{name}',flight,label,duration,a,resource,
                               tuple(f'{flight}-{d}' for d in deps)))
    return result

def simulate(items, priority=None):
    """Nonpreemptive serial schedule generation with a fixed flight priority.

    At each step choose the eligible task with earliest feasible start, then
    flight rank and stable task ID. Shared resources have capacity one.
    Resource ordering is a heuristic, not an optimal scheduling claim.
    """
    ids = {t.id for t in items}
    if len(ids) != len(items) or any(d not in ids for t in items for d in t.deps):
        raise ValueError('Duplicate task or missing dependency')
    if any(t.duration <= 0 or t.release < 0 for t in items):
        raise ValueError('Invalid duration or release')
    rank = {f:i for i,f in enumerate(priority or FLIGHTS)}
    pending = {t.id:t for t in items}
    done, resources = {}, {}
    while pending:
        candidates = []
        for t in pending.values():
            if all(d in done for d in t.deps):
                constraints = [(t.release,None,'arrival')]
                constraints += [(done[d]['end'],d,'dependency') for d in t.deps]
                if t.resource in resources:
                    previous = resources[t.resource]
                    constraints.append((done[previous]['end'],previous,'resource'))
                start = max(c[0] for c in constraints)
                blockers = [dict(task=p,kind=k) for v,p,k in constraints if v == start and p]
                candidates.append((start,rank.get(t.flight,len(rank)),t.id,t,blockers))
        if not candidates:
            raise ValueError('Cyclic task dependencies')
        start,_,_,t,blockers = min(candidates,key=lambda x:x[:3])
        done[t.id] = dict(asdict(t), start=start,end=start+t.duration,blockers=blockers)
        resources[t.resource] = t.id
        del pending[t.id]
    ready = {f:max(r['end'] for r in done.values() if r['flight']==f) for f in FLIGHTS}
    delay = {f:max(0,ready[f]-FLIGHTS[f]['target']) for f in FLIGHTS}
    critical = set()
    def trace(key):
        if key in critical: return
        critical.add(key)
        for b in done[key]['blockers']: trace(b['task'])
    for f in FLIGHTS:
        for r in done.values():
            if r['flight']==f and r['end']==ready[f]: trace(r['id'])
    return dict(rows=list(done.values()),ready=ready,delay=delay,total_delay=sum(delay.values()),critical=sorted(critical))

def scenario(task_id='TB101-clean', extra=15, saving=8, priority='TB101'):
    if task_id not in {t.id for t in tasks()}: raise ValueError('Unknown task')
    if type(extra) is not int or not 0 <= extra <= 60: raise ValueError('Extra duration must be 0–60')
    if type(saving) is not int or not 0 <= saving <= 20: raise ValueError('Saving must be 0–20')
    if priority not in FLIGHTS: raise ValueError('Unknown priority flight')
    items = [replace(t,duration=t.duration+extra) if t.id==task_id else t for t in tasks()]
    baseline = simulate(items)
    interventions=[]
    for t in items:
        amount=min(saving,t.duration-1)
        changed=[replace(x,duration=x.duration-amount) if x.id==t.id else x for x in items]
        outcome=simulate(changed)
        interventions.append(dict(task=t.id,label=t.label,flight=t.flight,reduction=amount,
                                  saved=baseline['total_delay']-outcome['total_delay'],
                                  ready_gain={f:baseline['ready'][f]-outcome['ready'][f] for f in FLIGHTS}))
    interventions.sort(key=lambda x:(-x['saved'],x['task']))
    best=interventions[0]
    improved=simulate([replace(t,duration=t.duration-best['reduction']) if t.id==best['task'] else t for t in items]) if best['saved'] > 0 else baseline
    prioritized=simulate(items,[priority]+[f for f in FLIGHTS if f!=priority])
    counterfactual=simulate(tasks())
    return dict(flights=FLIGHTS,baseline=baseline,improved=improved,prioritized=prioritized,
                interventions=interventions,selected=best,
                disruption_effect=baseline['total_delay']-counterfactual['total_delay'],
                assumptions=['Synthetic example; minutes after 09:00.',
                 'One baggage team and one cleaning team; other services are flight-specific.',
                 'Boarding follows cleaning, catering and fuel in this illustrative policy.',
                 'All six tasks must finish before readiness. No ATC, taxi or runway model.',
                 'Fixed-priority scheduling heuristic; no global optimality guarantee.'])

def uncertainty(seed=42, runs=200):
    rng=random.Random(seed)
    results={f:[] for f in FLIGHTS}
    for _ in range(runs):
        sampled=[replace(t,duration=max(1,round(t.duration*rng.triangular(.8,1.4,1)))) for t in tasks()]
        outcome=simulate(sampled)
        for f in FLIGHTS: results[f].append(outcome['ready'][f])
    return {f:dict(p50=sorted(v)[int(.5*(runs-1))],p90=sorted(v)[int(.9*(runs-1))],
                   on_time=sum(x<=FLIGHTS[f]['target'] for x in v)/runs) for f,v in results.items()}
