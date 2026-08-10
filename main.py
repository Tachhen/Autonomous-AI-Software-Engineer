from dotenv import load_dotenv

from agent.agent import CodingAgent


def main():

    load_dotenv()

    workspace = "./workspace/demo-project"

    agent = CodingAgent(workspace)

    task = input("What should the AI engineer do? ")

    print("\nStarting autonomous agent...\n")

    result = agent.run(task)

    print("\n===== FINAL RESULT =====\n")
    print(result)


if __name__ == "__main__":
    main()