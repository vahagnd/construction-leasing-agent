import requests
import time
import random
import json

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
    print(f"Contracts found: {contracts_found}")
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
        time.sleep(random.uniform(1, 4))

    return list(set(data))

# Example Usage
if __name__ == "__main__":
    print(parse_data_from_fedresurs(start_date='2025-01-20', end_date='2025-02-01'))
