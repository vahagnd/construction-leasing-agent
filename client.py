import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import initialize_agent, Tool, AgentType, AgentExecutor
from langchain_together import Together
from dotenv import load_dotenv
import json

load_dotenv()  # Load TOGETHER_API_KEY

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"]
    )

    llama = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
    exaone = "lgai/exaone-3-5-32b-instruct"
    exaone_deep = "lgai/exaone-deep-32b"

    llm = Together(
        model=exaone,
        temperature=0.0,
        max_tokens=200
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await load_mcp_tools(session)
            agent = initialize_agent(
                tools,
                llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            )

            # Parsing error handling
            agent_executor = AgentExecutor.from_agent_and_tools(
                agent=agent.agent,
                tools=tools,
                verbose=False,
                handle_parsing_errors=True  # Important
            )

            tools_response = await session.list_tools()
            print("Available tools: ", [tool.name for tool in tools_response.tools])

            result = await session.read_resource("fedresurs://contracts/2025-01-20/2025-02-01")
            contracts = json.loads(result.contents[0].text)["contracts"]

            print("Contracts parsed:", len(contracts))
            # print(f"Type: {type(contracts)}, Contracts: {contracts}")

            for i, contract in enumerate(contracts):
                input_text = (
                    f"Вот контракт: {contract.strip()}\n\n"
                    "Проанализируй этот контракт. "
                    "Используй инструмент 'analyze_contract_text', чтобы извлечь информацию. "
                    "Если результат НЕ равен '400', сохрани результат с помощью 'save_leasing_info'. "
                    "Если результат — '400', ничего не делай."
                )

                print(f"\nОбработка контракта #{i + 1}/{len(contracts)}")
                try:
                    await agent_executor.arun(input_text)
                except Exception as e:
                    print(f"Ошибка при обработке: {e}")

if __name__ == "__main__":
    asyncio.run(main())
