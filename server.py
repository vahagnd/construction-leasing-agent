import sys
import os
import json
from dotenv import load_dotenv
from langchain_together import Together
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

load_dotenv()

llm = Together(
    model="lgai/exaone-3-5-32b-instruct",
    temperature=0.0,
    max_tokens=200,
)

DATA_PATH = "data/contracts.json"

# === PROMPTS ===
extract_info_prompt = PromptTemplate(
    input_variables=["contract_text"],
    template=(
        "Ты — профессиональный аналитик договоров лизинга. "
        "Проанализируй следующий текст лизингового контракта и выведи "
        "название компании заключившего контракт, дату заключения контракта, предмет лизинга.\n"
        "Выводи СТРОГО по формату:\n"
        "Комания <комания> заключила сделку лизинга на <предмет лизинга> <дата заключения контракта на русском>.\n"
        "Выводи только одно предложение.\n"
        "НЕ ПРИДУМЫВАЙ ИНФОРМЦИЮ, все есть в тексте.\n"
        "Не выводи *\n"
        "НЕ ВЫВОДИ больше ничего.\n"
        "Текст: {contract_text}\n"
        "Ответ:"
    )
)

classify_prompt = PromptTemplate(
    input_variables=["product_description"],
    template=(
        "Ты эксперт по строительной технике.\n"
        "По описанию предмета лизинга определи, является ли он строительной техникой.\n"
        "Если это строительная техника, выведи текст как есть.\n"
        "Если это НЕ строительная техника, выводи '400'.\n"
        "Не добавляй пояснений, не используй символы '*', не выводи больше одного предложения.\n"
        "Описание: {product_description}\n"
        "Ответ:"
    )
)

extract_date_prompt = PromptTemplate(
    input_variables=["contract_structured_text"],
    template=(
        "Ты аналитик, получивший строку с структурированным текстом лизингового контракта.\n"
        "Твоя задача — выделить только дату заключения контракта из строки.\n"
        "Текст контракта: {contract_structured_text}\n"
        "Ответь только одной строкой: дата в формате гггг-мм-дд, без лишнего текста, без слов 'дата', без кавычек, без точки, без '*'."
    )
)

# === TOOL DEFINITIONS ===
TOOLS = [
    {
        "type": "tool",
        "name": "extract_information",
        "description": """Извлекает из неструктурированного текста лизингового договора
    название компании заключившего контракт, дата заключения контракта, название предмета лизинга.
    Собирает все это в одно предложение по формату 'Компания company_name заключила сделку лизинга на product_name contract_date(дата на русском)'.""",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_text": {"type": "string"}
            },
            "required": ["contract_text"]
        }
    },
    {
        "type": "tool",
        "name": "classify_contract",
        "description": """
    Получает структурированную информацию о контракте лизинга.
    Классифицирует описание предмета лизинга как строительную технику или нет с помощью LLM.
    Если предмет — строительная техника, возвращает текст как есть.
    Если нет — возвращает '400'.
    """,
        "parameters": {
            "type": "object",
            "properties": {
                "product_description": {"type": "string"}
            },
            "required": ["product_description"]
        }
    },
    {
        "type": "tool",
        "name": "extract_contract_date",
        "description": """
    Извлекает дату заключения контракта из структурированного текста лизинговой сделки.
    Возвращает дату в формате гггг-мм-дд. Не добавляет ничего лишнего.
    """,
        "parameters": {
            "type": "object",
            "properties": {
                "contract_structured_text": {"type": "string"}
            },
            "required": ["contract_structured_text"]
        }
    },
    {
        "type": "tool",
        "name": "save_leasing_info",
        "description": """
    Сохраняет информацию о лизинговом контракте и дате в JSON.
    Принимает только одну строку. Вызывает LLM-функцию для извлечения даты.
    """,
        "parameters": {
            "type": "object",
            "properties": {
                "contract_info": {"type": "string"}
            },
            "required": ["contract_info"]
        }
    }
]

# === TOOL HANDLERS ===
def extract_information(contract_text):
    chain = LLMChain(llm=llm, prompt=extract_info_prompt)
    response = chain.invoke({"contract_text": contract_text})
    return response["text"].strip()

def classify_contract(product_description):
    chain = LLMChain(llm=llm, prompt=classify_prompt)
    response = chain.invoke({"product_description": product_description})
    return response["text"].strip()

def extract_contract_date(contract_structured_text):
    chain = LLMChain(llm=llm, prompt=extract_date_prompt)
    response = chain.invoke({"contract_structured_text": contract_structured_text})
    return response["text"].strip()

def save_leasing_info(contract_info):
    os.makedirs("data", exist_ok=True)
    date = extract_contract_date(contract_info)

    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append({"text": contract_info, "date": date})

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return f"Контракт сохранен. Дата: {date}"

TOOL_HANDLERS = {
    "extract_information": extract_information,
    "classify_contract": classify_contract,
    "extract_contract_date": extract_contract_date,
    "save_leasing_info": save_leasing_info,
}

# === MCP LOOP ===
def main():
    for line in sys.stdin:
        req = json.loads(line)
        if req["type"] == "list_tools":
            print(json.dumps({"type": "tool_list", "tools": TOOLS}))
        elif req["type"] == "call_tool":
            try:
                tool_name = req["tool_name"]
                args = req["args"]
                result = TOOL_HANDLERS[tool_name](**args)
                print(json.dumps({"type": "tool_result", "output": result}))
            except Exception as e:
                print(json.dumps({"type": "tool_result", "output": f"ERROR: {str(e)}"}))
        sys.stdout.flush()

if __name__ == "__main__":
    main()
