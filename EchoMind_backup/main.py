from agentuity import Agent, event
import requests, os

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

class EchoMind(Agent):
    def __init__(self):
        super().__init__()
        self.memory = []

    @event("message")
    def on_message(self, message):
        """当有新消息进来时触发"""
        summary = self.summarize_message(message)
        if summary:
            self.memory.append(summary)
            if len(self.memory) > 10:  # 保持短期记忆长度
                self.memory.pop(0)
            print(f"[EchoMind] Updated memory: {self.memory}")

    def summarize_message(self, text):
        """调用 OpenRouter LLM 总结重点"""
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Extract key facts and intentions from this text."},
                {"role": "user", "content": text}
            ]
        }
        try:
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=body,
                timeout=20
            )
            res.raise_for_status()
            data = res.json()
            summary = data["choices"][0]["message"]["content"]
            return summary
        except Exception as e:
            print(f"[EchoMind Error] LLM summarization failed: {e}")
            return None

    @event("get_memory")
    def get_memory(self):
        """返回当前短期记忆"""
        return self.memory

# 创建 agent 实例
agent = EchoMind()