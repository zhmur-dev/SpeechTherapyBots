from django.core.management.base import BaseCommand

from core.constants import Platforms
from core.telegram_bot import TelegramBot


class Command(BaseCommand):
    help = 'Run telegram bot'

    def handle(self, *args, **kwargs):
        TelegramBot(Platforms.TELEGRAM)
