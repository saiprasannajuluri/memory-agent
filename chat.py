from agent import ask_agent, save_call

borrower = input("Borrower ID (example: borrower-1042): ")

while True:
    print("\nType 1 = ask the agent, 2 = log a call, 3 = quit")
    choice = input("> ")

    if choice == "1":
        question = input("Your question: ")
        answer, memory = ask_agent(borrower, question)
        print("\n--- What I remember ---\n" + memory)
        print("\n--- My advice ---\n" + answer)

    elif choice == "2":
        notes = input("What happened on the call? ")
        save_call(borrower, notes)
        print("Saved to memory.")

    elif choice == "3":
        break