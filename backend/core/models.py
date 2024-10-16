from itertools import chain
from operator import attrgetter

from django.contrib.auth.models import AbstractUser
from django.db import models

from backend.settings import FILES_URL
from core.constants import (
    BUTTON_MAX_LENGTH, PLATFORMS, PLATFORMS_VERBOSE, Platforms,
)
from core.localization import AdminPanel, Defaults, VerboseNames

PLATFORM_MAX_LENGTH = max(len(platform) for platform, _ in PLATFORMS)


class AdminUser(AbstractUser):
    telegram_id = models.BigIntegerField(
        VerboseNames.AdminUser.TELEGRAM_ID,
        blank=True,
        null=True,
        unique=True,
    )
    vk_id = models.BigIntegerField(
        VerboseNames.AdminUser.VK_ID,
        blank=True,
        null=True,
        unique=True,
    )
    is_staff = models.BooleanField(
        VerboseNames.AdminUser.ADMIN_PANEL_ACCESS,
        default=False,
    )

    class Meta:
        verbose_name = VerboseNames.AdminUser.ADMIN_USER
        verbose_name_plural = VerboseNames.AdminUser.ADMIN_USERS


class GenericButton(models.Model):
    name = models.CharField(
        VerboseNames.Buttons.NAME,
        max_length=BUTTON_MAX_LENGTH,
    )
    order = models.PositiveSmallIntegerField(
        VerboseNames.Buttons.ORDER,
        default=0,
    )

    class Meta:
        default_related_name = '%(class)ss'
        abstract = True

    def __str__(self):
        return self.name

    def get_data_for_bot(self):
        data = {
            field.name: getattr(self, field.name)
            for field in self._meta.get_fields()
            if field.concrete and field.name not in ('order', 'parent')
        }
        data['type'] = self.__class__.__name__
        return data


class MenuButton(GenericButton):
    parent = models.ForeignKey('self', models.CASCADE, blank=True, null=True)

    class Meta(GenericButton.Meta):
        verbose_name = VerboseNames.Buttons.MENU
        verbose_name_plural = VerboseNames.Buttons.MENU

    def get_children(self):
        return list(sorted(
            chain(
                self.menubuttons.all(),
                self.infobuttons.all(),
                self.subbuttons.all(),
                self.reminderbuttons.all(),
                self.askadminbuttons.all(),
            ),
            key=attrgetter('order'),
        ))


class Role(models.Model):
    name = models.CharField(
        VerboseNames.Role.NAME,
        max_length=BUTTON_MAX_LENGTH,
        unique=True,
    )
    menu = models.OneToOneField(
        MenuButton,
        on_delete=models.CASCADE,
        verbose_name=VerboseNames.Role.MENU,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = VerboseNames.Role.ROLE
        verbose_name_plural = VerboseNames.Role.ROLES

    def __str__(self):
        return self.name


class BasicButton(GenericButton):
    parent = models.ForeignKey(MenuButton, models.CASCADE)
    answer = models.TextField(VerboseNames.Buttons.ANSWER)

    class Meta(GenericButton.Meta):
        abstract = True


class InfoButton(BasicButton):
    file = models.FileField(
        VerboseNames.Buttons.FILE,
        upload_to=FILES_URL,
        blank=True,
        null=True,
    )

    class Meta(BasicButton.Meta):
        verbose_name = VerboseNames.Buttons.INFO
        verbose_name_plural = VerboseNames.Buttons.INFO_PLURAL


class SubButton(GenericButton):
    parent = models.ForeignKey(MenuButton, models.CASCADE)
    on_name = models.CharField(
        VerboseNames.Buttons.ON_NAME,
        max_length=BUTTON_MAX_LENGTH,
        default=Defaults.SUBSCRIBE,
    )
    off_name = models.CharField(
        VerboseNames.Buttons.OFF_NAME,
        max_length=BUTTON_MAX_LENGTH,
        default=Defaults.UNSUBSCRIBE,
    )
    on_answer = models.TextField(
        VerboseNames.Buttons.IS_SUBSCRIBER,
        default=Defaults.IS_SUBSCRIBER,
    )
    off_answer = models.TextField(
        VerboseNames.Buttons.IS_NOT_SUBSCRIBER,
        default=Defaults.IS_NOT_SUBSCRIBER,
    )

    class Meta(GenericButton.Meta):
        verbose_name = VerboseNames.Buttons.SUB


class ReminderButton(BasicButton):
    text = models.TextField(VerboseNames.Buttons.REMINDER_TEXT)

    class Meta(BasicButton.Meta):
        verbose_name = VerboseNames.Buttons.REMINDER


class AskAdminButton(BasicButton):
    received_answer = models.TextField(VerboseNames.Buttons.RECEIVED_ANSWER)

    class Meta(BasicButton.Meta):
        verbose_name = VerboseNames.Buttons.ASK_ADMIN


class User(models.Model):
    platform = models.CharField(
        VerboseNames.User.PLATFORM,
        choices=PLATFORMS,
        max_length=PLATFORM_MAX_LENGTH,
    )
    platform_id = models.BigIntegerField(VerboseNames.User.PLATFORM_ID)
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        verbose_name=VerboseNames.User.ROLE,
    )
    is_subscribed = models.BooleanField(
        VerboseNames.User.IS_SUBSCRIBED,
        default=False,
    )
    date_subscribed = models.DateTimeField(
        VerboseNames.User.DATE_SUBSCRIBED,
        blank=True,
        null=True,
        default=None,
    )
    is_blocked = models.BooleanField(
        VerboseNames.User.IS_BLOCKED,
        default=False,
    )

    class Meta:
        verbose_name = VerboseNames.User.USER
        verbose_name_plural = VerboseNames.User.USERS
        constraints = [
            models.UniqueConstraint(
                fields=('platform', 'platform_id'),
                name='unique_user',
            ),
        ]

    def __str__(self):
        return f'{PLATFORMS_VERBOSE[self.platform]}#{self.platform_id}'


class Question(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=VerboseNames.Question.USER,
        related_name='questions',
    )
    question = models.TextField(verbose_name=VerboseNames.Question.QUESTION)
    answer = models.TextField(VerboseNames.Question.ANSWER, blank=True)
    created = models.DateTimeField(
        VerboseNames.Question.CREATED,
        auto_now_add=True,
    )
    answered = models.DateTimeField(
        VerboseNames.Question.CLOSED,
        blank=True,
        null=True,
        default=None,
    )
    answer_sent = models.DateTimeField(
        VerboseNames.Question.ANSWER_SENT,
        blank=True,
        null=True,
        default=None,
    )

    class Meta:
        verbose_name = VerboseNames.Question.QUESTION
        verbose_name_plural = VerboseNames.Question.QUESTIONS
        ordering = ('created',)

    def __str__(self):
        return AdminPanel.QUESTION.format(id=self.id, user=self.user)


class MenuUpdate(models.Model):
    created = models.DateTimeField(VerboseNames.CREATED, auto_now_add=True)
    telegram = models.DateTimeField(
        Platforms.TELEGRAM_FULL,
        blank=True,
        null=True,
    )
    vk = models.DateTimeField(Platforms.VK_FULL, blank=True, null=True)

    class Meta:
        verbose_name = VerboseNames.MenuUpdate.MenuUpdate
        verbose_name_plural = VerboseNames.MenuUpdate.MenuUpdates

    def __str__(self):
        return f'{self.__class__.__name__}#{self.id}'
