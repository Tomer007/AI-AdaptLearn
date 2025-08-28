from app.services.agents.qa.qa_agent import QAAgent

def main() -> None:
    agent = QAAgent()
    print(type(agent.llm).__name__)

if __name__ == "__main__":
    main()


