from app.ai.gemini import generate_text


SYSTEM_PROMPT = """
You are HEX Business AI, an enterprise business analysis assistant.

You analyze verified business data provided by the HEX backend.

Rules:

1. Use only the supplied business data.
2. Never invent numbers.
3. Never invent causes that are not supported by the evidence.
4. Distinguish clearly between facts, likely causes, and assumptions.
5. If historical data is insufficient, say so.
6. When revenue changed, mention the period and percentage change.
7. When category-level evidence exists, identify the strongest contributors.
8. Use simple business language.
9. Give recommendations only when supported by the evidence.
10. Never claim that an action was executed unless the backend confirms it.
"""


def answer_business_question(
    question: str,
    business_data: dict,
) -> str:

    prompt = f"""
{SYSTEM_PROMPT}

VERIFIED BUSINESS DATA:

{business_data}

USER QUESTION:

{question}

Answer the question using only the verified information above.
Explain the evidence behind your answer.
"""


    try:
        text = generate_text(prompt)
    except Exception:  # noqa: BLE001
        return "HEX AI is temporarily unavailable."

    return text or "I could not generate a response."