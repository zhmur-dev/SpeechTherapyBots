import time
from itertools import zip_longest

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext, MessageHandler, Updater
from telegram.ext.filters import Filters

from backend.settings import get_logger, settings
from core import core
from core.constants import (
    BUTTONS_PER_ROW, ButtonTypes, Errors, PLATFORMS_VERBOSE, Platforms,
    Pooling, SEND_MESSAGE_INTERVAL,
)
from core.localization import ButtonLabels, ChatMessages, MAIN_MENU

logger = get_logger(Platforms.TELEGRAM_FULL.lower())


class Menus:
    ADMIN_MAIN = 0
    REGISTRATION = -1
    ADMIN_ANSWER = -2
    ADMIN_CONFIRM_BLOCK = -3
    ASK_ADMIN = -4


class Commands:
    MAIN_MENU = -1
    ADMIN_ANSWER_QUESTION = -2
    ADMIN_CANCEL = -3
    BLOCK = -4
    CONFIRM_BLOCK = -5
    CANCEL_BLOCK = -6
    CANCEL = -7


STATIC_MENUS = {
    Menus.ASK_ADMIN: [[ButtonLabels.CANCEL]],
    Menus.ADMIN_MAIN: [[ButtonLabels.ANSWER]],
    Menus.ADMIN_ANSWER: [[ButtonLabels.CANCEL, ButtonLabels.BLOCK]],
    Menus.ADMIN_CONFIRM_BLOCK: [
        [ButtonLabels.CANCEL, ButtonLabels.CONFIRM_BLOCK],
    ],
}

STATIC_COMMANDS = {
    Menus.ASK_ADMIN: {ButtonLabels.CANCEL: Commands.CANCEL},
    Menus.ADMIN_MAIN: {ButtonLabels.ANSWER: Commands.ADMIN_ANSWER_QUESTION},
    Menus.ADMIN_ANSWER: {
        ButtonLabels.CANCEL: Commands.ADMIN_CANCEL,
        ButtonLabels.BLOCK: Commands.BLOCK,
    },
    Menus.ADMIN_CONFIRM_BLOCK: {
        ButtonLabels.CANCEL: Commands.CANCEL_BLOCK,
        ButtonLabels.CONFIRM_BLOCK: Commands.CONFIRM_BLOCK,
    },
}


