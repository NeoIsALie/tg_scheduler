import logging
import random
from asyncio import sleep
from datetime import datetime

from telethon import TelegramClient, events
from telethon.tl.custom import Message


logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s: %(levelname)-8s %(name)-s] %(message)s",
                    handlers=[logging.FileHandler("autoposting.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TGScheduler:
    def __init__(
            self,
            client: TelegramClient,
            source_channel: str,
            target_channel: str,
    ):
        self.client = client
        self.source_channel = source_channel
        self.target_channel = target_channel
        self.schedule = []

        client.add_event_handler(
            self.send_message,
            events.NewMessage(chats=self.source_channel)
        )

        client.add_event_handler(
            self.send_album,
            events.Album(chats=self.source_channel)
        )

    async def get_chat_id(self, channel_name: str) -> int:
        await self.client.get_dialogs()
        chat_id = await self.client.get_entity(channel_name)
        return chat_id

    @staticmethod
    def is_empty(total_messages: int) -> bool:
        return total_messages == 0

    @staticmethod
    def convert_to_mins(x):
        return 60 * int(x[:2]) + int(x[-2:])

    @staticmethod
    def current_time():
        now = datetime.now()
        time_now = f"{now.hour:02}:{now.minute:02}"
        return time_now

    async def sample_messages(self, posts_num: int = 1) -> list | None:
        messages = await self.client.get_messages(self.source_channel, limit=None)
        messages_ids = [m.id for m in messages]
        total_messages = messages.total

        if self.is_empty(total_messages):
            return None

        random_ids = random.sample(messages_ids, posts_num)
        messages = await self.client.get_messages(self.source_channel, ids=random_ids)
        return messages

    def create_schedule(self, posts_num: int = 3):
        self.schedule = []

        for i in range(posts_num):
            hours = random.randint(10, 23)
            mins  = random.randint(0, 59)
            self.schedule.append((f"{hours:02}:{mins:02}", self.source_channel, self.target_channel))

        self.schedule = sorted(self.schedule, key=lambda x: self.convert_to_mins(x[0]))

    async def send_message(self, event) -> None:
        logging.info(f"Sending message {event}")
        msg = event.message
        msg.raw_text = ""
        await self.client.forward_messages(
            self.target_channel,
            event.message
        )

    async def send_album(self, event) -> None:
        logging.info(f"Sending album {event}")
        await self.client.forward_messages(
            self.target_channel,
            event.messages
        )

    async def forward_message(self, message: Message) -> None:
        await self.client.forward_messages(
            self.target_channel,
            message
        )

    async def delete_message(self, message_id: int) -> None:
        await self.client.delete_messages(self.source_channel, message_id)

    async def post(self):
        source_channel_id: int = await self.get_chat_id(self.source_channel)
        target_channel_id: int = await self.get_chat_id(self.target_channel)
        logger.info(f"{self.source_channel} -> {source_channel_id}")
        logger.info(f"{self.target_channel} -> {target_channel_id}")
        if source_channel_id is None or target_channel_id is None:
            return

        sample_messages = await self.sample_messages()
        if not sample_messages:
            return

        for message in sample_messages:
            try:
                logger.info(f"Trying to post {message.id} from {self.source_channel} to {self.target_channel}")
                await self.forward_message(message)
            except Exception:
                return
            else:
                await self.delete_message(message.id)

    async def run(self):
        time_now = self.current_time()
        while True:
            if time_now == "00:00" and len(self.schedule) == 0:
                self.create_schedule()
                for event in self.schedule:
                    e_time, e_queue, e_target = event
                    logger.info(f"[{e_time}] {e_queue} -> {e_target}")

            while len(self.schedule) > 0 and (self.convert_to_mins(time_now) > self.convert_to_mins(self.schedule[0][0])):
                self.schedule.pop(0)
                await self.post()

            await sleep(30)
            time_now = self.current_time()