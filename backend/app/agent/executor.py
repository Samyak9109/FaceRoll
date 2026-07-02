from datetime import date

from app.core.config import get_settings
from app.agent.tools import build_tools


def _llm():
    settings = get_settings()
    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=settings.llm_model, api_key=settings.openai_api_key, temperature=0)
    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=settings.llm_model, api_key=settings.anthropic_api_key, temperature=0)

    from langchain_ollama import ChatOllama

    return ChatOllama(model=settings.llm_model, temperature=0)


async def run_agent_query(db, query: str) -> str:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate

    tools = build_tools(db)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an attendance assistant. Today's date is {today}. "
                "Use tools for factual MongoDB data. Dates must be YYYY-MM-DD. "
                "If the user says today, use {today}. Keep answers concise.",
            ),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    agent = create_tool_calling_agent(_llm(), tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
    result = await executor.ainvoke({"input": query, "today": date.today().isoformat()})
    return str(result.get("output", result))
