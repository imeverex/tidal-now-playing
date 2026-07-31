import asyncio

from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
)


async def main():
    manager = await MediaManager.request_async()
    sessions = manager.get_sessions()
    if not sessions:
        print("No active media sessions found. Play something first.")
        return

    for session in sessions:
        props = await session.try_get_media_properties_async()
        print(f"aumid={session.source_app_user_model_id!r}  title={props.title!r}  artist={props.artist!r}")


if __name__ == "__main__":
    asyncio.run(main())
