import sys
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from datetime import date
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).parent/'examples'))
from smart_query_core import *
from stream_subgraph_core import build_story,build_custom,build_article,build_customer_subgraph
from test_advanced import Fake

class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir='D:/Codex/temp')
        self.path=init_database(self.temp.name,date(2026,10,13))
    def tearDown(self): self.temp.cleanup()
    def test_seed_and_join(self):
        self.assertEqual(read_query(self.path,"SELECT SUM(amount) FROM orders WHERE region='华北' AND order_date>='2026-09-01' AND order_date<'2026-10-01'")[1],[(6898.0,)])
        self.assertEqual(read_query(self.path,"SELECT SUM(o.amount) FROM orders o JOIN users u ON o.user_id=u.user_id WHERE u.city='北京'")[1],[(7297.0,)])
        init_database(self.temp.name,date(2026,10,13))
        self.assertEqual(read_query(self.path,'SELECT COUNT(*) FROM orders')[1],[(10,)])
        self.assertEqual(month_bounds(date(2026,1,5)),(date(2025,12,1),date(2026,1,1)))
    def test_sql_guard(self):
        for sql in ['DELETE FROM orders','SELECT 1; DROP TABLE users','SELECT * FROM sqlite_master',"SELECT load_extension('x')",'SELECT missing FROM orders']:
            with self.assertRaises((ValueError,sqlite3.Error)): read_query(self.path,sql,validate=True)
    def test_repair_flow_and_limit(self):
        keywords=json.dumps(dict(tables=['orders'],columns=['amount'],conditions=[],metrics=['sum']))
        g=build_query(self.path,Fake([keywords,'SELECT missing FROM orders','SELECT SUM(amount) FROM orders']),date(2026,10,13))
        result=g.invoke({'question':'总金额'})
        self.assertFalse(result['error']); self.assertEqual(result['retries'],1)
        g=build_query(self.path,Fake([keywords]+['SELECT bad FROM orders']*4))
        result=g.invoke({'question':'总金额'})
        self.assertEqual(result['retries'],3); self.assertIn('查询失败',result['answer'])
    def test_stream_modes(self):
        updates=list(build_story(Fake(['大纲','故事','点评'])).stream({'topic':'猪','outline':'','story':'','comment':''},stream_mode='updates'))
        self.assertEqual([next(iter(x)) for x in updates],['outline','write','comment'])
        values=list(build_story(Fake(['大纲','故事','点评'])).stream({'topic':'猪','outline':'','story':'','comment':''},stream_mode='values'))
        self.assertEqual(len(values),4); self.assertEqual(values[-1]['story'],'故事')
        self.assertEqual(values[1]['story'],'')
    def test_custom_stream_events(self):
        class Streaming:
            def stream(self,prompt):
                for text in ['你','好']: yield SimpleNamespace(content=text)
        events=list(build_custom(Streaming()).stream({'question':'q'},stream_mode='custom'))
        self.assertEqual([x['type'] for x in events],['status','token','token','done'])
        self.assertEqual(events[-1]['text'],'你好')
    def test_nested_graph(self):
        r=build_article(Fake(['标题','正文'])).invoke({'topic':'主题'})
        self.assertEqual(r,{'topic':'主题','title':'标题','article':'正文'})
        for responses,intent in [(['投诉','质量','抱歉'],'投诉'),(['咨询','政策待核实'],'咨询'),(['其他','你好'],'其他')]:
            r=build_customer_subgraph(Fake(responses)).invoke({'user_message':'q'})
            self.assertEqual(r['intent'],intent)
            self.assertEqual('complaint_type' in r,intent=='投诉')

if __name__=='__main__': unittest.main()
