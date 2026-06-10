from aiogram.fsm.state import State, StatesGroup


class ReviewStates(StatesGroup):
    # Шаг 1 — поиск туалета
    waiting_address = State()
    waiting_toilet_confirm = State()  # юзер выбирает из найденных или создаёт новый

    # Шаг 2 — анкета (6 критериев по очереди)
    score_cleanliness = State()   # 0–25
    score_supplies = State()      # 0–20
    score_smell = State()         # 0–20
    score_equipment = State()     # 0–15
    score_privacy = State()       # 0–5
    score_vibe = State()          # 0–5

    # Шаг 3 — комментарий
    comment = State()

    # Шаг 4 — фото (до 3, необязательно)
    photos = State()
