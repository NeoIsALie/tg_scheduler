import asyncio

from telethon import TelegramClient, connection

from config import get_settings
from scheduler import TGScheduler


async def main():
    settings = get_settings()
    async with TelegramClient(
        settings.tg_settings.user,
        api_id=int(settings.tg_settings.api_id),
        api_hash=settings.tg_settings.api_hash,
        connection=connection.ConnectionTcpMTProxyRandomizedIntermediate,
        proxy=(
            settings.proxy.host,
            settings.proxy.port,
            settings.proxy.secret
        ),
        timeout=30,
        connection_retries=5,
        retry_delay=2
    ) as app:
        scheduler = TGScheduler(app, settings.scheduler.source_channel, settings.scheduler.target_channel)
        scheduler.create_schedule()
        await scheduler.run()

asyncio.run(main())