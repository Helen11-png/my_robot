from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

response = client.chat.completions.create(
    model="local-model",
    messages=[{"role": "user", "content": "Say 'Hello, I am ready' in 5 words"}],
    max_tokens=20
)

print("✅ LM Studio says:", response.choices[0].message.content)