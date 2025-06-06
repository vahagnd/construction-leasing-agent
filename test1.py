from langchain.agents import initialize_agent, AgentType, tool
# from langchain_core.tools import tool
from langchain_together import Together
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os

load_dotenv()  # Load TOGETHER_API_KEY

# Initialize LLM
llm = Together(
    model="lgai/exaone-3-5-32b-instruct",
    temperature=1,
    max_tokens=200
)

# ---- TOOL 1: Extract Info ----
@tool
def extract_information(contract_text: str) -> str:
    """Извлекает из неструктурированного текста лизингового договора название предмета лизинга."""
    prompt = PromptTemplate(
        input_variables=["contract_text"],
        template=(
            "Ты — профессиональный аналитик договоров лизинга. "
            "Проанализируй следующий текст лизингового контракта и выводи предмет лизинга.\n"
            # "Выводи СТРОГО по формату:\n"
            # "Предмет лизинга: название предмета\n"
            "НЕ ПРИДУМЫВАЙ ИНФОРМЦИЮ, все есть в тексте.\n"
            "НЕ ВЫВОДИ больше ничего.\n"
            "НЕ выводи 'Предмет лизинга'\n"
            "Текст: {contract_text}\n"
            "Ответ:"
        )
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.invoke({"contract_text": contract_text})
    return response["text"].strip()


# ---- TOOL 2: Classify Product ----
@tool
def classify_contract(product_name: str) -> str:
    """Классифицирует предмет лизинга как строительная техника/не строительная техника."""
    prompt = PromptTemplate(
        input_variables=["product_name"],
        template=(
            "Ты эксперт по строительной технике.\n"
            "Исходя из информации о предмете лизинга:\n"
            "{product_name}\n"
            "Выясни является ли {product_name} строительной техникой.\n"
            "Ответь строго ДА или НЕТ.\n"
            "Одно слово, НИЧЕГО БОЛЬШЕ!\n"
            "ДА или НЕТ."
        )
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.invoke({"product_name": product_name})
    return response["text"].strip()


# ---- Build Agent ----
tools = [extract_information, classify_contract]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# ---- Example Usage ----
if __name__ == "__main__":
    input_text = (
        "Предмет финансовой аренды: XTC651155S1529342, 0106008 Автомобили, КАМАЗ T2530\nСрок финансовой аренды: 04.04.2025 - 04.03.2028\nКомментарий пользователя: <res>Заключение</res>"
    )

    product_name = extract_information(input_text)

    result = agent.run(
        input_text
    )

    print("\n📋 FINAL RESULT:")
    print(f"Лизинг на {product_name}. Строительный лизинг: {result}")
