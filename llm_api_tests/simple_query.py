import os
from openai import OpenAI

# --- Конфигурация --- 
# Укажите базовый URL вашего локального API
# Убедитесь, что он соответствует формату OpenAI API
LOCAL_API_BASE = "http://127.0.0.1:1337/v1"

# API ключ не обязателен для многих локальных серверов, но библиотека требует его.
# Можно использовать фиктивный ключ.
API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Модель, которую использует ваш локальный сервер (укажите правильное имя)
MODEL_NAME = "ggml-model-Q8_0.gguf" 

# --- Клиент OpenAI --- 
try:
    client = OpenAI(
        base_url=LOCAL_API_BASE,
        api_key=API_KEY,
    )
except Exception as e:
    print(f"Ошибка при инициализации клиента OpenAI: {e}")
    exit(1)

# --- Пример запроса --- 
def run_simple_query(prompt: str):
    """Отправляет простой запрос к LLM и выводит ответ."""
    try:
        print(f"\nОтправка запроса с промптом: '{prompt}'...")
        
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000, # Ограничение длины ответа
            temperature=0.7, # Параметр креативности ответа
        )
        
        response_content = completion.choices[0].message.content
        print("\nОтвет от LLM:")
        print(response_content)
        
    except Exception as e:
        print(f"Ошибка при выполнении запроса к API: {e}")

# --- Запуск эксперимента --- 
if __name__ == "__main__":
    test_prompt = "Расскажи коротко о Python."
    run_simple_query(test_prompt)
    
    # Вы можете добавить другие промпты или более сложную логику экспериментов здесь
    test_prompt_2 = "Как работает HTTP?"
    run_simple_query(test_prompt_2) 