import json
from pathlib import Path
from datetime import datetime, timezone

DATA_FILE = Path(__file__).with_name("conversations.json")

_data = {}


def load_data():
    """Загружает данные из conversations.json."""
    global _data

    if not DATA_FILE.exists():
        _data = {}
        save_data()
        return _data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            _data = json.load(file)
    except (json.JSONDecodeError, OSError):
        _data = {}

    return _data


def save_data():
    """Сохраняет данные в conversations.json."""
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(_data, file, ensure_ascii=False, indent=4)


def get_user(user_id):
    """Получает пользователя или создаёт новую запись."""
    user_id = str(user_id)

    if user_id not in _data:
        _data[user_id] = {
            "conversation_id": None,
            "messages": []
        }
        save_data()

    return _data[user_id]


def add_message(user_id, role, content, conversation_id=None):
    """Сохраняет сообщение пользователя или бота."""
    user = get_user(user_id)

    if conversation_id is not None:
        user["conversation_id"] = conversation_id

    user["messages"].append({
        "role": role,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    user["messages"] = user["messages"][-50:]

    save_data()


def get_conversation_id(user_id):
    """Возвращает ID текущего диалога Dify."""
    return get_user(user_id)["conversation_id"]


def reset_conversation(user_id):
    """Начинает новый диалог, сохраняя историю сообщений."""
    user = get_user(user_id)
    user["conversation_id"] = None
    save_data()


def get_history(user_id, limit=6):
    """Возвращает последние сообщения пользователя."""
    return get_user(user_id)["messages"][-limit:]


def get_message_count(user_id):
    """Возвращает количество сохранённых сообщений."""
    return len(get_user(user_id)["messages"])