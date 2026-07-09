from agent.graph import run_agent

result = run_agent("What's the average revenue by region?")

print("\n--- STEPS ---")
for s in result["steps_log"]:
    print(s)

print("\n--- FINAL ANSWER ---")
print(result["final_answer"])