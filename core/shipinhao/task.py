from celery import shared_task


@shared_task
def upload_videos(nickname, platform_type, file_path, title, tags, video_name):
    # asyncio.run(async_upload_task(nickname, platform_type, file_path, title, tags, video_name))
    pass