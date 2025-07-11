# Construction Leasing Agent — фильтрация лизинговых контрактов

---

## Описание проекта

Этот проект предназначен для автоматического сбора, фильтрации, структурирования и визуализации информации о лизинговых контрактах, опубликованных на [fedresurs.ru](https://fedresurs.ru).

---

### Функции проекта

- Сбор неструктурированной информации о лизинговых сделках
- Использование LLM-агента для извлечения ключевой информации и фильтрации контрактов связанных со строительным лизингом
- Сохранение результатов в ```.json``` файле
- Визуализация данных через интерактивный дашборд на Streamlit

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
└── .env (нужно создать вручную)
```

---

## Использованные технологии

- Python 3.13 — основной язык разработки  
- requests — для получения данных с сайта fedresurs.ru 
- LangChain — для построения LLM-агента и управления цепочками вызовов  
- Together AI — LLM API, на котором работает агент  
- Streamlit — для визуализации результатов в интерактивном дашборде
- JSON — формат хранения структурированных данных

---

## Установка и запуск

### Требования

- uv  
- ключ API Together

### Установка

Запустите

```bash
uv sync
```

#### Настройка API-ключа (для Together AI)

Создайте файл ```.env``` в корневой директории проекта

```bash
touch .env
```

Добавьте ваш API-ключ от Together в файл ```.env```

```bash
TOGETHER_API_KEY=ваш_ключ_здесь
```

### Запуск

Запустите Streamlit-приложение командой

```bash
streamlit run app.py
```

Затем откройте URL-адрес, указанный в вашем терминале (обычно это http://localhost:8501), в браузере.