from django.core.management.base import BaseCommand

from core.vk_bot import VKBot
from core.constants import Platforms


class Command(BaseCommand):
    help = 'Start VK Bot'

    def handle(self, *args, **options):
        VKBot(Platforms.VK)
