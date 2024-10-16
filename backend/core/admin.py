from itertools import zip_longest

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.db.models import BigIntegerField
from django.forms import TextInput
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django_object_actions import DjangoObjectActions, action
from import_export.admin import ExportActionModelAdmin
from prettytable import PrettyTable

from core.constants import BUTTONS_PER_ROW
from core.localization import AdminPanel, MAIN_MENU, VerboseNames
from core.models import (
    AskAdminButton, InfoButton, MenuButton, MenuUpdate, Question,
    ReminderButton, Role, SubButton, User,
)

admin.site.unregister(Group)

AdminUser = get_user_model()


def get_link(link, text):
    return mark_safe('<a href="{}">{}</a>'.format(link, text))


def get_menu_link(menu_id, text):
    return get_link(
        link=reverse('admin:core_menubutton_change', args=[menu_id]),
        text=text,
    )


def menu_preview(buttons, submenu):
    if not buttons and not submenu:
        return AdminPanel.EMPTY_MENU
    table = PrettyTable(header=False, padding_width=0)
    table.add_rows(zip_longest(
        *[iter(buttons)] * BUTTONS_PER_ROW,
        fillvalue='',
    ))
    if submenu:
        if len(buttons) % BUTTONS_PER_ROW == 0:
            table.add_row([MAIN_MENU] + [''] * (BUTTONS_PER_ROW - 1))
        else:
            table.rows[-1][-1] = MAIN_MENU
    return mark_safe(table.get_html_string(format=True))


class MenuInline(admin.TabularInline):
    model = MenuButton
    ordering = ('order',)
    extra = 0
    show_change_link = True


class InfoInline(admin.StackedInline):
    model = InfoButton
    ordering = ('order',)
    extra = 0


class UniqueInline(admin.StackedInline):
    extra = 0
    max_num = 1


class SubInline(UniqueInline):
    model = SubButton


class ReminderInline(UniqueInline):
    model = ReminderButton


class AskAdminInline(UniqueInline):
    model = AskAdminButton


class ModelAdminWithButton(admin.ModelAdmin):
    @action(label=AdminPanel.UPDATE_MENUS)
    def update_menus(self, request, obj):
        MenuUpdate.objects.create()
        return HttpResponseRedirect(
            reverse('admin:core_menuupdate_changelist')
        )


@admin.register(Role)
class RoleAdmin(DjangoObjectActions, ModelAdminWithButton):
    list_display = ('name', 'get_menu')
    exclude = ('menu',)
    changelist_actions = ('update_menus',)

    @admin.display(description=MAIN_MENU)
    def get_menu(self, role):
        return get_menu_link(role.menu_id, role.menu.name)

    def save_model(self, request, role, form, change):
        if role.menu is None:
            MenuButton.objects.create(name=role.name, role=role)
        return super().save_model(request, role, form, change)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'platform', 'platform_id', 'role', 'is_subscribed', 'is_blocked',
    )
    list_editable = ('is_blocked',)
    list_display_links = None
    list_filter = ('platform', 'role', 'is_subscribed', 'is_blocked')

    def save_model(self, request, user, form, change):
        if user.is_blocked:
            user.questions.all().delete()
        super().save_model(request, user, form, change)

    def has_add_permission(self, request):
        return False


class SubscriberStats(User):

    class Meta:
        proxy = True
        verbose_name = VerboseNames.User.SUBSCRIBER_STATS
        verbose_name_plural = VerboseNames.User.SUBSCRIBER_STATS


@admin.register(SubscriberStats)
class SubscriberStatsAdmin(ExportActionModelAdmin):
    date_hierarchy = 'date_subscribed'
    list_display = ('id', 'platform', 'platform_id', 'role', 'date_subscribed')
    list_filter = ('platform', 'role')
    readonly_fields = list_display

    def get_queryset(self, request):
        return (
            super(SubscriberStatsAdmin, self)
            .get_queryset(request)
            .filter(is_subscribed=True)
        )

    def get_actions(self, request):
        return None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AdminUser)
class AdminUserAdmin(DjangoUserAdmin):
    formfield_overrides = {BigIntegerField: {'widget': TextInput()}}
    list_display = ('username', 'email', 'is_staff', 'telegram_id', 'vk_id')
    list_editable = ('is_staff', 'telegram_id', 'vk_id')
    list_filter = ('is_staff',)
    search_fields = ('username', 'email')


@admin.register(MenuButton)
class MenuAdmin(DjangoObjectActions, ModelAdminWithButton):
    list_display = ('name', 'get_parent_links', 'get_buttons')
    exclude = ('parent', 'order')
    ordering = ('parent',)
    save_on_top = True
    changelist_actions = ('update_menus',)

    @admin.display(description=AdminPanel.PARENT_LINKS)
    def get_parent_links(self, menu: MenuButton):
        if menu.parent is None:
            return MAIN_MENU
        return get_menu_link(menu.parent.id, menu.parent.name)

    @admin.display(description=AdminPanel.MENU_PREVIEW)
    def get_buttons(self, menu: MenuButton):
        return menu_preview(
            buttons=[button.name for button in menu.get_children()],
            submenu=False if menu.parent is None else True,
        )

    def get_inlines(self, request, menu):
        inlines = [MenuInline, InfoInline]
        if menu is None or menu.parent is None:
            inlines.extend((SubInline, ReminderInline, AskAdminInline))
        return inlines

    def has_add_permission(self, request):
        return False


@admin.register(MenuUpdate)
class MenuUpdateAdmin(DjangoObjectActions, ModelAdminWithButton):
    list_display = ('id', 'created', 'telegram', 'vk')
    list_display_links = None
    changelist_actions = ('update_menus',)
    empty_value_display = AdminPanel.UPDATING

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'answer', 'created')
    list_editable = ('answer',)
    readonly_fields = (
        'id', 'user', 'question', 'created', 'answered', 'answer_sent',
    )
    list_display_links = None

    def get_queryset(self, request):
        return (
            super(QuestionAdmin, self)
            .get_queryset(request)
            .filter(answered__isnull=True)
        )

    def save_model(self, request, question, form, change):
        question.answered = now()
        super().save_model(request, question, form, change)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ClosedQuestion(Question):

    class Meta:
        proxy = True
        verbose_name = VerboseNames.Question.CLOSED_QUESTION
        verbose_name_plural = VerboseNames.Question.CLOSED_QUESTIONS
        ordering = ('answered',)


@admin.register(ClosedQuestion)
class ClosedQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'get_user_role', 'question', 'answer', 'created',
        'answered',
    )
    list_filter = ('user__platform', 'user__role')
    readonly_fields = (
        'id', 'user', 'question', 'answer', 'created', 'answered',
    )
    search_fields = ('question', 'answer')

    def get_queryset(self, request):
        return (
            super(ClosedQuestionAdmin, self)
            .get_queryset(request)
            .filter(answered__isnull=False)
        )

    @admin.display(description=VerboseNames.Role.ROLE)
    def get_user_role(self, question):
        return question.user.role

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class QuestionStats(Question):

    class Meta:
        proxy = True
        verbose_name = VerboseNames.Question.QUESTION_STATS
        verbose_name_plural = VerboseNames.Question.QUESTION_STATS


@admin.register(QuestionStats)
class QuestionStatsAdmin(ExportActionModelAdmin):
    date_hierarchy = 'created'
    list_display = ('id', 'user', 'question', 'answer', 'created', 'answered')
    list_filter = ('user__platform', 'user__role')
    readonly_fields = list_display
    search_fields = ('question', 'answer')

    def get_actions(self, request):
        return None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
