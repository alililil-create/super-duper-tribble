import importlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'examples'))
from advanced_graphs import build_service, config
from langgraph.types import Command
from test_advanced import Fake

class ReferenceTests(unittest.TestCase):
    def test_five_structures(self):
        m=importlib.import_module('18_compile_validation')
        for case,expected in [('normal','B'),('isolated','A'),('disconnected','B')]:
            self.assertEqual(m.build_case(case).invoke({})['message'],expected)
        self.assertEqual(sorted(m.build_case('branch').invoke({})['outputs']),['B','C'])
        self.assertEqual(m.build_case('loop').invoke({'count':0})['count'],2)

    def test_question_routes(self):
        m=importlib.import_module('19_question_workflow')
        for label in ['简单','复杂']:
            result=m.build_graph(Fake([label,'回答'])).invoke({'question':'问题'})
            self.assertEqual(result['complexity'],label)
            self.assertEqual(result['answer'],'回答')

    def test_customer_approve_retry_reject(self):
        model=Fake(['complaint','第一次回复','主管通知','不合格','第二次回复'])
        graph=build_service(model,human_review=True); cfg=config('review-test')
        result=graph.invoke({'user_input':'投诉','attempts':0,'path':[],'complaint_log':[],'ticket_id':'LOCAL-test'},cfg)
        self.assertIn('__interrupt__',result)
        self.assertFalse(result['complaint_log'])
        result=graph.invoke(Command(resume='yes'),cfg)
        self.assertIn('__interrupt__',result)
        self.assertEqual(result['attempts'],2)
        result=graph.invoke(Command(resume='no'),cfg)
        self.assertFalse(result['approved'])
        self.assertEqual(result['status'],'待人工处理（本地记录）')
        self.assertEqual(result['path'].count('local_ticket'),1)
        self.assertEqual(model.calls,5)

if __name__=='__main__': unittest.main()
