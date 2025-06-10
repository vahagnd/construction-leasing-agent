import streamlit as st
from parser.parser import parse_data_from_fedresurs
from agent.agent import agent_executor
import time
import json
import pandas as pd

def load_data(data_file):
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def visualize_data(data):
    df = pd.DataFrame(data)

    df = df.rename(columns={
        "text": "Информация о контракте",
        "date": "Дата заключения контракта"
    })

    if df.empty:
        st.info("Нет данных для отображения")
    else:
        st.dataframe(df)


DATA_FILE = "data/contracts.json"

st.set_page_config(page_title="Лизинговые контракты", layout="wide")
st.title("Извлечение данных из лизинговых контрактов")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Начальная дата", value=None)
with col2:
    end_date = st.date_input("Конечная дата", value=None)

run_button = st.button("Запустить обработку")

if run_button and start_date and end_date:
    st.info("Собираем и обрабатываем данные, это может занять несколько минут...")

    # Clear previous results
    with open("data/contracts.json", "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

    dirty_data = parse_data_from_fedresurs(str(start_date), str(end_date))

    results = []
    progress_bar = st.progress(0)

    for idx, dirty_text in enumerate(dirty_data):
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

        result = agent_executor.run(system_prompt)
        results.append(result)

        progress_bar.progress((idx + 1) / len(dirty_data))
        time.sleep(1)

    st.success("Обработка завершена ✅")

    st.subheader("Результаты:")

    data = load_data(DATA_FILE)
    visualize_data(data)

    # Optional: Downloadable JSON
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = f.read()

    st.download_button("📥 Скачать JSON", data, file_name="contracts.json", mime="application/json")
