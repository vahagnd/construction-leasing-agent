import json
import os
from mcp.server.fastmcp import FastMCP, Context
from mcp import types
from langchain.chains import LLMChain
import requests
import time
import random
import asyncio
from dotenv import load_dotenv


load_dotenv()

CONTRACTS_PATH = os.getenv("CONTRACTS_PATH")

# Create MCP server
mcp = FastMCP("leasing-contract-server")

# ---- Helper Functions ----
def parse_data_from_fedresurs(start_date: str ='2025-01-01', end_date: str ='2025-06-01') -> list:
    data = []
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://fedresurs.ru/search/encumbrances",  # important
    }

    first_url = f"https://fedresurs.ru/backend/encumbrances?searchString=%D0%97%D0%B0%D0%BA%D0%BB%D1%8E%D1%87%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%B4%D0%BE%D0%B3%D0%BE%D0%B2%D0%BE%D1%80%D0%B0&group=Leasing&publishDateStart={start_date}T00%3A00%3A00&publishDateEnd={end_date}T23%3A59%3A59&limit=15&offset=0"
    first_response = requests.get(first_url, headers=headers)
    first_info_json = first_response.json()

    contracts_found = first_info_json['found']
    # print(f"Contracts found: {contracts_found}")
    time.sleep(random.uniform(1, 4))

    for offset in range(0, contracts_found, 15):
        try:
            url = f"https://fedresurs.ru/backend/encumbrances?searchString=%D0%97%D0%B0%D0%BA%D0%BB%D1%8E%D1%87%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%B4%D0%BE%D0%B3%D0%BE%D0%B2%D0%BE%D1%80%D0%B0&group=Leasing&publishDateStart={start_date}T00%3A00%3A00&publishDateEnd={end_date}T23%3A59%3A59&limit=15&offset={offset}"

            response = requests.get(url, headers=headers)
            info_json = response.json()

            for contract_i in range(min(15, contracts_found - offset)):
                try:
                    date_signed = info_json['pageData'][contract_i]['publishDate'][:10]
                    date_signed = '.'.join(reversed(date_signed.split('-')))
                    company_name = info_json['pageData'][contract_i]['weakSide'][0]['name']
                    contract_info = info_json['pageData'][contract_i]['searchStringHighlights'][1]
                    prompt_string = f"Компания: {company_name}\nДата заключения контракта: {date_signed}\nИнформация о контракте:\n{contract_info}"
                    data.append(prompt_string)
                except IndexError:
                    continue
        except:
            continue
        time.sleep(random.uniform(2, 6))

    # print(f"Contracts parsed: {len(data)}")
    return list(set(data))

# -- Resource: fetch info from website
@mcp.resource("fedresurs://contracts/{start_date}/{finish_date}")
def fetch_contracts(start_date: str, finish_date: str) -> dict:
    """
    Парсит и возвращает список строк с текстами контрактов из Fedresurs
    между start_date и finish_date.
    """
    raw_data_list = parse_data_from_fedresurs(start_date, finish_date)  # list[str]
    return {"contracts": raw_data_list}

# -- Tool: create or modify text document
@mcp.tool()
async def save_leasing_info(contract_info: str, ctx: Context) -> None:
    """
    Сохраняет информацию о лизинговом контракте в JSON.
    Принимает только одну строку со структурированной информацией о контракте.
    """
    file_path = CONTRACTS_PATH

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append({"contract_info": contract_info})

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await ctx.info("Контракт сохранен.")
    return None


# # -- Prompt: all logic is embedded into a single prompt template
# @mcp.prompt()
# def promptishe(contract_text: str) -> str:
#     return (
#         "Ты — профессиональный аналитик договоров лизинга.\n"
#         "Тебе нужно из следующего текста:\n"
#         "- определить название компании, заключивший контракт\n"
#         "- определить дату заключения контракта (в формате гггг-мм-дд)\n"
#         "- определить предмет лизинга\n"
#         "- определить, является ли предмет строительной техникой\n\n"
#         "Если предмет является строительной техникой, выводи в формате:\n"
#         "'Компания <название компании> заключила сделку лизинга на <предмет лизинга> <дата в формате гггг-мм-дд>.'"
#         "Если же предмет лизинга НЕ строительная техника: выводи '400'."
#         "Ничего не придумывай. Не добавляй лишнего. Не используй ковычки, точки, *, пояснения или дополнительные строки.\n"
#         "Не придумывай информацию, все есть в тексте контракта."
#         f"\nТекст контракта:\n{{contract_text}}\n"
#         "\nОтвет:"
#     )

# -- Tool : calls model giving it prompt via client sampling
@mcp.tool()
async def analyze_contract_text(contract_text: str, ctx: Context) -> str:
    """
    Извлекает из неструктурированного текста лизингового договора
    название компании заключившего контракт, дата заключения контракта, название предмета лизинга.
    Классифицирует предмет лизинга как строительая техника или нет.
    Если предмет НЕ строительная техника - выводит ОДНО ЧИСЛО - 400.
    Если же предмет строительая техника, то
    собирает все в одном предложении по формату:
    'Компания <название компании> заключила сделку лизинга на <предмет лизинга> <дата в формате гггг-мм-дд>.'.
    """
    prompt = (
        "Тебе нужно из следующего текста контракта:\n"
        "- определить название компании, заключивший контракт\n"
        "- определить дату заключения контракта (в формате гггг-мм-дд)\n"
        "- определить предмет лизинга\n"
        "- определить, является ли предмет строительной техникой\n\n"
        "Если предмет лизинга НЕ является строительной техиникой - выведи ТОЛьКО ОДНО ЧИСЛО - 400. "
        "Если же предмет лизинга строительная техника, то:\n"
        "собери информацию в предложении по формату:\n"
        "'Компания <название компании> заключила сделку лизинга на <предмет лизинга> <дата в формате гггг-мм-дд>.'"
        "Ничего не придумывай. Не добавляй лишнего. Не используй ковычки, точки, *, пояснения или дополнительные строки.\n"
        "Не придумывай информацию, все есть в тексте контракта."
        "\nТекст контракта:\n{contract_text}\n"
        "\nОтвет:"
    ).format(contract_text=contract_text)

    result = await ctx.session.create_message(
        messages=[
            types.SamplingMessage(
                role="user",
                content=types.TextContent(type="text", text=prompt),
            )
        ],
        max_tokens=200,
        temperature=0
    )

    if result.content.type == "text":
        return result.content.text
    return str(result.content)

if __name__ == "__main__":
    mcp.run(transport="stdio")