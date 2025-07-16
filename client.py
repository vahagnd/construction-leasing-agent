import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import initialize_agent, Tool
from langchain_together import Together
from dotenv import load_dotenv

load_dotenv()  # Load TOGETHER_API_KEY

llama = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
exaone = "lgai/exaone-3-5-32b-instruct"
exaone_deep = "lgai/exaone-deep-32b"


async def main():
    # 1. Connect to your server
    server_params = stdio_client(command="python", args=["server.py"])

    llama = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
    exaone = "lgai/exaone-3-5-32b-instruct"
    exaone_deep = "lgai/exaone-deep-32b"

    llm = Together(
        model=exaone,
        temperature=0.0,
        max_tokens=200
    )

    async with server_params as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await load_mcp_tools(session)
            agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

            tools_response = await session.list_tools()
            print("Available tools: ", [tool.name for tool in tools_response.tools])

            result = await session.read_resource("fedresurs://contracts/2025-01-20/2025-02-01")
            contracts = result.content["contracts"]

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
                    await agent.arun(input_text)
                except Exception as e:
                    print(f"Ошибка при обработке: {e}")

            print(result)

asyncio.run(main())