class TelegramBot(core.GenericBot):
    def __init__(self, platform):
        super().__init__(platform)
        self.menus = {}
        self.commands = {}
        self.ask_admin_button_links = {}
        self.current_questions = {}
        self.main_menu_links[core.ADMIN_ROLE_ID] = Menus.ADMIN_MAIN
        self.build_menus()
        self.start()

    def build_menus(self):
        self.build_dynamic_menus()
        self.build_static_menus()

    def build_dynamic_menus(self):
        for menu_id, menu in core.get_menus().items():
            current_commands = {}
            current_menu = []
            current_row = []
            for button in menu.children:
                current_commands[button.name] = button
                current_row.append(button.name)
                if button.type == ButtonTypes.ASK_ADMIN:
                    self.ask_admin_button_links[menu_id] = button.name
                if len(current_row) == BUTTONS_PER_ROW:
                    current_menu.append(current_row)
                    current_row = []
            if not menu.main_menu:
                current_row.append(MAIN_MENU)
                current_commands[MAIN_MENU] = Commands.MAIN_MENU
            if current_row:
                current_menu.append(current_row)
            self.menus[menu_id] = self.get_keyboard(current_menu)
            self.commands[menu_id] = current_commands
        self.menus[Menus.REGISTRATION] = self.get_keyboard(
            [[role for role in row if role is not None]
             for row in zip_longest(
                *[iter(self.roles.values())] * BUTTONS_PER_ROW,
            )]
        )
        self.commands[Menus.REGISTRATION] = {
            value: key for key, value in self.roles.items()
        }
        self.build_static_menus()

    def build_static_menus(self):
        for menu_id, menu in STATIC_MENUS.items():
            self.menus[menu_id] = self.get_keyboard(menu)
        for menu_id, commands in STATIC_COMMANDS.items():
            self.commands[menu_id] = commands

    def check_menu_updates(self, context):
        update_ids = core.check_menu_updates(self.platform)
        if not update_ids:
            return
        self.get_data()
        self.build_dynamic_menus()
        core.complete_menu_updates(self.platform, update_ids)

    def update_user_roles(self, context):
        self.users = core.get_users(self.platform)

    def send_admin_answers(self, context):
        answered_questions = core.get_answered_questions(self.platform)
        if not answered_questions:
            return
        question_ids = set()
        for answered_question in answered_questions:
            question_id, user_id, answer = answered_question
            context.bot.send_message(
                user_id,
                ChatMessages.ANSWER.format(answer=answer),
            )
            question_ids.add(question_id)
            time.sleep(SEND_MESSAGE_INTERVAL)
        core.confirm_answer_sent(question_ids)

    @staticmethod
    def info_button(button, user_id, context):
        if not button.file:
            context.bot.send_message(user_id, button.answer)
            return
        with button.file.open('rb') as file:
            context.bot.send_document(
                user_id,
                document=file,
                caption=button.answer,
            )

    def move_to_menu(self, user_id, message, menu_id, context):
        context.bot.send_message(
            user_id,
            message,
            reply_markup=self.menus[menu_id],
        )
        self.current_menus[user_id] = menu_id

    @staticmethod
    def reminder_button(user_id, context):
        context.bot.send_message(user_id, ChatMessages.NOT_IMPLEMENTED)

    def ask_admin_button(self, button, user_id, context):
        self.move_to_menu(user_id, button.answer, Menus.ASK_ADMIN, context)

    def add_question(self, user_id, role_id, message, context):
        menu_id = self.main_menu_links[role_id]
        core.add_question(self.platform, user_id, message)
        context.bot.send_message(
            user_id,
            self.commands[menu_id][
                self.ask_admin_button_links[menu_id]
            ].received_answer,
        )
        self.main_menu(user_id, role_id, context)

    def subscribe_button(self, button, user_id, role_id, context):
        if user_id not in self.subscribers[role_id]:
            core.subscribe(self.platform, user_id)
            self.subscribers[role_id].add(user_id)
            context.bot.send_message(user_id, button.on_answer)
            return
        core.unsubscribe(self.platform, user_id)
        self.subscribers[role_id].remove(user_id)
        context.bot.send_message(user_id, button.off_answer)

    def main_menu(self, user_id, role_id, context):
        self.move_to_menu(
            user_id, MAIN_MENU, self.main_menu_links[role_id], context,
        )

    def register(self, user_id, message, context):
        try:
            role_id = self.commands[Menus.REGISTRATION][message]
            core.add_user(
                platform=self.platform,
                platform_id=user_id,
                role_id=role_id,
            )
            self.users[user_id] = role_id
            self.main_menu(user_id, role_id, context)
        except KeyError:
            context.bot.send_message(
                user_id,
                ChatMessages.REGISTRATION,
                reply_markup=self.menus[Menus.REGISTRATION],
            )

    def answer_question(self, admin_id, context):
        self.current_questions[admin_id] = core.get_open_question()
        question = self.current_questions[admin_id]
        if not question:
            context.bot.send_message(admin_id, ChatMessages.NO_QUESTIONS)
            self.main_menu(admin_id, core.ADMIN_ROLE_ID, context)
            return
        self.move_to_menu(
            admin_id,
            ChatMessages.QUESTION.format(
                question_id=question['id'],
                user_platform=PLATFORMS_VERBOSE[question['user__platform']],
                user_id=question['user__platform_id'],
                user_role=self.roles[question['user__role']],
                question=question['question'],
            ),
            Menus.ADMIN_ANSWER,
            context,
        )

    def admin_cancel(self, admin_id, context):
        if self.current_menus[admin_id] == Menus.ADMIN_CONFIRM_BLOCK:
            self.answer_question(admin_id, context)
        else:
            self.main_menu(admin_id, core.ADMIN_ROLE_ID, context)

    def admin_block(self, admin_id, context):
        question = self.current_questions[admin_id]
        self.move_to_menu(
            admin_id,
            ButtonLabels.CONFIRM_BLOCK_TEXT.format(
                platform=PLATFORMS_VERBOSE[question['user__platform']],
                id=question['user__platform_id'],
            ),
            Menus.ADMIN_CONFIRM_BLOCK,
            context,
        )

    def admin_confirm_block(self, admin_id, context):
        question = self.current_questions[admin_id]
        user_platform = question['user__platform']
        user_id = question['user__platform_id']
        core.block(user_platform, user_id)
        context.bot.send_message(
            admin_id,
            ChatMessages.BLOCK_USER.format(
                platform=PLATFORMS_VERBOSE[user_platform],
                id=user_id,
                role=self.roles[question['user__role']],
            ),
        )
        self.main_menu(admin_id, core.ADMIN_ROLE_ID, context)

    def admin_answer(self, admin_id, message, context):
        core.answer_question(self.current_questions[admin_id]['id'], message)
        context.bot.send_message(admin_id, ChatMessages.ANSWER_ACCEPTED)
        self.answer_question(admin_id, context)

    def answer(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        message = update.message.text
        if user_id not in self.users:
            self.register(user_id, message, context)
            return
        role_id = self.users[user_id]
        if role_id == core.BLOCKED_USER_ROLE_ID:
            return
        if user_id not in self.current_menus:
            self.main_menu(user_id, role_id, context)
            return
        try:
            command = self.commands[self.current_menus[user_id]][message]
            if isinstance(command, int):
                match command:
                    case Commands.MAIN_MENU | Commands.CANCEL:
                        self.main_menu(user_id, role_id, context)
                    case Commands.ADMIN_ANSWER_QUESTION:
                        self.answer_question(user_id, context)
                    case Commands.ADMIN_CANCEL | Commands.CANCEL_BLOCK:
                        self.admin_cancel(user_id, context)
                    case Commands.BLOCK:
                        self.admin_block(user_id, context)
                    case Commands.CONFIRM_BLOCK:
                        self.admin_confirm_block(user_id, context)
            else:
                match command.type:
                    case ButtonTypes.INFO:
                        self.info_button(command, user_id, context)
                    case ButtonTypes.MENU:
                        self.move_to_menu(
                            user_id, command.name, command.id, context,
                        )
                    case ButtonTypes.ASK_ADMIN:
                        self.ask_admin_button(command, user_id, context)
                    case ButtonTypes.SUBSCRIBE:
                        self.subscribe_button(
                            command, user_id, role_id, context,
                        )
                    case ButtonTypes.REMINDER:
                        self.reminder_button(user_id, context)
        except KeyError:
            match self.current_menus[user_id]:
                case Menus.ADMIN_ANSWER:
                    self.admin_answer(user_id, message, context)
                case Menus.ASK_ADMIN:
                    self.add_question(user_id, role_id, message, context)
                case _:
                    context.bot.send_message(
                        user_id,
                        ChatMessages.UNKNOWN_COMMAND,
                        reply_markup=self.menus[self.current_menus[user_id]],
                    )

    @staticmethod
    def error_handler(update, context):
        logger.exception(
            Errors.TELEGRAM.format(update=update, error=context.error)
        )

    @staticmethod
    def get_keyboard(keyboard):
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    def start(self):
        updater = Updater(token=settings.telegram_token)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(MessageHandler(Filters.text, self.answer))
        dispatcher.add_error_handler(self.error_handler)
        job_queue = updater.job_queue
        job_queue.run_repeating(self.check_menu_updates, Pooling.MENU_UPDATE)
        job_queue.run_repeating(self.update_user_roles, Pooling.USER_ROLES)
        job_queue.run_repeating(self.send_admin_answers, Pooling.ANSWERS)
        updater.start_polling()
        updater.idle()
