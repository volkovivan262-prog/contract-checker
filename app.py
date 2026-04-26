import streamlit as st
import PyPDF2
import requests
import os
from dotenv import load_dotenv

# --- Загрузка секретов из файла .env ---
# Эта команда найдёт ваш файл .env в той же папке и загрузит из него переменные
load_dotenv()

# --- Получение ключей из переменных окружения ---
FOLDER_ID = os.getenv("FOLDER_ID")
API_KEY = os.getenv("API_KEY")

# --- Функция для извлечения текста из PDF ---
def extract_text_from_pdf(file):
    """Открывает PDF и возвращает весь текст из него."""
    try:
        reader = PyPDF2.PdfReader(file)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        # Возвращаем текст, убрав лишние переносы строк и пробелы
        return ' '.join(full_text.split())
    except Exception as e:
        return f"Ошибка при чтении PDF: {str(e)}"

# --- Функция для отправки запроса к YandexGPT ---
def ask_yandexgpt(prompt_text: str) -> str:
    """Отправляет запрос к YandexGPT и возвращает ответ."""
    # URL для API YandexGPT
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    # Заголовки запроса, содержат наш API-ключ для авторизации
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_KEY}"
    }
    
    # Данные для отправки: указываем модель, настройки и сам текст запроса
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": 2000
        },
        "messages": [{"role": "user", "text": prompt_text}]
    }
    
    try:
        # Отправляем POST-запрос к API
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # Проверяем, не вернул ли сервер ошибку
        result = response.json()
        # Извлекаем текст ответа из полученного JSON
        return result["result"]["alternatives"][0]["message"]["text"]
    except Exception as e:
        return f"Произошла ошибка при обращении к YandexGPT: {e}"

# --- Интерфейс приложения (Streamlit) ---
st.set_page_config(page_title="Сравнение договоров", layout="centered")
st.title("📄 Сравнение договора и технического проекта")
st.markdown("Загрузите два PDF-файла, и программа найдёт для вас все ключевые расхождения.")

# Создаём две колонки для загрузки файлов
col1, col2 = st.columns(2)

with col1:
    contract_file = st.file_uploader("1️⃣ Загрузите договор (PDF)", type="pdf")
with col2:
    project_file = st.file_uploader("2️⃣ Загрузите эталонный проект (PDF)", type="pdf")

# Если оба файла загружены, показываем кнопку для запуска анализа
if contract_file and project_file:
    if st.button("🔍 Сравнить документы", type="primary"):
        # 1. Извлечение текста
        with st.spinner("📖 Извлекаем текст из PDF-файлов..."):
            contract_text = extract_text_from_pdf(contract_file)
            project_text = extract_text_from_pdf(project_file)
        
        # 2. Отправка запроса к YandexGPT
        st.info("🧠 Анализирую документы с помощью нейросети. Это может занять до 30 секунд...")
        
        prompt = f"""
        Внимательно проанализируй и сравни два документа.

        **Первый документ: Договор (Спецификация от заказчика)**
        ---
        {contract_text[:10000]}
        ---

        **Второй документ: Эталонный технический проект (Требования разработчика)**
        ---
        {project_text[:10000]}
        ---

        Задание: Найди все расхождения и противоречия между этими документами.
        Обрати особое внимание на:
        - Список и марки оборудования.
        - Характеристики и материалы трубопроводов.
        - Параметры металлоконструкций.
        - Технические условия, давления, температуры.

        Оформи ответ в виде структурированного списка. Для каждого найденного расхождения укажи:
        1.  **Пункт/объект:** (Например, "Оборудование: Насос")
        2.  **Несоответствие:** (Что указано в договоре vs что указано в проекте)
        3.  **Критичность:** (Высокая / Средняя / Низкая)
        4.  **Рекомендация:** (Краткий совет, как согласовать разногласие)
        """
        
        report = ask_yandexgpt(prompt)
        
        # 3. Вывод результата
        st.subheader("📊 Результаты анализа")
        st.success("Анализ завершён!")
        st.markdown(report)
        
        # Добавляем кнопку для скачивания отчёта
        st.download_button(
            label="📥 Скачать отчёт в виде файла",
            data=report,
            file_name="report.txt",
            mime="text/plain",
        )
else:
    st.info("⏳ Пожалуйста, загрузите оба PDF-файла, чтобы начать сравнение.")