from agentuity import AgentRequest, AgentResponse, AgentContext
from openai import AsyncOpenAI
import json
import os
from typing import List, Dict, Any, Optional

client = AsyncOpenAI()

# =========================
# 🧠 Three-Layer Memory Structure
# =========================
short_term: List[str] = []     # Short-term memory (in-process)
mid_term: List[str] = []       # Mid-term merged summaries (cached)
long_term: List[str] = []      # Long-term memory (persisted to file)

LONG_TERM_FILE = "long_term_new.json"  # Use a separate file to avoid conflict with EchoMinder
SHORT_LIMIT = 10
MID_LIMIT = 10

# -------------------------
# 📁 File Path Handling (relative to agent directory)
# -------------------------
def get_long_term_path() -> str:
    """Get the full path of the long-term memory file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "..", "..", LONG_TERM_FILE)

# -------------------------
# 💾 Load / Save Long-Term Memory
# -------------------------
def load_long_term():
    """Load long-term memory from file"""
    global long_term
    file_path = get_long_term_path()
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                long_term = json.load(f)
        except Exception as e:
            long_term = []
            print(f"[EchoMinderNew] Failed to load long-term memory: {e}")

def save_long_term():
    """Save long-term memory to file"""
    try:
        file_path = get_long_term_path()
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(long_term, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[EchoMinderNew] Failed to save long-term memory: {e}")

# Initialize by loading long-term memory
load_long_term()

# -------------------------
# 🔍 Intelligent Memory Retrieval
# -------------------------
async def retrieve_relevant_memories(query: str, limit: int = 5) -> List[str]:
    """
    Retrieve relevant memories based on a query from all three memory layers.
    Prioritize long-term memory but include mid- and short-term ones.
    """
    query_lower = query.lower()
    relevant = []
    all_memories = []

    # 1. Long-term memory (highest priority)
    for memory in long_term:
        all_memories.append(("long", memory))

    # 2. Mid-term memory
    for memory in mid_term:
        all_memories.append(("mid", memory))

    # 3. Short-term memory (most recent and important)
    for memory in short_term:
        all_memories.append(("short", memory))

    if not all_memories:
        return []

    # Keyword matching — smarter retrieval
    stop_words = {"is", "are", "was", "were", "the", "a", "an", "what", "where", "when", "who", "how", "why"}
    query_words = [w for w in query_lower.split() if len(w) > 1 and w not in stop_words]

    # Expand keywords (handle synonyms and variants)
    expanded_keywords = set(query_words)
    keyword_mapping = {
        "fav": ["favorite", "prefer", "like", "love", "preference"],
        "language": ["programming", "code", "coding", "lang"],
        "programming": ["code", "coding", "language", "lang"],
        "what": ["tell", "say", "remember", "know"],
        "my": ["i", "me", "user"],
        "python": ["python", "py"],
    }
    for word in query_words:
        if word in keyword_mapping:
            expanded_keywords.update(keyword_mapping[word])
        expanded_keywords.add(word)

    for memory_type, memory in all_memories:
        memory_lower = memory.lower()
        if expanded_keywords and any(word in memory_lower for word in expanded_keywords):
            relevant.append(memory)
            if len(relevant) >= limit:
                break

    if not relevant and query_words:
        for memory_type, memory in all_memories:
            memory_lower = memory.lower()
            if any(word in memory_lower for word in query_words):
                relevant.append(memory)
                if len(relevant) >= limit:
                    break

    # If no matches, return most recent ones (prefer short-term)
    if not relevant:
        if short_term:
            relevant = short_term[-min(limit, len(short_term)):]
        elif mid_term:
            relevant = mid_term[-min(limit, len(mid_term)):]
        elif long_term:
            relevant = long_term[-min(limit, len(long_term)):]
    
    return relevant

# -------------------------
# 📝 Summary Generation
# -------------------------
async def generate_summary(text: str, is_user_message: bool = True) -> str:
    """Generate a concise factual summary of the input text"""
    role = "user" if is_user_message else "assistant"
    system_prompt = (
        "Summarize this message as a concise factual statement about the user, "
        "their preferences, context, or important information. "
        "Focus on information that should be remembered for future conversations."
    )

    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": role, "content": text}
            ],
            temperature=0.3
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"User mentioned: {text[:100]}"

# -------------------------
# 🔄 Merge Mid-Term Memories
# -------------------------
async def merge_mid_term_memories() -> str:
    """Merge all mid-term memories into one long-term summary"""
    if not mid_term:
        return ""
    
    merge_input = " | ".join(mid_term)
    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Combine these factual summaries into one coherent memory paragraph "
                              "that captures all key information without redundancy."
                },
                {"role": "user", "content": merge_input}
            ],
            temperature=0.3
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return " | ".join(mid_term)

# -------------------------
# 🎯 Build Enhanced Prompt
# -------------------------
async def build_enhanced_prompt(
    user_message: str,
    include_memory: bool = True
) -> Dict[str, Any]:
    """
    Build an enhanced prompt that includes contextual memory information.
    Returns a dict containing the original message and memory context.
    """
    result = {
        "original_message": user_message,
        "memory_context": "",
        "enhanced_prompt": user_message
    }

    if include_memory:
        relevant_memories = await retrieve_relevant_memories(user_message, limit=8)

        # Always include recent memory if none found
        if not relevant_memories:
            if short_term:
                relevant_memories = short_term[-5:]
            elif mid_term:
                relevant_memories = mid_term[-3:]
            elif long_term:
                relevant_memories = long_term[-3:]
        else:
            # Add recent short-term memories for better recall continuity
            if short_term and len(relevant_memories) < 8:
                recent_short = short_term[-3:]
                for mem in recent_short:
                    if mem not in relevant_memories:
                        relevant_memories.append(mem)
                        if len(relevant_memories) >= 8:
                            break
        
        if not relevant_memories and short_term:
            relevant_memories = short_term.copy()
        
        if relevant_memories:
            memory_context = "\n".join([f"- {memory}" for memory in relevant_memories])
            result["memory_context"] = memory_context
            enhanced = (
                "You are a helpful AI assistant. Below is important context about the user that you MUST remember and use:\n\n"
                f"{memory_context}\n\n"
                f"User's current question: {user_message}\n\n"
                "IMPORTANT: Use the context above to answer the user's question. If the context contains relevant information, you MUST use it in your response. "
                "For example, if the user asks about their favorite language and the context mentions it, you should tell them what it is based on the context."
            )
            result["enhanced_prompt"] = enhanced
    
    return result

# -------------------------
# 🌐 Main Logic
# -------------------------
async def run(request: AgentRequest, response: AgentResponse, context: AgentContext):
    """
    EchoMinderNew - Long-term memory agent
    Features:
    1. Automatically remembers user and chatbot conversations
    2. Generates summaries and stores them across three memory layers
    3. Returns an enhanced prompt containing relevant memory context
    """
    try:
        content_type = request.data.contentType or ""
        user_message = ""
        chatbot_reply = ""
        mode = "auto"
        
        try:
            if "json" in content_type.lower():
                data = await request.data.json()
                user_message = data.get("user_message", "")
                chatbot_reply = data.get("chatbot_reply", "")
                mode = data.get("mode", "auto")
                context.logger.info(f"[EchoMinderNew] Received JSON - User: {user_message[:50]}..., Mode: {mode}")
            else:
                try:
                    text = await request.data.text()
                    import json as json_lib
                    data = json_lib.loads(text)
                    user_message = data.get("user_message", "")
                    chatbot_reply = data.get("chatbot_reply", "")
                    mode = data.get("mode", "auto")
                    context.logger.info(f"[EchoMinderNew] Parsed JSON from text - User: {user_message[:50]}..., Mode: {mode}")
                except (json_lib.JSONDecodeError, ValueError):
                    user_message = text.strip()
                    chatbot_reply = ""
                    mode = "auto"
                    context.logger.info(f"[EchoMinderNew] Received text - User: {user_message[:50]}...")
        except Exception as e:
            try:
                text = (await request.data.text()).strip()
                user_message = text
                chatbot_reply = ""
                mode = "auto"
                context.logger.info(f"[EchoMinderNew] Fallback to text - User: {user_message[:50]}..., Error: {e}")
            except Exception as e2:
                context.logger.error(f"[EchoMinderNew] Failed to parse request: {e2}")
                return response.json({
                    "mode": "error",
                    "error": f"Failed to parse request: {str(e2)}",
                    "enhanced_prompt": ""
                })
        
        if not user_message and mode == "auto":
            context.logger.warning("[EchoMinderNew] Empty user message in auto mode")
        
        # ==========================================================
        # 1️⃣ Recall Mode - Show Memory
        # ==========================================================
        if mode == "recall" or (user_message and user_message.lower().startswith(("show memory", "recall"))):
            memory_summary = {
                "short_term": short_term[-SHORT_LIMIT:],
                "mid_term": mid_term[-5:],
                "long_term": long_term[-5:],
                "total_counts": {
                    "short_term": len(short_term),
                    "mid_term": len(mid_term),
                    "long_term": len(long_term)
                }
            }
            context.logger.info(f"[EchoMinderNew] Returning memory summary")
            return response.json({
                "mode": "recall",
                "memory": memory_summary
            })
        
        # ==========================================================
        # 2️⃣ Manual Remember Command
        # ==========================================================
        if mode == "remember" or (user_message and user_message.lower().startswith("remember")):
            fact = user_message
            if user_message.lower().startswith("remember that"):
                fact = user_message.replace("remember that", "", 1).strip()
            elif user_message.lower().startswith("remember"):
                fact = user_message.replace("remember", "", 1).strip()
            
            if fact:
                long_term.append(fact)
                save_long_term()
                short_term.append(fact)
                if len(short_term) > SHORT_LIMIT:
                    short_term.pop(0)
                mid_term.append(fact)
                if len(mid_term) >= MID_LIMIT:
                    merged_summary = await merge_mid_term_memories()
                    if merged_summary:
                        long_term.append(merged_summary)
                        save_long_term()
                        mid_term.clear()
                context.logger.info(f"[EchoMinderNew] Stored fact manually: {fact}")
                return response.json({
                    "mode": "store",
                    "stored_fact": fact,
                    "long_term_total": len(long_term),
                    "short_term_count": len(short_term),
                    "mid_term_count": len(mid_term)
                })
        
        # ==========================================================
        # 3️⃣ Auto Memory and Enhanced Prompt Mode
        # ==========================================================
        if user_message:
            user_summary = await generate_summary(user_message, is_user_message=True)
            short_term.append(user_summary)
            if len(short_term) > SHORT_LIMIT:
                short_term.pop(0)
            mid_term.append(user_summary)
            if len(mid_term) >= MID_LIMIT:
                merged_summary = await merge_mid_term_memories()
                if merged_summary:
                    long_term.append(merged_summary)
                    save_long_term()
                    mid_term.clear()
                    context.logger.info("[EchoMinderNew] Merged mid-term into long-term memory.")
            context.logger.info(f"[EchoMinderNew] Stored user summary: {user_summary}")
        
        if chatbot_reply:
            chatbot_summary = await generate_summary(chatbot_reply, is_user_message=False)
            short_term.append(f"Chatbot: {chatbot_summary}")
            if len(short_term) > SHORT_LIMIT:
                short_term.pop(0)
            context.logger.info(f"[EchoMinderNew] Stored chatbot summary: {chatbot_summary}")
        
        enhanced_prompt_data = await build_enhanced_prompt(
            user_message if user_message else "",
            include_memory=True
        )
        
        return response.json({
            "mode": "auto",
            "enhanced_prompt": enhanced_prompt_data["enhanced_prompt"],
            "memory_context": enhanced_prompt_data["memory_context"],
            "original_message": enhanced_prompt_data["original_message"],
            "memory_stats": {
                "short_term_count": len(short_term),
                "mid_term_count": len(mid_term),
                "long_term_count": len(long_term)
            },
            "hint": "Use the 'enhanced_prompt' field as input to your chatbot. "
                   "It contains the user's message with relevant memory context."
        })
    
    except Exception as e:
        context.logger.error(f"[EchoMinderNew] Error: {e}", exc_info=True)
        return response.json({
            "mode": "error",
            "error": str(e),
            "enhanced_prompt": user_message if 'user_message' in locals() else ""
        })
