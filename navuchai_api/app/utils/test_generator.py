import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.auth import APIKeyAuth


def generate_test_questions(source_text: str) -> List[Dict[str, Any]]:
    """
    Генерирует тестовые вопросы на основе предоставленного текста.
    
    Args:
        source_text (str): Исходный текст для генерации вопросов
        
    Returns:
        List[Dict[str, Any]]: Список тестовых вопросов в формате JSON
        
    Raises:
        Exception: При ошибке в работе с Yandex Cloud ML API
    """
    try:
        # Загружаем переменные из .env
        load_dotenv()
        
        # Инициализируем SDK
        sdk = YCloudML(
            folder_id=os.getenv("YC_FOLDER_ID"),
            auth=APIKeyAuth(os.getenv("YC_API_KEY")),
        )
        
        # Настраиваем модель
        model = sdk.models.completions("yandexgpt-lite", model_version="rc")
        model = model.configure(temperature=0.3)
        
        # Формируем промпт для генерации вопросов
        prompt = f"""
        Создай минимум 5 тестовых вопросов по тексту ниже, содержать минимум 3-5 вариантов ответов. Каждый вопрос должен быть в формате JSON как в примере:

        {{
          "text": "<p>Вопрос в HTML</p>",
          "text_abstract": "копия поля text но без HTML тегов",
          "type_id": 1,
          "reviewable": false,
          "answers": {{
            "correctAnswer": ["<p>Правильный ответ</p>"],
            "allAnswer": [
              "<p>Правильный ответ</p>",
              "<p>Неверный 1</p>",
              "<p>Неверный 2</p>"
            ],
            "settings": {{
              "correctScore": 1,
              "incorrectScore": 0,
              "showMaxScore": true,
              "requireAnswer": false,
              "stopIfIncorrect": false
            }}
          }}
        }}

        Вот текст: {source_text}
        
        Верни только JSON массив с вопросами, без дополнительного текста.
        """
        
        # Выполняем запрос к модели
        result = model.run(
            [
                {"role": "system", "text": "Ты преподаватель, создатель тестов. Твоя задача - создавать качественные тестовые вопросы на основе предоставленного текста."},
                {"role": "user", "text": prompt},
            ]
        )
        
        # Получаем ответ от модели
        response_text = result[0].text.strip()
        
        # Пытаемся найти JSON в ответе (на случай если модель добавила дополнительный текст)
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        
        if start_idx != -1 and end_idx != 0:
            json_text = response_text[start_idx:end_idx]
        else:
            json_text = response_text
        
        # Парсим JSON
        questions = json.loads(json_text)
        
        # Валидируем структуру вопросов
        validated_questions = []
        for question in questions:
            if isinstance(question, dict) and 'text' in question and 'answers' in question:
                # Убеждаемся, что все необходимые поля присутствуют
                validated_question = {
                    'text': question.get('text', ''),
                    'text_abstract': question.get('text_abstract', ''),
                    'type_id': question.get('type_id', 1),
                    'reviewable': question.get('reviewable', False),
                    'answers': {
                        'correctAnswer': question.get('answers', {}).get('correctAnswer', []),
                        'allAnswer': question.get('answers', {}).get('allAnswer', []),
                        'settings': {
                            'correctScore': question.get('answers', {}).get('settings', {}).get('correctScore', 1),
                            'incorrectScore': question.get('answers', {}).get('settings', {}).get('incorrectScore', 0),
                            'showMaxScore': question.get('answers', {}).get('settings', {}).get('showMaxScore', True),
                            'requireAnswer': question.get('answers', {}).get('settings', {}).get('requireAnswer', False),
                            'stopIfIncorrect': question.get('answers', {}).get('settings', {}).get('stopIfIncorrect', False)
                        }
                    }
                }
                validated_questions.append(validated_question)
        
        return validated_questions
        
    except json.JSONDecodeError as e:
        raise Exception(f"Ошибка парсинга JSON ответа от модели: {e}")
    except Exception as e:
        raise Exception(f"Ошибка при генерации тестовых вопросов: {e}")


def generate_test_questions_sync(source_text: str) -> List[Dict[str, Any]]:
    """
    Синхронная версия генерации тестовых вопросов.
    Используется как альтернатива асинхронной версии.
    
    Args:
        source_text (str): Исходный текст для генерации вопросов
        
    Returns:
        List[Dict[str, Any]]: Список тестовых вопросов в формате JSON
    """
    return generate_test_questions(source_text) 