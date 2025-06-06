from fedresurs import parse_data_from_fedresurs
from agent import agent_executor
import time
import random
import json

STRUCTURED_DATA_FILE = "structured_data.json"

def find_text_by_date(json_path, target_date):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)  # data is a list of dicts

    for record in data:
        if record.get('date') == target_date:
            return record.get('text')
    return None  # if not found

def main():
    # DEBUG
    count = 0

    starting_date = '2025-01-20'
    ending_date = '2025-02-01'
    dirty_data = parse_data_from_fedresurs(starting_date, ending_date)

    for dirty_text in dirty_data:
        if dirty_text[:7] == "CHECKED":
            print("Already checked:", find_text_by_date(STRUCTURED_DATA_FILE, dirty_text[8:]))
        else:
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

            result = agent_executor.run(
                system_prompt
            )

            print(result)

            time.sleep(random.uniform(2, 6))

        # DEBUG
        print(count)
        count += 1

if __name__ == "__main__":
    main()