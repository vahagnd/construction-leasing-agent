import sys
import os
import json
import asyncio
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
        "Компания <компания> заключила сделку лизинга на <предмет лизинга> <дата заключения контракта на русском>.\n"
        "Выводи только одно предложение.\n"
        "НЕ ПРИДУМЫВАЙ ИНФОРМАЦИЮ, все есть в тексте.\n"
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

PROMPTS = {
    "extract_info_prompt" : extract_info_prompt,
    "extract_date_prompt" : extract_date_prompt,
    "classify_prompt" : classify_prompt,
}

# === TOOLS ===
TOOLS = {
    "extract_information": {
        "description": "Извлекает из неструктурированного текста лизингового договора информацию о компании, дате и предмете лизинга",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_text": {"type": "string"}
            },
            "required": ["contract_text"]
        }
    },
    "classify_contract": {
        "description": "Классифицирует предмет лизинга как строительную технику или нет",
        "parameters": {
            "type": "object",
            "properties": {
                "product_description": {"type": "string"}
            },
            "required": ["product_description"]
        }
    },
    "extract_contract_date": {
        "description": "Извлекает дату заключения контракта в формате YYYY-MM-DD",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_structured_text": {"type": "string"}
            },
            "required": ["contract_structured_text"]
        }
    },
    "save_leasing_info": {
        "description": "Сохраняет информацию о лизинговом контракте в JSON файл",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_info": {"type": "string"}
            },
            "required": ["contract_info"]
        }
    }
}

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

# === SERVER ===
def handle_message(message):
    try:
        data = json.loads(message)
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "1.0.0",
                    "capabilities": {
                        "tools": True
                    }
                }
            }

        elif method == "tools/list":
            tools_list = []
            for name, tool in TOOLS.items():
                tools_list.append({
                    "name": name,
                    "description": tool["description"],
                    "inputSchema": tool["parameters"]
                })
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools_list}
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name in TOOL_HANDLERS:
                result = TOOL_HANDLERS[tool_name](**arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": result}]
                    }
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}
                }

        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32603, "message": str(e)}
        }

def main():
    for line in sys.stdin:
        line = line.strip()
        if line:
            response = handle_message(line)
            print(json.dumps(response, ensure_ascii=False))
            sys.stdout.flush()

if __name__ == "__main__":
    main()