from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils.timezone import now

from core.constants import ADMIN_PLATFORMS, Errors, MENU_UPDATES
from core.models import MenuButton, MenuUpdate, Question, Role, User

AdminUser = get_user_model()

BLOCKED_USER_ROLE_ID = -1
ADMIN_ROLE_ID = 0


class Button:
    def __init__(self, fields: dict):
        for key, value in fields.items():
            setattr(self, key, value)


def get_roles():
    return {role.id: role.name for role in Role.objects.all()}


def change_role(platform, platform_id, new_role_id):
    user = User.objects.get(platform=platform, platform_id=platform_id)
    user.role = Role.objects.get(pk=new_role_id)
    user.save()


def add_user(platform, platform_id, role_id):
    User.objects.create(
        platform=platform,
        platform_id=platform_id,
        role=Role.objects.get(pk=role_id),
    )


def get_users(platform):
    admin_field = ADMIN_PLATFORMS[platform]
    return {
        user.platform_id:
            user.role.id if not user.is_blocked else BLOCKED_USER_ROLE_ID
        for user in User.objects.filter(platform=platform).all()
    } | {
        getattr(admin, admin_field): ADMIN_ROLE_ID
        for admin in AdminUser.objects.filter(
            **{'{}__isnull'.format(admin_field): False}
        )
    }


def get_menus():
    return {
        menu.id: Button(dict(
            main_menu=False if menu.parent else True,
            children=[
                Button(button.get_data_for_bot())
                for button in menu.get_children()
            ],
        ))
        for menu in MenuButton.objects.all()
    }


def check_menu_updates(platform):
    return set(MenuUpdate.objects.filter(
        **{'{}__isnull'.format(MENU_UPDATES[platform]): True}
    ).values_list('id', flat=True))


def complete_menu_updates(platform, update_ids):
    MenuUpdate.objects.filter(id__in=update_ids).update(
        **{f'{MENU_UPDATES[platform]}': datetime.now()}
    )


def get_main_menu_links():
    return {role.id: role.menu.id for role in Role.objects.all()}


def get_subscribers(platform, role_id=None):
    if role_id is not None:
        return set(
            User.objects.filter(
                is_subscribed=True, platform=platform, role=role_id,
            ).values_list('platform_id', flat=True)
        )
    return set(
        User.objects.filter(
            is_subscribed=True, platform=platform,
        ).values_list('platform_id', flat=True)
    )


def subscribe(platform, platform_id):
    user = User.objects.get(platform=platform, platform_id=platform_id)
    if user.is_subscribed:
        raise ValueError(
            Errors.ALREADY_SUBSCRIBED.format(
                platform=platform, platform_id=platform_id,
            )
        )
    user.is_subscribed = True
    user.date_subscribed = now()
    user.save()


def unsubscribe(platform, platform_id):
    user = User.objects.get(platform=platform, platform_id=platform_id)
    if not user.is_subscribed:
        raise ValueError(
            Errors.NOT_SUBSCRIBED.format(
                platform=platform, platform_id=platform_id,
            )
        )
    user.is_subscribed = False
    user.date_subscribed = None
    user.save()


def get_blocked_users(platform):
    return set(
        User.objects.filter(
            is_blocked=True, platform=platform,
        ).values_list('platform_id', flat=True)
    )


def block(platform, platform_id):
    user = User.objects.get(platform=platform, platform_id=platform_id)
    if user.is_blocked:
        raise ValueError(
            Errors.ALREADY_BLOCKED.format(
                platform=platform, platform_id=platform_id,
            )
        )
    user.is_blocked = True
    user.questions.all().delete()
    user.save()


def add_question(platform, platform_id, question):
    user = User.objects.get(platform=platform, platform_id=platform_id)
    if not user.is_blocked:
        Question.objects.create(user=user, question=question)


def get_open_question():
    return Question.objects.filter(
        answered__isnull=True,
    ).values(
        'id', 'user__platform', 'user__platform_id', 'user__role', 'question',
    ).first()


def get_answered_questions(platform):
    return set(
        Question.objects.filter(
            user__platform=platform,
            answered__isnull=False,
            answer_sent=None,
        ).values_list('id', 'user__platform_id', 'answer')
    )


def answer_question(question_id, answer):
    question = Question.objects.get(id=question_id)
    question.answer = answer
    question.answered = now()
    question.save()


def confirm_answer_sent(question_ids):
    Question.objects.filter(id__in=question_ids).update(answer_sent=now())


class GenericBot:
    def __init__(self, platform):
        self.platform = platform
        self.roles = None
        self.users = None
        self.subscribers = None
        self.main_menu_links = None
        self.current_menus = None
        self.get_data()

    def get_data(self):
        self.roles = get_roles()
        self.users = get_users(self.platform)
        self.subscribers = {
            role: get_subscribers(self.platform, role) for role in self.roles
        }
        self.main_menu_links = get_main_menu_links()
        self.current_menus = {}
