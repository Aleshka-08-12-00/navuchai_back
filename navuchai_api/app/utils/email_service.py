import asyncio
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.config import EMAIL_CONFIG
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Сервис для отправки email писем"""

    def __init__(self):
        self.config = self._create_config()
        self.fastmail = FastMail(self.config)

    def _create_config(self) -> ConnectionConfig:
        """Создание конфигурации для FastMail"""
        return ConnectionConfig(
            MAIL_USERNAME=EMAIL_CONFIG["MAIL_USERNAME"] or "",
            MAIL_PASSWORD=EMAIL_CONFIG["MAIL_PASSWORD"] or "",
            MAIL_FROM=EMAIL_CONFIG["MAIL_FROM"],
            MAIL_PORT=EMAIL_CONFIG["MAIL_PORT"],
            MAIL_SERVER=EMAIL_CONFIG["MAIL_SERVER"],
            MAIL_STARTTLS=EMAIL_CONFIG["MAIL_STARTTLS"],
            MAIL_SSL_TLS=EMAIL_CONFIG["MAIL_SSL_TLS"],
            USE_CREDENTIALS=bool(EMAIL_CONFIG["MAIL_USERNAME"] and EMAIL_CONFIG["MAIL_PASSWORD"]),
            VALIDATE_CERTS=True,
            TEMPLATE_FOLDER=None
        )

    async def send_password_reset_email(self, email: str, new_password: str, user_name: str) -> bool:
        """
        Отправка email с новым паролем пользователю
        
        Args:
            email: Email адрес пользователя
            new_password: Новый сгенерированный пароль
            user_name: Имя пользователя
            
        Returns:
            bool: True если письмо отправлено успешно
        """
        try:
            subject = "Восстановление пароля - Навучай"

            # HTML шаблон письма
            html_content = self._get_password_reset_template(new_password, user_name)

            # Создание сообщения
            message = MessageSchema(
                subject=subject,
                recipients=[email],
                body=html_content,
                subtype="html"
            )

            # Отправка email
            await self.fastmail.send_message(message)
            logger.info(f"Email с новым паролем отправлен на {email}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при отправке email на {email}: {str(e)}")
            raise Exception(f"Не удалось отправить email: {str(e)}")

    async def send_test_email(self, email: str) -> bool:
        """
        Отправка тестового email для проверки настроек
        
        Args:
            email: Email адрес для отправки теста
            
        Returns:
            bool: True если письмо отправлено успешно
        """
        try:
            subject = "Тест настроек email - Навучай"

            # Простое текстовое сообщение
            text_content = """
            <html>
            <body>
                <h2>Тест настроек email</h2>
                <p>Это тестовое письмо для проверки настроек email в системе Навучай.</p>
                <p>Если вы получили это письмо, значит настройки email работают корректно.</p>
                <hr>
                <p><small>Отправлено автоматически из системы Навучай</small></p>
            </body>
            </html>
            """

            # Создание сообщения
            message = MessageSchema(
                subject=subject,
                recipients=[email],
                body=text_content,
                subtype="html"
            )

            # Отправка email
            await self.fastmail.send_message(message)
            logger.info(f"Тестовый email отправлен на {email}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при отправке тестового email на {email}: {str(e)}")
            raise Exception(f"Не удалось отправить тестовый email: {str(e)}")

    def _get_password_reset_template(self, new_password: str, user_name: str) -> str:
        """Генерация HTML шаблона для восстановления пароля"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Восстановление пароля</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }}
                .container {{
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                    color: white;
                    padding: 30px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 300;
                }}
                .content {{
                    padding: 30px 20px;
                }}
                .password-box {{
                    background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    text-align: center;
                    font-size: 20px;
                    font-weight: bold;
                    color: #2e7d32;
                    letter-spacing: 2px;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    border-radius: 4px;
                    padding: 15px;
                    margin: 25px 0;
                }}
                .warning strong {{
                    color: #856404;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #6c757d;
                    font-size: 12px;
                    border-top: 1px solid #dee2e6;
                }}
                .btn {{
                    display: inline-block;
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                .btn:hover {{
                    background-color: #45a049;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Восстановление пароля</h1>
                </div>
                <div class="content">
                    <p>Здравствуйте, <strong>{user_name}</strong>!</p>
                    
                    <p>Мы получили запрос на восстановление пароля для вашего аккаунта в системе <strong>Навучай</strong>.</p>
                    
                    <p>Ваш новый временный пароль:</p>
                    <div class="password-box">
                        {new_password}
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Важно:</strong> Рекомендуем сменить этот пароль после входа в систему в целях безопасности.
                    </div>
                    
                    <p>Если вы не запрашивали восстановление пароля, проигнорируйте это письмо и обратитесь в службу поддержки.</p>
                    
                    <p>С уважением,<br><strong>Команда Навучай</strong></p>
                </div>
                <div class="footer">
                    <p>Это автоматическое письмо, не отвечайте на него.</p>
                    <p>© 2025 Навучай. Все права защищены.</p>
                </div>
            </div>
        </body>
        </html>
        """


# Создаем глобальный экземпляр сервиса
email_service = EmailService()
