import sys
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from threading import Barrier
sys.path.insert(0,str(Path(__file__).parent/'examples'))
from advanced_graphs import *
from langgraph.types import Command
from langgraph.checkpoint.sqlite import SqliteSaver

class Fake:
    def __init__(self,answers): self.answers=iter(answers); self.calls=0
    def invoke(self,prompt):
        self.calls+=1
        return SimpleNamespace(content=next(self.answers))

class AdvancedTests(unittest.TestCase):
    def test_approval_does_not_regenerate(self):
        model=Fake(['SELECT name,age FROM users WHERE age>18'])
        graph=build_review(model); cfg=config('test')
        paused=graph.invoke({'question':'query'},cfg)
        self.assertIn('__interrupt__',paused)
        self.assertNotIn('result',paused)
        result=graph.invoke(Command(resume='yes'),cfg)
        self.assertIn('张三',result['result']); self.assertNotIn('李四',result['result'])
        self.assertEqual(model.calls,1)

    def test_rejection_and_write_denied(self):
        graph=build_review(Fake(['DROP TABLE users']))
        cfg=config('no'); graph.invoke({'question':'query'},cfg)
        self.assertIn('拒绝',graph.invoke(Command(resume='no'),cfg)['result'])
        cfg=config('yes'); graph=build_review(Fake(['DROP TABLE users']))
        graph.invoke({'question':'query'},cfg)
        with self.assertRaises(sqlite3.DatabaseError): graph.invoke(Command(resume='yes'),cfg)

    def test_customer_review(self):
        for answer in ['yes','no']:
            graph=build_review(Fake(['很抱歉，请提供订单号。']),customer=True)
            cfg=config(answer); graph.invoke({'question':'投诉'},cfg)
            result=graph.invoke(Command(resume=answer),cfg)
            self.assertEqual(result['approved'],answer=='yes')

    def test_sqlite_reopen_and_isolation(self):
        with tempfile.TemporaryDirectory(dir='D:/Codex/temp') as folder:
            db=str(Path(folder)/'test.sqlite'); cfg=config('saved')
            with SqliteSaver.from_conn_string(db) as saver:
                graph=build_review(Fake(['SELECT name FROM users']),saver=saver)
                graph.invoke({'question':'q'},cfg)
            with SqliteSaver.from_conn_string(db) as saver:
                model=Fake([]); graph=build_review(model,saver=saver)
                self.assertTrue(graph.get_state(cfg).next)
                self.assertFalse(graph.get_state(config('other')).values)
                result=graph.invoke(Command(resume='yes'),cfg)
                self.assertIn('张三',result['result']); self.assertEqual(model.calls,0)

    def test_conditional_paths_and_bad_label(self):
        for label,node in [('greeting','greet'),('question','answer'),('calculate','calculator')]:
            r=build_conditional(Fake([label,'reply'])).invoke({'user_input':'q','path':[]})
            self.assertEqual(r['path'],['classify',node])
        with self.assertRaises(ValueError):
            build_conditional(Fake(['invalid'])).invoke({'user_input':'q','path':[]})

    def test_loop_retry_and_limit(self):
        poem='春风吹柳绿\n细雨润花红\n燕子穿云去\n新芽向日生'
        r=build_loop(Fake([poem,'不合格',poem,'合格'])).invoke({'topic':'春','attempts':0})
        self.assertEqual(r['attempts'],2)
        r=build_loop(Fake([poem,'不合格']*3)).invoke({'topic':'春','attempts':0})
        self.assertEqual(r['attempts'],3); self.assertEqual(r['quality'],'不合格')

    def test_parallel_barrier_and_empty(self):
        barrier=Barrier(3)
        class Concurrent:
            def invoke(self,prompt):
                barrier.wait(timeout=5)
                return SimpleNamespace(content=prompt[-1].content)
        r=build_parallel(Concurrent()).invoke({'topics':['A','B','C'],'results':[]},{'max_concurrency':3})
        self.assertEqual(len(r['results']),3)
        self.assertEqual(r['summary'],'A：A\nB：B\nC：C')
        r=build_parallel(Fake([])).invoke({'topics':[],'results':[]})
        self.assertEqual(r['summary'],'')

    def test_service_retries_and_last_success(self):
        for final in ['合格','不合格']:
            model=Fake(['consult','r1','不合格','r2','不合格','r3',final])
            r=build_service(model).invoke({'user_input':'q','attempts':0,'path':[],'complaint_log':[]})
            self.assertEqual(r['attempts'],3)
            self.assertEqual('handoff' in r['path'],final=='不合格')

    def test_complaint_join_and_no_duplicate_side_effects(self):
        r=build_service(Fake(['complaint','r1','通知','不合格','r2','合格'])).invoke(
            {'user_input':'投诉','attempts':0,'path':[],'complaint_log':[],'ticket_id':'LOCAL-test'})
        self.assertEqual(len(r['complaint_log']),2)
        self.assertEqual(r['path'].count('assess'),2)
        self.assertEqual(r['path'].count('local_ticket'),1)
        self.assertEqual(r['status'],'完成')

if __name__=='__main__': unittest.main()
