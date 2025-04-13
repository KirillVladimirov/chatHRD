import os
from openai import OpenAI
from pydantic import BaseModel, Field

# --- Конфигурация --- 
# Используем OpenAI-совместимый API, который Ollama предоставляет из коробки
LOCAL_API_BASE = "http://localhost:11434/v1"
API_KEY = "ollama" # API ключ (может быть любым для Ollama)
MODEL_NAME = "hf.co/ruslandev/llama-3-8b-gpt-4o-ru1.0-gguf:Q8_0" # Модель из проекта

# --- Клиент OpenAI --- 
try:
    client = OpenAI(
        base_url=LOCAL_API_BASE,
        api_key=API_KEY,
    )
except Exception as e:
    print(f"Ошибка при инициализации клиента OpenAI: {e}")
    exit(1)

# --- Определение схемы структурированного вывода Pydantic --- 
class CalendarEvent(BaseModel):
    """Структура для извлечения информации о событии."""
    name: str = Field(description="Название или краткое описание события.")
    date: str = Field(description="Дата события (например, 'Пятница', '2024-09-15').")
    participants: list[str] = Field(description="Список имен участников.")

# --- Пример запроса со структурированным выводом --- 
def run_structured_query(prompt: str):
    """Отправляет запрос к LLM с требованием структурированного ответа.
       Выводит извлеченные данные.
    """
    try:
        print(f"\nОтправка запроса на структурированное извлечение из: '{prompt}'...")
        
        completion = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Ты ассистент, который извлекает информацию о событиях из текста и возвращает ее в формате JSON, соответствующем схеме CalendarEvent."},
                {"role": "user", "content": prompt},
            ],
            response_format=CalendarEvent,  # Указываем Pydantic модель для формата ответа
        )

        # Извлечение результата
        # Проверяем, успешно ли парсинг
        if completion.choices and completion.choices[0].message and completion.choices[0].message.parsed:
            event: CalendarEvent = completion.choices[0].message.parsed
            print("\nУспешно извлеченное событие:")
            print(f"  Название: {event.name}")
            print(f"  Дата: {event.date}")
            print(f"  Участники: {event.participants}")
        else:
            print("\nНе удалось извлечь структурированный ответ.")
            # Можно вывести сырой ответ для отладки, если он есть
            if completion.choices and completion.choices[0].message:
                 print(f"  Сырой ответ: {completion.choices[0].message.content}")

    except Exception as e:
        print(f"\nОшибка при выполнении структурированного запроса к API: {e}")
        # Дополнительная информация об ошибке, если доступна
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
             print(f"  Ответ сервера: {e.response.text}")

# --- Запуск эксперимента --- 
if __name__ == "__main__":
    test_prompt_1 = "Встреча проектной команды по проекту 'Альфа' назначена на понедельник, участвуют Иван, Мария и Петр."
    run_structured_query(test_prompt_1)
    
    test_prompt_2 = "Science fair on Friday, Alice and Bob are going."
    run_structured_query(test_prompt_2)
    
    # Пример, который может не соответствовать схеме
    test_prompt_3 = "Просто поговорить о погоде"
    run_structured_query(test_prompt_3) 