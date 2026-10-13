import asyncio
import contextlib
import importlib
import io
from pathlib import Path
import sys
import unittest
from langchain_core.messages import AIMessage
sys.path.insert(0, str(Path(__file__).parent / 'examples'))

class FakeModel:
    """仅供单元测试；实际示例不使用替身。"""
    def __init__(self):
        self.calls = []
    def invoke(self, prompt):
        self.calls.append(prompt)
        return AIMessage(content='草稿' if '请用中文简要回答' in prompt else '润色答案')

class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.module = importlib.import_module('09_checkpointer_demo')
        self.config = {'configurable': {'thread_id': 'test'}}

    def test_history_and_thread_isolation(self):
        model = FakeModel()
        graph = self.module.build_graph(model)
        with contextlib.redirect_stdout(io.StringIO()):
            result = graph.invoke({'question': '什么是微积分？'}, self.config)
        self.assertEqual(result['answer'], '润色答案')
        history = list(graph.get_state_history(self.config))
        self.assertEqual(history[0].values, result)
        self.assertTrue(any(s.values == {'question': '什么是微积分？'} for s in history))
        self.assertTrue(any(s.values.get('draft') == '草稿' and 'answer' not in s.values for s in history))
        self.assertEqual(graph.get_state({'configurable': {'thread_id': 'other'}}).values, {})
        self.assertEqual(len(model.calls), 2)
        self.assertIn('草稿', model.calls[1])

    def test_pause_resume_does_not_repeat_draft(self):
        model = FakeModel()
        graph = self.module.build_graph(model, pause=True)
        with contextlib.redirect_stdout(io.StringIO()):
            first = graph.invoke({'question': '问题'}, self.config)
            self.assertNotIn('answer', first)
            self.assertEqual(graph.get_state(self.config).next, ('polish_node',))
            self.assertEqual(len(model.calls), 1)
            final = graph.invoke(None, self.config)
        self.assertEqual(final['answer'], '润色答案')
        self.assertEqual(len(model.calls), 2)
        self.assertEqual(graph.get_state(self.config).next, ())

    def test_new_saver_is_empty(self):
        graph = self.module.build_graph(FakeModel())
        self.assertEqual(list(graph.get_state_history(self.config)), [])

    def test_compile_execution_modes(self):
        module = importlib.import_module('08_compile_graph')
        graph = module.build_graph()
        initial = {'message': '你好', 'output': ''}
        async def execute():
            final = await graph.ainvoke(initial)
            events = [item async for item in graph.astream(initial, stream_mode='updates')]
            return final, events
        with contextlib.redirect_stdout(io.StringIO()):
            sync_result = graph.invoke(initial)
            async_result, events = asyncio.run(execute())
        self.assertEqual(sync_result, async_result)
        self.assertEqual(sync_result['message'], initial['message'])
        self.assertEqual([next(iter(e)) for e in events], ['add_info', 'print_info'])
        self.assertEqual(initial['output'], '')

if __name__ == '__main__':
    unittest.main()
