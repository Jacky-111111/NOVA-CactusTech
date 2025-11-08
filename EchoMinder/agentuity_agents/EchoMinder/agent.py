from agentuity import AgentRequest, AgentResponse, AgentContext
from openai import AsyncOpenAI
import json, os

client = AsyncOpenAI()

# =========================
# 三层记忆结构
# =========================
short_term = []     # 最近摘要（进程内）
mid_term = []       # 中期合并摘要（缓存）
long_term = []      # 永久存储（本地文件）
LONG_TERM_FILE = "long_term.json"
SHORT_LIMIT = 10
MID_LIMIT = 10

# -------------------------
# 加载长期记忆
# -------------------------
def load_long_term():
    global long_term
    if os.path.exists(LONG_TERM_FILE):
        try:
            with open(LONG_TERM_FILE, "r") as f:
                long_term = json.load(f)
        except Exception:
            long_term = []

def save_long_term():
    try:
        with open(LONG_TERM_FILE, "w") as f:
            json.dump(long_term, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

load_long_term()

# -------------------------
# 主逻辑
# -------------------------
async def run(request: AgentRequest, response: AgentResponse, context: AgentContext):
    try:
        text = (await request.data.text()).strip().lower()
        context.logger.info(f"[EchoMinder] Received: {text}")

        # 🔍 1️⃣ 显示记忆
        if text.startswith("show memory") or text.startswith("recall"):
            return response.json({
                "mode": "recall",
                "short_term": short_term[-SHORT_LIMIT:],
                "mid_term": mid_term[-5:],
                "long_term": long_term[-5:]
            })

        # 💾 2️⃣ 主动记忆指令
        if text.startswith("remember that"):
            fact = text.replace("remember that", "").strip()
            if not fact:
                fact = text
            long_term.append(fact)
            save_long_term()
            return response.json({
                "mode": "store",
                "stored_fact": fact,
                "long_term_total": len(long_term)
            })

        # 🧠 3️⃣ 自动摘要 + 记忆更新
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Summarize this input in one concise factual sentence."},
                {"role": "user", "content": text}
            ]
        )
        summary = completion.choices[0].message.content.strip()

        # 更新短期
        short_term.append(summary)
        if len(short_term) > SHORT_LIMIT:
            short_term.pop(0)

        # 更新中期
        mid_term.append(summary)
        if len(mid_term) >= MID_LIMIT:
            merge_input = " | ".join(mid_term)
            merge_completion = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Combine the following summaries into one coherent paragraph that captures all key ideas without redundancy."},
                    {"role": "user", "content": merge_input}
                ]
            )
            merged_summary = merge_completion.choices[0].message.content.strip()
            long_term.append(merged_summary)
            save_long_term()
            mid_term.clear()
            context.logger.info("[EchoMinder] Mid-term merged into long-term memory.")

        context.logger.info(f"[EchoMinder] Stored summary: {summary}")

        return response.json({
            "mode": "encode",
            "summary": summary,
            "short_term_tail": short_term[-5:],
            "mid_term_tail": mid_term[-3:],
            "long_term_total": len(long_term),
            "hint": "Say 'recall' or 'show memory' to review stored knowledge."
        })

    except Exception as e:
        context.logger.error(f"[EchoMinder] Error: {e}")
        return response.text(f"EchoMinder error: {e}")