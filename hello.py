from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()

reply = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=200,
    messages=[{"role": "user", "content": "Say hi to a new agent builder in one sentence."}],
)
print(reply.content[0].text)
