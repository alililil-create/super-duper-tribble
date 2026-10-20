"""Learning reports computed from persisted messages; no fabricated scores."""
import re
from collections import Counter

def build_report(session, scene, messages):
    user_messages = [m for m in messages if m.role == "user"]
    ai_messages = [m for m in messages if m.role == "assistant"]
    words = re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)*", " ".join(m.content for m in user_messages))
    hints = []
    for message in ai_messages:
        if "[Hint" in message.content:
            hints.append({"message_id": message.id, "content": message.content[message.content.index("[Hint"):].strip()})
    return {
        "session_id": session.id,
        "scene_title": scene.title,
        "difficulty": scene.difficulty,
        "goal": scene.goal,
        "language_goals": scene.language_goals,
        "started_at": session.created_at,
        "last_activity_at": session.updated_at,
        "user_messages": len(user_messages),
        "ai_messages": len(ai_messages),
        "english_words": len(words),
        "unique_english_words": len(set(w.lower() for w in words)),
        "frequent_words": [{"word": w, "count": n} for w, n in Counter(w.lower() for w in words).most_common(8)],
        "expressions": [{"message_id": m.id, "content": m.content} for m in user_messages[-5:]],
        "hints": hints,
        "next_step": "先向场景角色介绍自己，开始第一轮英文交流。" if not user_messages else ("回看角色给出的 Hint，改写其中一句表达，再围绕场景目标继续对话。" if hints else "回看最近的英文表达，尝试给出理由、举例或提出追问，继续完成场景目标。"),
        "note": "根据已保存的会话记录统计；英文词数按字母词匹配，重复词计入总数。未评估熟练度、语法正确率或任务完成度。",
    }
