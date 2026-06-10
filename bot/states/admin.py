from aiogram.fsm.state import State, StatesGroup


class NicknameStates(StatesGroup):
    waiting_target_id = State()   # ввод telegram_id цели
    waiting_nickname = State()    # ввод прозвища


class DeleteReviewStates(StatesGroup):
    waiting_review_id = State()   # ввод ID отзыва
    waiting_reason = State()      # ввод причины


class BroadcastStates(StatesGroup):
    waiting_message = State()     # ввод текста для рассылки в канал
