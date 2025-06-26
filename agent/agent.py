from langchain.agents import initialize_agent, AgentType, tool, AgentExecutor
from langchain_together import Together
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os
import json

load_dotenv()  # Load TOGETHER_API_KEY

llama = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
exaone = "lgai/exaone-3-5-32b-instruct"
exaone_deep = "lgai/exaone-deep-32b"

# Initialize LLM
llm = Together(
    model=exaone,
    temperature=0.0,
    max_tokens=200
)

# ---- TOOL 1: Extract Info ----
@tool
def extract_information(contract_text: str) -> str:
    """Извлекает из неструктурированного текста лизингового договора
    название компании заключившего контракт, дата заключения контракта, название предмета лизинга.
    Собирает все это в одно предложение по формату 'Компания company_name заключила сделку лизинга на product_name contract_date(дата на русском)'."""
    prompt = PromptTemplate(
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
            "Не выводи *\n"
            # "Пример вывода:\n"
            # 'Название компании: ООО "СТРОЙМАГИСТРАЛЬ"\n'
            # "Дата заключения контракта: 2025-04-14\n"
            # "Название предмета лизнга: 0106008 Автомобили, SITRAK C7H MAX (LZZ7CMWDXRC643572)\n"
            "Текст: {contract_text}\n"
            "Ответ:"
        )
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.invoke({"contract_text": contract_text})
    return response["text"].strip()

# ---- TOOL 2: Classify Product ----
@tool
def classify_contract(contract_structured_text: str) -> str:
    """
    Получает структурированную информацию о контракте лизинга.
    Классифицирует описание предмета лизинга как строительную технику или нет с помощью LLM.
    Если предмет — строительная техника, возвращает текст как есть.
    Если нет — возвращает '400'.
    """
    prompt = PromptTemplate(
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

    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.invoke({"product_description": contract_structured_text})
    return response["text"].strip()

# ---- TOOL 3: Extract contract signing date from structure text about contract
@tool
def extract_contract_date(contract_structured_text: str) -> str:
    """
    Извлекает дату заключения контракта из структурированного текста лизинговой сделки.
    Возвращает дату в формате гггг-мм-дд. Не добавляет ничего лишнего.
    """
    prompt = PromptTemplate(
        input_variables=["contract_structured_text"],
        template=(
            "Ты аналитик, получивший строку с структурированным текстом лизингового контракта.\n"
            "Твоя задача — выделить только дату заключения контракта из строки.\n"
            "Текст контракта: {contract_structured_text}\n"
            "Ответь только одной строкой: дата в формате гггг-мм-дд, без лишнего текста, без слов 'дата', без кавычек, без точки, без '*'."
        )
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.invoke({"contract_structured_text": contract_structured_text})
    return result["text"].strip()

# ---- TOOL 4: Create or modify text document ----
@tool
def save_leasing_info(contract_info: str) -> str:
    """
    Сохраняет информацию о лизинговом контракте и дате в JSON.
    Принимает только одну строку. Вызывает LLM-функцию для извлечения даты.
    """
    # Call the tool directly (simulate how agent would call it)
    date = extract_contract_date.run(contract_info)

    file_path = "data/contracts.json"

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append({"text": contract_info, "date": date})

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return f"Контракт сохранен. Дата: {date}"


# ---- Build Agent ----
tools = [extract_information, classify_contract, extract_contract_date, save_leasing_info]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False
)

# Parsing error handling
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent.agent,
    tools=tools,
    verbose=False,
    handle_parsing_errors=True # Important
)


# ---- Example Usage ----
if __name__ == "__main__":
    input_text = (
        'Компания: ООО "СТРОЙМАГИСТРАЛЬ"\n'
        "Дата заключения контракта: 14.04.2025\n"
        "Информация о контракте:\n"
        "Предмет финансовой аренды: LZZ7CMWDXRC643572, 0106008 экскаваторы, SITRAK C7H MAX\n"
        "Срок финансовой аренды: 15.04.2025 - 15.03.2028\n"
        "Комментарий пользователя: <res>Заключение</res>"
    )

    input_text_construction = (
        'Компания: ООО "СТРОЙГРАНИТ"\n'
        "Дата заключения контракта: 22.05.2025\n"
        "Информация о контракте:\n"
        "Предмет финансовой аренды: Экскаватор-погрузчик JCB 3CX\n"
        "Срок финансовой аренды: 22.05.2025 - 22.05.2028\n"
        "Комментарий пользователя: <res>Подписан</res>"
    )

    query = (
        f"Вот неструктурированный текст лизингового контракта:\n{input_text_construction}\n\n"
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

    result = agent_executor.run(
        query
    )

    print("\n📋 FINAL RESULT:")
    print(result)