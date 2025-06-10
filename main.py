import streamlit as st
import json
from datetime import datetime
from agent.agent import agent_executor
from parser.parser import parse_data_from_fedresurs

DATA_FILE = "data/contracts.json"

def run_agent_and_save(start_date: str, end_date: str):

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

    dirty_data = parse_data_from_fedresurs(start_date, end_date)

    for dirty_text in dirty_data:
        system_prompt = (
            f"Вот неструктурированный текст лизингового контракта:\n{dirty_text}\n\n"
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
        _ = agent_executor.run(system_prompt)

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def visualize_data(data):
    st.subheader("Обработанные лизинговые контракты")

    if not data:
        st.info("Данные отсутствуют. Запустите анализ.")

    for entry in data:
        st.json(entry["text"])

def main():
    st.title("Дашборд анализа лизинговых контрактов")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Дата начала", value=datetime(2025, 1, 1))
    with col2:
        end_date = st.date_input("Дата окончания", value=datetime(2025, 2, 1))

    if st.button("Запустить анализ"):
        st.info("Запуск анализа... Пожалуйста, подождите.")
        run_agent_and_save(str(start_date), str(end_date))
        st.success("Анализ завершён! Данные сохранены.")

    data = load_data()
    visualize_data(data)

    # Optional: Downloadable JSON
    with open("data/contracts.json", "r", encoding="utf-8") as f:
        data = f.read()

    st.download_button("📥 Скачать JSON", data, file_name="contracts.json", mime="application/json")

if __name__ == "__main__":
    main()
