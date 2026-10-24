import unittest
from turnaround.engine import Task,tasks,simulate,scenario,uncertainty,FLIGHTS
class EngineTests(unittest.TestCase):
    def test_physical_constraints(self):
        for task in tasks():
            for extra in (0,15,60):
                s=scenario(task.id,extra)
                for name in ('baseline','improved','prioritized'):
                    rows=s[name]['rows']; byid={r['id']:r for r in rows}
                    self.assertEqual(len(rows),18)
                    for r in rows:
                        self.assertGreaterEqual(r['start'],r['release'])
                        self.assertEqual(r['end']-r['start'],r['duration'])
                        for d in r['deps']:self.assertGreaterEqual(r['start'],byid[d]['end'])
                    for resource in {r['resource'] for r in rows}:
                        chain=sorted([r for r in rows if r['resource']==resource],key=lambda r:r['start'])
                        for a,b in zip(chain,chain[1:]):self.assertLessEqual(a['end'],b['start'])
                    self.assertEqual(s[name]['total_delay'],sum(max(0,s[name]['ready'][f]-v['target']) for f,v in FLIGHTS.items()))
    def test_hand_calculated_resource_wait(self):
        s=simulate([Task('a','TB101','A',10,0,'crew'),Task('b','TB101','B',5,0,'crew'),Task('c','TB203','C',7,0,'other'),Task('d','TB305','D',4,0,'other')])
        rows={r['id']:r for r in s['rows']};self.assertEqual((rows['b']['start'],rows['b']['end']),(10,15))
        self.assertEqual(rows['b']['blockers'],[{'task':'a','kind':'resource'}])
    def test_intervention_recomputed(self):
        s=scenario();self.assertEqual(s['selected']['saved'],s['baseline']['total_delay']-s['improved']['total_delay'])
        self.assertEqual(s['selected']['saved'],max(x['saved'] for x in s['interventions']))
    def test_zero_budget(self):
        s=scenario(saving=0);self.assertEqual(s['baseline'],s['improved'])
    def test_invalid_and_cycle(self):
        for kw in ({'extra':-1},{'saving':21},{'task_id':'bad'},{'priority':'bad'}):
            with self.assertRaises(ValueError):scenario(**kw)
        with self.assertRaises(ValueError):simulate([Task('a','TB101','A',1,0,'x',('a',))])
    def test_seeded_uncertainty(self):
        self.assertEqual(uncertainty(),uncertainty())
        for v in uncertainty().values():self.assertLessEqual(v['p50'],v['p90']);self.assertTrue(0<=v['on_time']<=1)
if __name__=='__main__':unittest.main()
