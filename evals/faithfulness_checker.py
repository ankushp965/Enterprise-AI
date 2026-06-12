import ollama

def check_faithfulness(context: str, answer: str):
    prompt = f"""
You are an AI evaluator.
Your task is to determine whether the answer is fully supported by the provided context.
Context:
{context}

Answer:
{answer}
Respond ONLY with:
FAITHFUL
or
NOT_FAITHFUL
"""
    response = ollama.chat(
        model="gemma4:e4b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    result = response['message']['content'].strip()

    return result