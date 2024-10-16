class Platforms:
    TELEGRAM = 'tg'
    TELEGRAM_FULL = 'Telegram'
    VK = 'vk'
    VK_FULL = 'VK'


class ButtonTypes:
    INFO = 'InfoButton'
    ASK_ADMIN = 'AskAdminButton'
    SUBSCRIBE = 'SubButton'
    MENU = 'MenuButton'
    REMINDER = 'ReminderButton'


class Pooling:
    MENU_UPDATE = 15 * 60
    USER_ROLES = 5 * 60
    ANSWERS = 5 * 60


PLATFORMS = (
    (Platforms.TELEGRAM, Platforms.TELEGRAM_FULL),
    (Platforms.VK, Platforms.VK_FULL),
)
PLATFORMS_VERBOSE = {
    Platforms.TELEGRAM: Platforms.TELEGRAM_FULL,
    Platforms.VK: Platforms.VK_FULL,
}
ADMIN_PLATFORMS = {
    Platforms.TELEGRAM: 'telegram_id',
    Platforms.VK: 'vk_id',
}
MENU_UPDATES = {
    Platforms.TELEGRAM: 'telegram',
    Platforms.VK: 'vk',
}
BUTTON_MAX_LENGTH = 22
BUTTONS_PER_ROW = 2
SEND_MESSAGE_INTERVAL = 1


class Errors:
    ALREADY_SUBSCRIBED = 'User {platform}#{platform_id} is already subscribed'
    NOT_SUBSCRIBED = 'User {platform}#{platform_id} is not subscribed'
    ALREADY_BLOCKED = 'User {platform}#{platform_id} is already blocked'
    CANNOT_UPLOAD_FILE = 'Cannot upload file {file}: {error}'
    MENU_NO_BUTTONS = 'Menu for role {role} has no buttons'
    SUBSCRIBE = 'Unexpected error while subscribing: {error}'
    UNSUBSCRIBE = 'Unexpected error while unsubscribing: {error}'
    RUNTIME = 'Unexpected error led to bot crash: {error_type}: {error}'
    TELEGRAM = 'Update {update} caused an error {error}'
