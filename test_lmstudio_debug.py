from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

try:
    response = client.chat.completions.create(
        model="local-model",
        messages=[{"role": "user", "content": "Say 'Hello world'"}],
        max_tokens=50
    )
    print("✅ Raw response:", repr(response.choices[0].message.content))
except Exception as e:
    print("❌ Error:", e)