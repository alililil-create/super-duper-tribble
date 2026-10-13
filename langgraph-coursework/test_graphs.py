import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).parent / "examples"))

class GraphTests(unittest.TestCase):
    def test_lcel_matches_graph(self):
        m = importlib.import_module("01_graph_and_langchain")
        for text in ["  hello  ", "", "中文 abc"]:
            self.assertEqual(m.build_graph().invoke({"text": text})["text"], m.upper(m.clean(text)))

    def test_reducer_and_unchanged_field(self):
        m = importlib.import_module("02_state_design")
        initial = {"message": ["已有消息"], "user_query": "原始输入", "results": "旧结果"}
        result = m.build_graph().invoke(initial)
        self.assertEqual(result["message"], ["已有消息", "你好，我是 AI 助手", "请问有什么可以帮助你？"])
        self.assertEqual(result["user_query"], "原始输入")
        self.assertEqual(result["results"], "节点二完成")
        self.assertEqual(initial["message"], ["已有消息"])

    def test_structure(self):
        m = importlib.import_module("03_stategraph_structure")
        result = m.build_graph().invoke({"message": [], "user_query": "  hi  ", "results": ""})
        self.assertEqual(result["results"], "HI")
        self.assertEqual(result["user_query"], "  hi  ")

    def test_hello(self):
        m = importlib.import_module("04_hello_world")
        self.assertEqual(m.build_graph().invoke({"message": "old"}), {"message": "Hello LangGraph!"})

    def test_multiple_nodes_order(self):
        m = importlib.import_module("05_multiple_nodes")
        initial = {"message": [], "user_query": "问题", "results": ""}
        events = list(m.build_graph().stream(initial, stream_mode="updates"))
        self.assertEqual([next(iter(event)) for event in events], ["hello", "process", "goodbye"])
        result = m.build_graph().invoke(initial)
        self.assertEqual(result["message"], ["Hello LangGraph!", "处理节点收到：Hello LangGraph!", "Goodbye!"])
        self.assertEqual(result["results"], "Goodbye!")

    def test_string_overwrite(self):
        m = importlib.import_module("05_multiple_nodes")
        states = list(m.build_overwrite_graph().stream({"message": ""}, stream_mode="values"))
        self.assertEqual([s["message"] for s in states], ["", "Hello LangGraph!", "Goodbye!"])

    def test_safe_calculator(self):
        m = importlib.import_module("07_conditional_edges")
        self.assertEqual(m.calculate("25 × 4 + 100"), 200)
        self.assertEqual(m.calculate("(15+27)*3-18/2"), 117.0)
        for text in ['__import__("os")', '2**100', 'True + 1', '[1][0]']:
            with self.assertRaises(ValueError):
                m.calculate(text)
        with self.assertRaises(ZeroDivisionError):
            m.calculate('1/0')

    def test_conditional_paths(self):
        # 测试替身仅用于单元测试；示例入口使用真实千问。
        from langchain_core.messages import AIMessage
        m = importlib.import_module("07_conditional_edges")
        class Stub:
            def __init__(self, category):
                self.category = category
                self.calls = 0
            def invoke(self, messages):
                self.calls += 1
                if self.calls == 1:
                    return AIMessage(content='{"category":"' + self.category + '","expression":"25*4+100"}')
                return AIMessage(content='你好')
        for category in ['calculate', 'chat']:
            llm = Stub(category)
            state = {'user_query': '测试', 'category': '', 'expression': '', 'reply': '', 'visited': []}
            result = m.build_graph(llm).invoke(state)
            self.assertEqual(result['visited'], ['classify', category])
            self.assertEqual(result['reply'], '200' if category == 'calculate' else '你好')
            self.assertEqual(llm.calls, 1 if category == 'calculate' else 2)

    def test_invalid_classification(self):
        m = importlib.import_module("07_conditional_edges")
        for content in ['{"category":"unknown"}', '[]', '{"category":"calculate","expression":123}']:
            with self.assertRaises(ValueError):
                m.parse_decision(content)

if __name__ == "__main__":
    unittest.main()
