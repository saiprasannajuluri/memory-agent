
import os
from dotenv import load_dotenv
from hindsight_client import Hindsight


load_dotenv()


hs = Hindsight(
    base_url=os.getenv("HINDSIGHT_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY"),
)


hs.retain(
    bank_id="borrower-1042",
    content="Ravi Kumar promised to pay his EMI of Rs 18,500 on 7th October. He said his salary is delayed.",
    context="collection call",
    timestamp="2026-09-20T11:00:00Z",
)
print("Saved to memory!")


result = hs.recall(bank_id="borrower-1042", query="What did Ravi promise?")

# 6. Print every memory it found
for memory in result.results:
    print("-", memory.text)