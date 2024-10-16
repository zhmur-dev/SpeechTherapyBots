APP_NAME = 'Привет, Логопед!'
MAIN_MENU = 'Главное меню'


class Defaults:
    SUBSCRIBE = 'Подписаться'
    UNSUBSCRIBE = 'Отписаться'
    IS_SUBSCRIBER = 'Вы подписаны на рассылку.'
    IS_NOT_SUBSCRIBER = 'Вы не подписаны на рассылку.'


class VerboseNames:
    CREATED = 'время создания'

    class AdminUser:
        TELEGRAM_ID = 'Telegram ID'
        VK_ID = 'VK ID'
        ADMIN_USER = 'администратор'
        ADMIN_USERS = 'администраторы'
        ADMIN_PANEL_ACCESS = 'доступ в админ-панель'

    class Buttons:
        NAME = 'текст на кнопке'
        ORDER = 'расположение'
        ANSWER = 'ответ'
        INFO = 'информационная кнопка'
        INFO_PLURAL = 'информационные кнопки'
        SUB = 'подписка'
        REMINDER = 'напоминание'
        ASK_ADMIN = 'вопрос админу'
        MENU = 'меню'
        FILE = 'файл'
        ON_NAME = 'текст на кнопке при подписке'
        OFF_NAME = 'текст на кнопке при отписке'
        IS_SUBSCRIBER = 'сообщение если пользователь подписан'
        IS_NOT_SUBSCRIBER = 'сообщение если пользователь не подписан'
        REMINDER_TEXT = 'текст напоминания'
        RECEIVED_ANSWER = 'ответ при получении вопроса'

    class Question:
        USER = 'пользователь'
        QUESTION = 'вопрос'
        QUESTIONS = 'вопросы'
        ANSWER = 'ответ'
        CREATED = 'дата и время публикации'
        IS_CLOSED = 'вопрос закрыт?'
        CLOSED = 'дата и время ответа'
        CLOSED_QUESTION = 'закрытый вопрос'
        CLOSED_QUESTIONS = 'архив вопросов'
        QUESTION_STATS = 'статистика вопросов/ответов'
        ANSWER_SENT = 'ответ отправлен пользователю'

    class User:
        PLATFORM = 'платформа'
        PLATFORM_ID = 'ID'
        ROLE = 'роль'
        IS_SUBSCRIBED = 'подписан'
        DATE_SUBSCRIBED = 'дата подписки'
        SUBSCRIBER_STATS = 'статистика активных подписчиков'
        IS_BLOCKED = 'заблокировать'
        USER = 'пользователь'
        USERS = 'пользователи'

    class Role:
        NAME = 'название'
        MENU = 'меню'
        ROLE = 'роль'
        ROLES = 'роли'

    class MenuUpdate:
        MenuUpdate = 'обновление меню'
        MenuUpdates = 'обновления меню'


class AdminPanel:
    PARENT_LINKS = 'Родительское меню'
    MENU_PREVIEW = 'Превью меню'
    EMPTY_MENU = 'Пустое меню'
    UPDATE_MENUS = 'Обновить меню ботов'
    UPDATING = 'Обновляется...'
    QUESTION = 'Вопрос #{id} от {user}'


class ButtonLabels:
    START = 'Начать'
    ANSWER = 'Ответить на вопрос'
    CANCEL = 'Отмена'
    BLOCK = 'Заблокировать'
    CONFIRM_BLOCK = 'Подтвердить'
    CONFIRM_BLOCK_TEXT = (
        'Вы уверены, что хотите заблокировать пользователя {platform}#{id}? '
        'Все вопросы этого пользователя будут удалены,'
        'а бот перестанет отвечать на его запросы.'
    )


class ChatMessages:
    CHOOSE_BUTTON = 'Выберите запрос в меню'
    FILE_NOT_FOUND = 'Файл не найден'
    REGISTRATION = 'Добро пожаловать! Выберите свою роль'
    CHANGE_ROLE_COMMAND = 'Хочу сменить роль'
    NO_BUTTONS = 'Бот временно не работает'
    NO_QUESTIONS = 'Вопросы от пользователей отсутствуют'
    BLOCK_USER = 'Пользователь {platform}#{id} ({role}) заблокирован'
    ANSWER_ACCEPTED = 'Ответ принят. Следующий вопрос:'
    UNKNOWN_COMMAND = 'Неизвестная команда. Пожалуйста, пользуйтесь меню'
    QUESTION = (
        'Вопрос #{question_id} от {user_platform}#{user_id} '
        '({user_role}):\n\n{question}'
    )
    ANSWER = 'Ответ на Ваш вопрос администратору:\n\n{answer}'
    NOT_IMPLEMENTED = 'Функционал находится в разработке'
