import asyncio
import websockets
import logging
import json
from datetime import datetime
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Множество для хранения активных WebSocket-подключений
connected_clients = set()

# Файл для хранения истории чата
CHAT_HISTORY_FILE = "chat_history.txt"
# Количество сообщений для отправки новым пользователям
MAX_HISTORY_MESSAGES = 10

class ChatHistory:
    def __init__(self, filename=CHAT_HISTORY_FILE, max_history=MAX_HISTORY_MESSAGES):
        self.filename = filename
        self.max_history = max_history
        self.messages = []
        self.load_history()
    
    def load_history(self):
        """Загружает историю сообщений из файла"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Загружаем последние MAX_HISTORY_MESSAGES сообщений
                    for line in lines[-self.max_history:]:
                        line = line.strip()
                        if line:
                            self.messages.append(line)
                logger.info(f"Загружено {len(self.messages)} сообщений из истории")
            else:
                logger.info("Файл истории не найден, будет создан новый")
        except Exception as e:
            logger.error(f"Ошибка при загрузке истории: {e}")
    
    def save_message(self, message):
        """Сохраняет сообщение в историю"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            
            # Добавляем в память
            self.messages.append(formatted_message)
            
            # Сохраняем в файл
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(formatted_message + '\n')
            
            # Поддерживаем максимальное количество сообщений в памяти
            if len(self.messages) > self.max_history:
                self.messages = self.messages[-self.max_history:]
                
            return formatted_message
        except Exception as e:
            logger.error(f"Ошибка при сохранении сообщения: {e}")
            return message
    
    def get_recent_messages(self, count=None):
        """Возвращает последние сообщения"""
        if count is None:
            count = self.max_history
        return self.messages[-count:]

# Создаем экземпляр для управления историей чата
chat_history = ChatHistory()

async def handle_connection(websocket):
    """
    Обработчик нового подключения.
    Регистрирует клиента, принимает входящие сообщения и транслирует их всем подключенным клиентам.
    """
    connected_clients.add(websocket)
    logger.info(f"Новое подключение: {websocket.remote_address}")
    
    try:
        # Отправляем историю чата новому пользователю
        recent_messages = chat_history.get_recent_messages()
        if recent_messages:
            history_message = json.dumps({
                "type": "history",
                "messages": recent_messages
            })
            await websocket.send(history_message)
            logger.info(f"Отправлено {len(recent_messages)} сообщений из истории клиенту {websocket.remote_address}")
        
        # Обрабатываем входящие сообщения
        async for message in websocket:
            logger.info(f"Получено сообщение: {message} от {websocket.remote_address}")
            
            # Сохраняем сообщение в историю
            saved_message = chat_history.save_message(message)
            
            # Транслируем сохраненное сообщение (с временной меткой) всем клиентам
            await broadcast(saved_message)
            
    except websockets.exceptions.ConnectionClosed as e:
        logger.warning(f"Соединение с клиентом {websocket.remote_address} закрыто: {e}")
    except Exception as e:
        logger.error(f"Ошибка при обработке соединения: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Клиент {websocket.remote_address} отключился")

async def broadcast(message):
    """
    Транслирует полученное сообщение всем подключенным клиентам.
    """
    if connected_clients:
        try:
            # Отправляем сообщение всем клиентам
            await asyncio.gather(
                *(client.send(message) for client in connected_clients),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"Ошибка при broadcast: {e}")

async def main():
    # Запуск WebSocket-сервера на localhost:8765
    server = await websockets.serve(handle_connection, "localhost", 8765)
    logger.info("WebSocket сервер запущен на ws://localhost:8765")
    logger.info(f"История чата сохраняется в файл: {CHAT_HISTORY_FILE}")
    logger.info(f"Новым пользователям отправляются последние {MAX_HISTORY_MESSAGES} сообщений")
    
    try:
        await server.wait_closed()
    except KeyboardInterrupt:
        logger.info("Сервер остановлен")

if __name__ == "__main__":
    asyncio.run(main())


# pip install websockets
# Запуск сервера: python .\serve\main.py &
# Запуск клиента: cd client/ && python -m http.server 8000 &