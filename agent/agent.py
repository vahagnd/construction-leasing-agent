from langchain_together import Together
from mcp_adapter import McpAdapter
from langchain.agents import initialize_agent, AgentType
import asyncio

llm = Together(
    model="lgai/exaone-3-5-32b-instruct",
    temperature=0.0,
    max_tokens=200,
)

async def main():
    adapter = await McpAdapter.from_command("python server.py")
    await adapter.initialize()
    tools = await adapter.get_tools()

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

    query = (
        "Вот неструктурированный текст лизингового контракта:\n"
        'Компания: ООО "СТРОЙГРАНИТ"\n'
        "Дата заключения контракта: 22.05.2025\n"
        "Информация о контракте:\n"
        "Предмет финансовой аренды: Экскаватор-погрузчик JCB 3CX\n"
        "Срок финансовой аренды: 22.05.2025 - 22.05.2028\n"
        "Комментарий пользователя: <res>Подписан</res>\n\n"
        "Твоя задача:\n"
        "1. Извлеки из текста информацию о сделке: название компании, предмет лизинга и дату заключения контракта. "
        "Оформи это в одно предложение.\n"
        "2. Определи, является ли предмет лизинга строительной техникой. "
        "Если это не строительная техника — верни '400' и остановись.\n"
        "3. Если это строительная техника — сохрани информацию о сделке в JSON-файл. "
        "Записать нужно: исходный текст информации о сделке и отдельно дату.\n"
        "Используй доступные тебе инструменты, чтобы выполнить задание. Не делай шаги сам, вызывай нужные функции.\n"
        "Не придумывай информацию, вся информация в тексте лизингового контракта."
    )

    result = agent.run(query)
    print("\n📋 FINAL RESULT:")
    print(result)

    await adapter.close()

if __name__ == "__main__":
    asyncio.run(main())
