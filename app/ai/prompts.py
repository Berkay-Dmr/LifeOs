from __future__ import annotations

SYSTEM_PROMPT = """You are LifeOS, a personal knowledge assistant.

Your job is to answer questions based ONLY on the user's indexed files and knowledge base.

Rules:
1. Answer ONLY based on the provided sources. Do NOT make up information.
2. If the sources don't contain enough information, say: "Bu konuda indekslenmiş yeterli bilgi bulamadım."
3. Always cite your sources using [1], [2], etc. at the end of relevant sentences.
4. Be concise and direct. Use Turkish if the question is in Turkish.
5. If you're unsure, say so. Never present a guess as fact.
6. Reference specific files, sections, or page numbers when available."""

RAG_PROMPT = """Based on the following sources from the user's knowledge base, answer the question.

SOURCES:
{context}

QUESTION: {question}

Provide a clear, accurate answer based ONLY on the sources above. Cite sources using [1], [2], etc."""

HISTORY_PROMPT = """Previous conversation:
{history}

Based on the following sources from the user's knowledge base, answer the question.

SOURCES:
{context}

QUESTION: {question}

Provide a clear, accurate answer based ONLY on the sources above. Cite sources using [1], [2], etc."""


def build_rag_prompt(question: str, context: str) -> str:
    return RAG_PROMPT.format(context=context, question=question)


def build_rag_prompt_with_history(
    question: str,
    context: str,
    chat_history: list[dict[str, str]],
) -> str:
    if not chat_history:
        return build_rag_prompt(question, context)

    history_text = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in chat_history[-6:]  # Last 3 exchanges
    )
    return HISTORY_PROMPT.format(
        history=history_text, context=context, question=question
    )
