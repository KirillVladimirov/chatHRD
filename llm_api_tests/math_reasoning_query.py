import os
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List

# --- Конфигурация --- 
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

# --- Определение схем структурированного вывода Pydantic --- 
class Step(BaseModel):
    """Один шаг в математическом решении."""
    explanation: str = Field(description="Текстовое объяснение шага.")
    output: str = Field(description="Математическое выражение или результат этого шага.")

class MathReasoning(BaseModel):
    """Полное пошаговое решение математической задачи."""
    steps: List[Step] = Field(description="Список шагов решения.")
    final_answer: str = Field(description="Окончательный ответ на задачу.")

# --- Пример запроса для решения математической задачи --- 
def run_math_reasoning_query(problem: str):
    """Отправляет запрос к LLM для пошагового решения математической задачи.
       Выводит структурированный результат.
    """
    try:
        print(f"\nОтправка запроса на решение задачи: '{problem}'...")
        
        completion = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system", 
                    "content": f"Реши следующую математическую задачу шаг за шагом. Предоставь свое решение в формате JSON, соответствующем схеме MathReasoning. Каждый шаг должен содержать текстовое объяснение и математический результат этого шага. В конце укажи финальный ответ."
                },
                {"role": "user", "content": problem},
            ],
            response_format=MathReasoning,  # Указываем Pydantic модель для формата ответа
            temperature=0.1 # Низкая температура для более детерминированного математического вывода
        )

        # Извлечение результата
        if completion.choices and completion.choices[0].message and completion.choices[0].message.parsed:
            reasoning: MathReasoning = completion.choices[0].message.parsed
            print("\nУспешно полученное пошаговое решение:")
            for i, step in enumerate(reasoning.steps):
                print(f"  Шаг {i+1}:")
                print(f"    Объяснение: {step.explanation}")
                print(f"    Вывод: {step.output}")
            print(f"\n  Финальный ответ: {reasoning.final_answer}")
        else:
            print("\nНе удалось извлечь структурированный ответ.")
            if completion.choices and completion.choices[0].message:
                 print(f"  Сырой ответ: {completion.choices[0].message.content}")

    except Exception as e:
        print(f"\nОшибка при выполнении запроса на решение задачи к API: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
             print(f"  Ответ сервера: {e.response.text}")

# --- Запуск эксперимента --- 
if __name__ == "__main__":
    math_problem = "Реши уравнение: 8x + 7 = -23"
    run_math_reasoning_query(math_problem)
    
    math_problem_2 = "Вычисли: (5 + 3) * 2 - 10 / 5"
    run_math_reasoning_query(math_problem_2) 