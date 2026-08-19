import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_groq():
    api_key = os.environ.get("GROQ_API_KEY", "")
    print(f"1. GROQ_API_KEY Configured: {'YES (Key Present)' if api_key else 'NO (Missing)'}")
    if not api_key:
        print("ERROR: GROQ_API_KEY is not set in environment or .env file.")
        return

    models_to_test = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-8b-8192"]
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for model in models_to_test:
        print(f"\n--- Testing Groq Model: {model} ---")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello, respond with JSON: {\"status\": \"ok\"}"}],
            "max_tokens": 50,
            "temperature": 0.1
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                print(f"HTTP Status: {res.status_code}")
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    print(f"Response Received: {content}")
                    print(f"MODEL '{model}': PASS!")
                else:
                    print(f"HTTP Error ({res.status_code}): {res.text}")
        except Exception as e:
            print(f"Exception for model {model}: {e}")

if __name__ == "__main__":
    asyncio.run(test_groq())
