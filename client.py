import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters, types
from dotenv import load_dotenv
import json
from openai import OpenAI
import os
from pprint import pformat
import logging
from time import sleep

logger = logging.getLogger(__name__)
load_dotenv()

API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_URL = os.getenv("TOGETHER_API_BASE")
MODEL_NAME = os.getenv("LLAMA")

tools_specs = []

def set_tools(tools: list[types.Tool]):
    for tool in tools:
        logger.info("register tool: %s", pformat(tool.name))
        tools_specs.append({
            'type': 'function',
            'function': {
                'name': tool.name,
                'description': tool.description,
                'parameters': {
                    'type': 'object',
                    'required': tool.inputSchema["required"],
                    'properties': {
                        prop: {
                            "type": prop_data["type"]
                        }
                        for prop, prop_data in tool.inputSchema["properties"].items()
                    },
                },
            }
        })

async def sampling_message_callback(
        context,
        params: types.CreateMessageRequestParams,
) -> types.CreateMessageResult:
    logging.debug("sampling: %s", params)

    input_message = params.messages[0]
    logging.debug("sampling message: %s", input_message)
    messages = [
        {
            "role": input_message.role,
            "content": input_message.content.text
        }
    ]

    logging.debug("sleeping before sampling llm call")
    sleep(2) # to handle too many requests
    with OpenAI(base_url=TOGETHER_URL, api_key=API_KEY) as sampling_llm_client:
        completion = sampling_llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
        )

        logging.debug("sampling completion response: %s", completion)
        resp_choice = completion.choices[0]
        resp_message = resp_choice.message.content
        logging.debug("sampling message response: %s", resp_message)

    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text=resp_message,
        ),
        model=MODEL_NAME,
        stopReason="endTurn",
    )

async def notifications_callback(
        params: types.LoggingMessageNotificationParams,
) -> None:
    logger.info(params)

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
                read,
                write,
                sampling_callback=sampling_message_callback,
                logging_callback=notifications_callback
        ) as session:
            await session.initialize()

            tools_response = await session.list_tools()
            set_tools(tools_response.tools)
            logger.info("tools:\n%s", pformat(tools_specs))

            result = await session.read_resource("fedresurs://contracts/2025-01-20/2025-02-01")
            contracts = json.loads(result.contents[0].text)["contracts"]

            # input_text = (
            #     'Компания: ООО "СТРОЙМАГИСТРАЛЬ"\n'
            #     "Дата заключения контракта: 14.04.2025\n"
            #     "Информация о контракте:\n"
            #     "Предмет финансовой аренды: LZZ7CMWDXRC643572, 0106008 экскаваторы, SITRAK C7H MAX\n"
            #     "Срок финансовой аренды: 15.04.2025 - 15.03.2028\n"
            #     "Комментарий пользователя: <res>Заключение</res>"
            # )
            #
            # contracts = [input_text]

            with OpenAI(base_url=TOGETHER_URL, api_key=API_KEY) as llm_client:
                for contract in contracts:
                    tool_used = False
                    for i in range(2):
                        current_tools = tools_specs if not tool_used else None
                        messages = [
                            {
                                "role": "system",
                                "content": (
                                    "Ты — профессиональный аналитик договоров лизинговых контрактов.\n"
                                    "Если текст контракта, который тебе дали, РОВНО РАВЕН:\n"
                                    "  - '400'\n"
                                    "  - ИЛИ начинается с 'Компания ' и содержит ' заключила контракт лизинга на ' и заканчивается на дату в формате 'гггг-мм-дд'\n"
                                    "ТОГДА ничего не делай, просто верни этот текст как есть и не вызывай инструмент.\n\n"
                                    "Если же формат другой — тогда:\n"
                                    "- Определи, является ли предмет строительной техникой.\n"
                                    "- Если НЕ является — верни '400'.\n"
                                    "- Если является — верни ответ строго в следующем формате:\n"
                                    "Компания <название> заключила контракт лизинга на <предмет> <дата в формате гггг-мм-дд>.\n"
                                    "Никаких других слов, разметок, пояснений или альтернативных формулировок."
                                )
                            },
                            {
                                "role": "user",
                                "content": f"Вот текст контракта: {contract.strip()}."
                            }
                        ]
                        logging.debug("sleeping before main llm call")
                        sleep(2) # to handle too many requests
                        completion = llm_client.chat.completions.create(
                            model=MODEL_NAME,
                            messages=messages,
                            tools=current_tools
                        )

                        logger.debug("completion response:\n%s", pformat(completion))
                        resp_choice = completion.choices[0]
                        messages.append(resp_choice.message)
                        logger.debug("completion message:\n%s", pformat(resp_choice))

                        reason = resp_choice.finish_reason

                        if reason == "tool_calls":
                            response_tools = resp_choice.message.tool_calls
                            tool_call = response_tools[0]
                            logger.debug("tool call response: %s, %s", tool_call, type(tool_call))

                            tool_call_args = json.loads(tool_call.function.arguments)
                            logger.debug("tool call args: %s, %s", tool_call_args, type(tool_call_args))

                            result_tool = await session.call_tool(tool_call.function.name, arguments=tool_call_args)
                            tool_response = result_tool.content[0].text
                            logger.debug("tool response: %s", tool_response)

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": tool_response
                            })
                        else:
                            final_answer = resp_choice.message.content
                            logger.debug("final answer: %s", final_answer)

                            if final_answer.strip() != "400":
                                logger.info("saving contract to json")
                                args = {"contract_info": final_answer}
                                await session.call_tool("save_leasing_info", arguments=args)
                            break
                        logger.debug("messages:\n%s", messages)
                        tool_used = True

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(module)s - %(message)s"
    )
    asyncio.run(main())
