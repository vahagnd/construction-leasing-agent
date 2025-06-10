from parser.parser import parse_data_from_fedresurs
from agent.agent import agent_executor
import time
import random
import json

def main():
    # DEBUG
    count = 0

    starting_date = '2025-01-20'
    ending_date = '2025-02-01'
    dirty_data = parse_data_from_fedresurs(starting_date, ending_date)

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