from dotenv import load_dotenv
import anthropic, json

load_dotenv()
client = anthropic.Anthropic()

# PART 1: THE CAR (sample data shaped like Tesla's real API; we swap in your real car later)
def get_battery():
    return {"battery_level": 72, "battery_range_miles": 210, "charging_state": "Disconnected"}

def get_climate():
    return {"inside_temp_c": 18.5, "outside_temp_c": 12.0, "is_climate_on": False}

# PART 2: THE TOOL MENU (tells Claude which tools exist and when to use them)
tools = [
    {"name": "get_battery",
     "description": "Get the car's battery percent, estimated range in miles, and charging status.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "get_climate",
     "description": "Get the car's inside and outside temperature (Celsius) and whether climate is on.",
     "input_schema": {"type": "object", "properties": {}}},
]
TOOL_FUNCTIONS = {"get_battery": get_battery, "get_climate": get_climate}

# PART 3: THE AGENT LOOP (ask Claude -> run the tool it picks -> give it the result -> repeat)
def ask(question):
    messages = [{"role": "user", "content": question}]
    while True:
        response = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=1000,
            system="You are EV Copilot, an assistant for the user's electric car. "
                   "Always use tools to get car data. Never guess numbers.",
            tools=tools,
            messages=messages,
        )
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"   [tool] Claude is using: {block.name}")
                output = TOOL_FUNCTIONS[block.name]()
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": json.dumps(output)})
        messages.append({"role": "user", "content": results})

while True:
    question = input("\nYou: ")
    if question.lower() in ("quit", "exit"):
        break
    print("Copilot:", ask(question))
