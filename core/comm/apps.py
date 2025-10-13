from django.apps import AppConfig
import threading


class CommConfig(AppConfig):
    name = 'core.comm'
    verbose_name = 'comm'
    default_auto_field = 'django.db.models.BigAutoField'


    def ready(self):
        from utils import playwright

        # 在后台线程初始化 browser
        def init_browser_thread():
            playwright.get_browser()

        threading.Thread(target=init_browser_thread, daemon=True).start()