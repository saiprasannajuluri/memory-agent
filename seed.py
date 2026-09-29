import json
from agent import hs

with open("borrowers.json") as f:
    borrowers = json.load(f)

for b in borrowers:
    intro = f"{b['name']} drives a {b['car']}. Monthly EMI is Rs {b['emi']}."
    hs.retain(bank_id=b["id"], content=intro, context="borrower profile")

    for call in b["calls"]:
        hs.retain(bank_id=b["id"], content=call["notes"],
                  context="collection call", timestamp=call["date"])
        hs.retain(bank_id="team-playbook", content=b["id"] + ": " + call["notes"],
                  context="collection call outcome", timestamp=call["date"])

    print("Loaded", b["name"])

print("All done!")