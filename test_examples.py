"""验证计算边界、LCEL 和工具调用回传；不调用远程 API。"""
import contextlib
import importlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent / 'examples'))
sys.argv.append('--offline')
import toolkit
from langchain_core.messages import AIMessage, ToolMessage

class ExampleTests(unittest.TestCase):
    def test_arithmetic(self):
        for expression, expected in [('125 + 378', 503), ('(15 + 27) * 3 - 18 / 2', 117.0), ('-3 * (2 + 4)', -18)]:
            self.assertEqual(toolkit.safe_calculate(expression), expected)

    def test_reject_code(self):
        for expression in ['__import__("os")', '2 ** 100', 'True + 1', '(1).__class__', '[1, 2][0]']:
            with self.assertRaises(ValueError):
                toolkit.safe_calculate(expression)
        self.assertIn('计算失败', toolkit.calculator.invoke({'expression':'1 / 0'}))

    def test_memory(self):
        from class3_memory import main
        with contextlib.redirect_stdout(io.StringIO()):
            messages = main()
        self.assertEqual(len(messages), 11)
        self.assertIn('宫保鸡丁', messages[-3].content)
        self.assertIn('米饭', messages[-3].content)

    def test_chain_count(self):
        module = importlib.import_module('07_langchain_long_chain')
        result = module.count_words(module.add_separator('你好 Python！'))
        self.assertIn('正文字符数：9', result)

    def test_tool_result_returned_to_model(self):
        class FakeModel:
            count = 0
            def bind_tools(self, tools):
                return self
            def invoke(self, messages):
                self.count += 1
                if self.count == 1:
                    return AIMessage(content='', tool_calls=[{'name':'calculator','args':{'expression':'125+378'},'id':'test-call','type':'tool_call'}])
                assert isinstance(messages[-1], ToolMessage)
                assert messages[-1].tool_call_id == 'test-call'
                assert '503' in messages[-1].content
                return AIMessage(content='结果是503')
        fake = FakeModel()
        with patch.object(toolkit, 'OFFLINE', False), patch.object(toolkit, 'model', return_value=fake), contextlib.redirect_stdout(io.StringIO()):
            toolkit.run_agent('计算125+378', [toolkit.calculator])
        self.assertEqual(fake.count, 2)

if __name__ == '__main__':
    sys.argv.remove('--offline')
    unittest.main()

