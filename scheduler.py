import logging
import random
from asyncio import sleep

from telethon import TelegramClient, events
from telethon.tl.custom import Message

from utils import convert_to_mins, current_time


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

    async def sample_messages(self, posts_num: int = 1) -> list | None:
        messages = await self.client.get_messages(self.source_channel, limit=None)
        messages_ids = [m.id for m in messages]
        total_messages = messages.total

        if self.is_empty(total_messages):
            return None

        random_ids = random.sample(messages_ids, posts_num)
        messages = await self.client.get_messages(self.source_channel, ids=random_ids)
        return messages

    def create_schedule(self, posts_num: int = 5):
        self.schedule = []

        for i in range(posts_num):
            hours = random.randint(10, 23)
            mins  = random.randint(0, 59)
            self.schedule.append((f"{hours:02}:{mins:02}", self.source_channel, self.target_channel))

        self.schedule = sorted(self.schedule, key=lambda x: convert_to_mins(x[0]))

    async def get_album(self, message: Message) -> list[Message]:
        messages = await self.client.get_messages(
            self.source_channel,
            limit=10,
            offset_id=message.id,
        )
        album = [msg for msg in messages if msg.grouped_id == message.grouped_id]
        return sorted(album, key=lambda msg: msg.id)

    async def send_message(self, message) -> None:
        logging.info(f"Sending message {message}")
        if message.grouped_id:
            album = await self.get_album(message)
            if album:
                await self.send_album(album)

        if message.text and not message.media:
            await self.client.send_message(self.target_channel, message.text)
            return

        if message.media:
            await self.client.send_file(self.target_channel, message.media, caption=message.text or None)
            return

    async def send_album(self, messages: list[Message]) -> None:
        logging.info(f"Sending album {messages}")

        messages = sorted(messages, key=lambda message: message.id)
        files = [message.media for message in messages if message.media]

        if not files:
            return

        captions = [message.text for message in messages if message.text]
        caption = captions[0] if captions else None

        await self.client.send_file(self.target_channel, files, caption=caption)

    async def delete_message(self, message_id: int) -> None:
        logging.info(f"Deleting message {message_id}")
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
                if isinstance(message, Message):
                    await self.send_message(message)
                else:
                    await self.send_album(message)
            except Exception:
                return
            # else:
                # await self.delete_message(message.id)

    async def run(self):
        time_now = current_time()
        while True:
            if time_now == "00:00" and len(self.schedule) == 0:
                self.create_schedule()
                for event in self.schedule:
                    e_time, e_queue, e_target = event
                    logger.info(f"[{e_time}] {e_queue} -> {e_target}")

            while len(self.schedule) > 0 and (convert_to_mins(time_now) > convert_to_mins(self.schedule[0][0])):
                self.schedule.pop(0)
                await self.post()

            await sleep(30)
            time_now = current_time()