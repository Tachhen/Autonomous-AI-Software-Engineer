from dotenv import load_dotenv
from agent.agent import CodingAgent


def main():
    load_dotenv()
    workspace = "./workspace/demo-project"
    agent = CodingAgent(workspace)
    task = input("TASK? ")
    print("\nStarting autonomous agent...\n")
    result = agent.run(task)
    print("\nFINAL RESULT\n")
    print(result)

if __name__ == "__main__":
    main()