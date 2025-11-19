document.addEventListener("DOMContentLoaded", () => {
    let username = null;
    let ws = null;

    const loginContainer = document.getElementById("login-container");
    const chatContainer = document.getElementById("chat-container");
    const usernameInput = document.getElementById("username-input");
    const loginButton = document.getElementById("login-button");

    const chatWindow = document.getElementById("chat-window");
    const messageInput = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");

    // Входим в чат по клику на кнопку "Войти"
    loginButton.addEventListener("click", () => {
        username = usernameInput.value.trim();
        if (username !== "") {
            // Скрываем форму логина и показываем чат
            loginContainer.style.display = "none";
            chatContainer.style.display = "flex";
            initializeWebSocket();
        }
    });

    // Инициализация WebSocket-подключения
    function initializeWebSocket() {
        ws = new WebSocket("ws://localhost:8765");

        ws.onopen = () => {
            console.log("Подключение к серверу установлено");
        };

        ws.onmessage = (event) => {
            const data = event.data;
            
            try {
                // Пытаемся разобрать JSON (для истории сообщений)
                const parsedData = JSON.parse(data);
                
                if (parsedData.type === "history") {
                    // Загружаем историю сообщений
                    console.log(`Получено ${parsedData.messages.length} сообщений из истории`);
                    parsedData.messages.forEach(message => {
                        appendMessage(message, true);
                    });
                }
            } catch (e) {
                // Если не JSON, то обычное текстовое сообщение
                appendMessage(data, false);
            }
        };

        ws.onclose = () => {
            console.log("Соединение с сервером закрыто");
            // Показываем сообщение о разрыве соединения
            appendMessage("Соединение с сервером потеряно. Переподключитесь...", false);
        };

        ws.onerror = (error) => {
            console.error("Ошибка WebSocket:", error);
            appendMessage("Ошибка соединения с сервером", false);
        };
    }

    // Отправка сообщения по кнопке "Отправить"
    sendButton.addEventListener("click", sendMessage);

    // Отправка по Enter
    messageInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    });

    // Формируем сообщение с именем пользователя и отправляем
    function sendMessage() {
        const text = messageInput.value.trim();
        if (text !== "" && ws && ws.readyState === WebSocket.OPEN) {
            const fullMessage = `${username}: ${text}`;
            ws.send(fullMessage);
            messageInput.value = "";
        }
    }

    // Добавляем новое сообщение в окно чата и прокручиваем вниз
    function appendMessage(message, isHistory = false) {
        const messageElem = document.createElement("div");
        
        // Добавляем специальный класс для сообщений из истории
        if (isHistory) {
            messageElem.className = "history-message";
        } else {
            // Определяем, наше ли это сообщение
            if (message.startsWith(username + ": ")) {
                messageElem.className = "my-message";
            } else if (message.includes(": ")) {
                messageElem.className = "other-message";
            } else {
                // Системные сообщения (ошибки, уведомления)
                messageElem.className = "info-message";
            }
        }
        
        messageElem.textContent = message;
        chatWindow.appendChild(messageElem);

        // Прокручиваем окно к последнему сообщению (только для новых сообщений)
        if (!isHistory) {
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    }
}); // <-- Добавлена эта закрывающая скобка и круглая скобка