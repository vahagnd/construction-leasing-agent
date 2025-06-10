# Construction Leasing Agent — фильтрация лизинговых контрактов

---

## Описание проекта

Этот проект предназначен для автоматического сбора, фильтрации, структурирования и визуализации информации о лизинговых контрактах, опубликованных на [fedresurs.ru](https://fedresurs.ru).

---

### Функции проекта:

- Сбор неструктурированной информации о лизинговых сделках;
- Использование LLM-агента для извлечения ключевой информации и фильтрации контрактов связанных со строительным лизингом;
- Сохранение результатов в ```.json``` файле;
- Визуализация данных через интерактивный дашборд на Streamlit.

---

## Структура проекта

```
construction-leasing-agent/
│
├── agent/
│   └── agent.py
│
├── parser/
│   └── parser.py
│
├── data/
│   └── contracts.json
│
├── app.py
├── requirements.txt
├── .env (нужно создать вручную)
└── README.md
```

---

## Использованные технологии

- Python 3.12 — основной язык разработки  
- requests — для получения данных с сайта fedresurs.ru 
- LangChain — для построения LLM-агента и управления цепочками вызовов  
- Together AI — LLM API, на котором работает агент  
- Streamlit — для визуализации результатов в интерактивном дашборде
- JSON — формат хранения структурированных данных

---

## Установка и запуск

1. Клонировать репозиторий:

```bash
git clone https://github.com/vahagnd/construction-leasing-agent.git
cd construction-leasing-agent
```

2. (Опционально) Создать виртуальное окружение:

```bash
python3 -m venv .venv
source .venv/bin/activate  # для Linux/macOS
.venv\Scripts\activate     # для Windows
```

3. Установить зависимости:

```bash
pip install -r requirements.txt
```

---

## Настройка API-ключа (для Together AI)

1. Создайте файл ```.env``` в корневой директории проекта:

```bash
touch .env
```

2. Добавьте ваш API-ключ от Together в файл ```.env```:

```bash
TOGETHER_API_KEY=ваш_ключ_здесь
```

---

## Запуск приложения

Запустите Streamlit-приложение командой:

```bash
streamlit run app.py
```

Затем откройте URL-адрес, указанный в вашем терминале (обычно это http://localhost:8501), в браузере.