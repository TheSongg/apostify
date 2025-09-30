from utils.utils import get_thread_language
from utils.i18n import I18n


aic_i18n = I18n()


class APException(Exception):
    def __init__(self, message, code='0001', *args, **kwargs):
        super(APException, self).__init__()
        self._args = args
        self.data = aic_i18n.get_label(code, get_thread_language(), *args, **kwargs)
        self.code = code
        self.message = message
        self.status = kwargs.get('status', 500)
        self.err_name = kwargs.get('err_name', None)
        self.strategy = kwargs.get("strategy", None)

    def __str__(self):
        return self.message

    def get_args(self):
        return self._args