import os

from django.core.exceptions import ObjectDoesNotExist
from schedule import every, run_pending
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.exceptions import ApiError
from vk_api.keyboard import VkKeyboard
from vk_api.upload import VkUpload
from vk_api.utils import get_random_id

from backend.settings import BASE_DIR, get_logger, settings
from core import core
from core.constants import (
    BUTTONS_PER_ROW, ButtonTypes, Errors, PLATFORMS_VERBOSE, Platforms,
    Pooling,
)
from core.localization import ButtonLabels, ChatMessages, MAIN_MENU

logger = get_logger(Platforms.VK_FULL.lower())


class MenuTypes:
    ADMIN = 0
    REGISTRATION = -1
    ASK_ADMIN = -2
    ADMIN_ANSWER_QUESTIONS = -3
    ADMIN_BLOCK_USER = -4


class Callbacks:
    DELIMITER = '#'
    MAIN_MENU = 'main_menu'
    REGISTER = 'role'
    SUBSCRIBE = 'sub'
    UNSUBSCRIBE = 'unsub'
    GET_QUESTION = 'questions'
    BLOCK_USER = 'block'
    CONFIRM_BLOCK = 'confirm_block'


class VKBot(core.GenericBot):
    def __init__(self, platform):
        super().__init__(platform)
        self.menus = {}
        self.ask_admin_answers = {}
        self.subscription_submenus = {}
        self.current_questions = {}
        self.vk = VkApi(token=settings.vk_token)
        self.create_static_menus()
        self.callbacks = self.create_dynamic_menus()
        self.main_menu_links[core.ADMIN_ROLE_ID] = MenuTypes.ADMIN
        self.main_menu_links[
            core.BLOCKED_USER_ROLE_ID
        ] = VkKeyboard.get_empty_keyboard()
        self.schedule_updates()
        self.vk_bot()

    def send_message(self, user_id, message, keyboard=None, attachment=None):
        self.vk.method(
            'messages.send',
            {
                'user_id': user_id,
                'random_id': get_random_id(),
                'message': message,
                'keyboard': keyboard,
                'attachment': attachment,
            },
        )

    def send_message_event_answer(self, event):
        self.vk.method(
            'messages.sendMessageEventAnswer',
            {
                'user_id': event.object.user_id,
                'event_id': event.object.event_id,
                'peer_id': event.object.peer_id,
                'event_data': event.object.event_data,
            },
        )

    @staticmethod
    def create_standard_button(
        keyboard, name=ButtonLabels.CANCEL, callback=Callbacks.MAIN_MENU,
    ):
        keyboard.add_callback_button(
            name,
            payload={
                'callback_data': (
                    f'{callback}{Callbacks.DELIMITER}'
                )
            },
        )

    def create_subscription_submenus(self, button, menu_id):
        names = (button.on_name, button.off_name)
        callbacks = (Callbacks.SUBSCRIBE, Callbacks.UNSUBSCRIBE)
        for (name, callback) in zip(names, callbacks):
            keyboard = VkKeyboard()
            keyboard.add_callback_button(
                name,
                payload={
                    'callback_data': (
                        f'{callback}{Callbacks.DELIMITER}{button.id}'
                    )
                },
            )
            keyboard.add_line()
            self.create_standard_button(keyboard)
            self.subscription_submenus[menu_id] = keyboard.get_keyboard()
            menu_id = -menu_id

    def create_static_menus(self):
        keyboard = VkKeyboard()
        self.create_standard_button(keyboard)
        self.menus[MenuTypes.ASK_ADMIN] = keyboard.get_keyboard()
        keyboard = VkKeyboard()
        self.create_standard_button(
            keyboard,
            ButtonLabels.ANSWER,
            Callbacks.GET_QUESTION,
        )
        self.menus[MenuTypes.ADMIN] = keyboard.get_keyboard()
        keyboard = VkKeyboard()
        self.create_standard_button(
            keyboard,
            ButtonLabels.BLOCK,
            Callbacks.BLOCK_USER,
        )
        self.create_standard_button(keyboard)
        self.menus[MenuTypes.ADMIN_ANSWER_QUESTIONS] = keyboard.get_keyboard()
        keyboard = VkKeyboard()
        self.create_standard_button(
            keyboard,
            ButtonLabels.CONFIRM_BLOCK,
            Callbacks.CONFIRM_BLOCK,
        )
        self.create_standard_button(keyboard)
        self.menus[MenuTypes.ADMIN_BLOCK_USER] = keyboard.get_keyboard()

    def create_dynamic_menus(self):
        callbacks = {}
        for menu_id, menu in core.get_menus().items():
            keyboard = VkKeyboard()
            buttons_in_line = 0
            for button in menu.children:
                if buttons_in_line >= BUTTONS_PER_ROW:
                    keyboard.add_line()
                    buttons_in_line = 0
                callback_data = (
                    f'{button.type}{Callbacks.DELIMITER}{button.id}'
                )
                callbacks[callback_data] = button
                name = button.name
                keyboard.add_callback_button(
                    name, payload={'callback_data': callback_data},
                )
                buttons_in_line += 1
                match button.type:
                    case ButtonTypes.SUBSCRIBE:
                        self.create_subscription_submenus(button, menu_id)
                    case ButtonTypes.ASK_ADMIN:
                        self.ask_admin_answers[menu_id] = button.id
            if not menu.main_menu:
                if buttons_in_line >= BUTTONS_PER_ROW:
                    keyboard.add_line()
                self.create_standard_button(keyboard, MAIN_MENU)
            self.menus[menu_id] = keyboard.get_keyboard()
        keyboard = VkKeyboard(one_time=True)
        for role_id, role in self.roles.items():
            keyboard.add_callback_button(
                role,
                payload={
                    'callback_data': (
                        f'{Callbacks.REGISTER}{Callbacks.DELIMITER}{role_id}'
                    )
                },
            )
        self.menus[MenuTypes.REGISTRATION] = keyboard.get_keyboard()
        return callbacks

    def check_menu_updates(self):
        update_ids = core.check_menu_updates(self.platform)
        if update_ids:
            self.get_data()
            self.callbacks = self.create_dynamic_menus()
            core.complete_menu_updates(self.platform, update_ids)

    def update_user_roles(self):
        self.users = core.get_users(self.platform)

    def schedule_updates(self):
        every(Pooling.MENU_UPDATE).seconds.do(self.check_menu_updates)
        every(Pooling.USER_ROLES).seconds.do(self.update_user_roles)

    def get_menu(
        self,
        user_id,
        menu_id,
        message=ChatMessages.CHOOSE_BUTTON,
        subscription=False
    ):
        if subscription:
            menu = self.subscription_submenus[menu_id]
        else:
            menu = self.menus[menu_id]
        try:
            self.send_message(user_id, message, menu)
        except ApiError:
            logger.error(
                Errors.MENU_NO_BUTTONS.format(role=self.users[user_id])
            )
            self.send_message(user_id, ChatMessages.NO_BUTTONS)
        self.current_menus[user_id] = menu_id

    def get_current_menu(self, user_id):
        if user_id not in self.current_menus:
            try:
                self.current_menus[
                    user_id
                ] = self.main_menu_links[self.users[user_id]]
            except KeyError:
                self.get_menu(
                    user_id,
                    MenuTypes.REGISTRATION,
                    ChatMessages.REGISTRATION,
                )

    def answer_info_button(self, user_id, peer_id, button):
        file = button.file.name
        if file:
            try:
                upload = VkUpload(self.vk).document_message(
                    os.path.join(BASE_DIR, file),
                    file.split('.')[0].split('/')[1:],
                    peer_id=peer_id,
                )
                self.send_message(
                    user_id,
                    button.answer,
                    attachment=(
                        f'doc{upload["doc"]["owner_id"]}_'
                        f'{upload["doc"]["id"]}'
                    ),
                )
            except (ApiError, ObjectDoesNotExist) as error:
                logger.error(
                    Errors.CANNOT_UPLOAD_FILE.format(file=file, error=error)
                )
                self.send_message(user_id, button.answer)
        else:
            self.send_message(user_id, button.answer)

    def answer_remainder_button(self, user_id):
        self.send_message(user_id, ChatMessages.NOT_IMPLEMENTED)

    def answer_subscribe_button(self, user_id, button_id):
        button = self.callbacks[
            f'{ButtonTypes.SUBSCRIBE}{Callbacks.DELIMITER}{button_id}'
        ]
        role_id = self.users[user_id]
        try:
            core.subscribe(self.platform, user_id)
        except ValueError as error:
            logger.error(Errors.SUBSCRIBE.format(error=error))
        self.subscribers[role_id].add(user_id)
        self.get_menu(user_id, self.main_menu_links[role_id], button.on_answer)

    def answer_unsubscribe_button(self, user_id, button_id):
        button = self.callbacks[
            f'{ButtonTypes.SUBSCRIBE}{Callbacks.DELIMITER}{button_id}'
        ]
        role_id = self.users[user_id]
        try:
            core.unsubscribe(self.platform, user_id)
        except ValueError as error:
            logger.error(Errors.UNSUBSCRIBE.format(error=error))
        self.subscribers[role_id].remove(user_id)
        self.get_menu(
            user_id, self.main_menu_links[role_id], button.off_answer,
        )

    def answer_role_menu(self, user_id, role_id):
        if user_id in self.users:
            old_role = self.users[user_id]
            core.change_role(self.platform, user_id, role_id)
            if user_id in self.subscribers[old_role]:
                self.subscribers[old_role].remove(user_id)
                self.subscribers[role_id].add(user_id)
        else:
            core.add_user(self.platform, user_id, role_id)
        self.users[user_id] = role_id
        self.get_menu(
            user_id,
            self.main_menu_links[role_id],
            ChatMessages.REGISTRATION,
        )

    def answer_get_question(self, admin_id):
        self.current_questions[admin_id] = core.get_open_question()
        question = self.current_questions[admin_id]
        if not question:
            self.get_menu(admin_id, MenuTypes.ADMIN, ChatMessages.NO_QUESTIONS)
            return
        self.get_menu(
            admin_id,
            MenuTypes.ADMIN_ANSWER_QUESTIONS,
            ChatMessages.QUESTION.format(
                question_id=question['id'],
                user_platform=PLATFORMS_VERBOSE[question['user__platform']],
                user_id=question['user__platform_id'],
                user_role=self.roles[question['user__role']],
                question=question['question'],
            ),
        )

    def admin_block(self, admin_id):
        question = self.current_questions[admin_id]
        self.get_menu(
            admin_id,
            MenuTypes.ADMIN_BLOCK_USER,
            ButtonLabels.CONFIRM_BLOCK_TEXT.format(
                platform=PLATFORMS_VERBOSE[question['user__platform']],
                id=question['user__platform_id'],
            ),
        )

    def answer_confirm_block(self, admin_id):
        question = self.current_questions[admin_id]
        blocked_user_platform = question['user__platform']
        blocked_user_id = question['user__platform_id']
        core.block(blocked_user_platform, blocked_user_id)
        self.get_menu(
            admin_id,
            MenuTypes.ADMIN,
            ChatMessages.BLOCK_USER.format(
                platform=PLATFORMS_VERBOSE[blocked_user_platform],
                id=blocked_user_id,
                role=self.roles[question['user__role']],
            ),
        )

    def answer_ask_admin(self, user_id, message, menu_id):
        core.add_question(self.platform, user_id, message)
        self.get_menu(
            user_id,
            menu_id,
            self.callbacks[
                f'{ButtonTypes.ASK_ADMIN}{Callbacks.DELIMITER}'
                f'{self.ask_admin_answers[menu_id]}'
            ].received_answer,
        )

    def admin_answer_questions(self, admin_id, message):
        core.answer_question(self.current_questions[admin_id]['id'], message)
        self.send_message(admin_id, ChatMessages.ANSWER_ACCEPTED)
        self.answer_get_question(admin_id)

    def answer_message(self, user_id, message):
        if (
            user_id in self.users and
            message != ChatMessages.CHANGE_ROLE_COMMAND
        ):
            if self.users[user_id] == core.BLOCKED_USER_ROLE_ID:
                return
            self.get_current_menu(user_id)
            menu_id = self.main_menu_links[self.users[user_id]]
            match self.current_menus[user_id]:
                case MenuTypes.ASK_ADMIN:
                    self.answer_ask_admin(user_id, message, menu_id)
                case MenuTypes.ADMIN_ANSWER_QUESTIONS:
                    self.admin_answer_questions(user_id, message)
                case _:
                    self.get_menu(user_id, menu_id)
        else:
            self.get_menu(
                user_id,
                MenuTypes.REGISTRATION,
                ChatMessages.REGISTRATION,
            )

    def answer_button(self, event, user_id, callback_data):
        role_id = self.users.get(user_id)
        if role_id == core.BLOCKED_USER_ROLE_ID:
            self.get_menu(user_id, self.main_menu_links(role_id))
            return
        button_type, button_id = callback_data.split(Callbacks.DELIMITER)
        match button_type:
            case ButtonTypes.INFO:
                self.answer_info_button(
                    user_id,
                    event.object.peer_id,
                    self.callbacks[callback_data],
                )
            case ButtonTypes.REMINDER:
                self.answer_remainder_button(user_id)
            case ButtonTypes.SUBSCRIBE:
                self.get_current_menu(user_id)
                if user_id in self.subscribers[role_id]:
                    menu_id = -self.current_menus[user_id]
                    answer = self.callbacks[callback_data].on_answer
                else:
                    menu_id = self.current_menus[user_id]
                    answer = self.callbacks[callback_data].off_answer
                self.get_menu(user_id, menu_id, answer, subscription=True)
            case ButtonTypes.ASK_ADMIN:
                self.get_menu(
                    user_id,
                    MenuTypes.ASK_ADMIN,
                    self.callbacks[callback_data].answer,
                )
            case ButtonTypes.MENU:
                self.get_menu(user_id, int(button_id))
            case Callbacks.SUBSCRIBE:
                self.answer_subscribe_button(user_id, button_id)
            case Callbacks.UNSUBSCRIBE:
                self.answer_unsubscribe_button(user_id, button_id)
            case Callbacks.REGISTER:
                self.answer_role_menu(user_id, int(button_id))
            case Callbacks.GET_QUESTION:
                self.answer_get_question(user_id)
            case Callbacks.BLOCK_USER:
                self.admin_block(user_id)
            case Callbacks.CONFIRM_BLOCK:
                self.answer_confirm_block(user_id)
            case Callbacks.MAIN_MENU:
                self.get_menu(user_id, self.main_menu_links[role_id])
            case _:
                self.send_message(user_id, ChatMessages.CHOOSE_BUTTON)
        self.send_message_event_answer(event)

    def vk_bot(self):
        try:
            for event in VkBotLongPoll(
                self.vk, group_id=settings.vk_group_id,
            ).listen():
                run_pending()
                if event.type == VkBotEventType.MESSAGE_NEW:
                    self.answer_message(
                        event.message.from_id,
                        event.message.text,
                    )
                if event.type == VkBotEventType.MESSAGE_EVENT:
                    self.answer_button(
                        event,
                        event.object.user_id,
                        event.object.payload['callback_data'],
                    )
        except Exception as error:
            logger.error(Errors.RUNTIME.format(
                    error_type=type(error).__name__,
                    error=error,
            ))
