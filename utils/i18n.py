import os
import gettext


LOCALE_PATH = os.path.dirname(os.path.abspath(__file__))
SYSCONFIG_I18N = '/etc/sysconfig/i18n'
LANGUAGE_LIST = {"en": "en_US", "zh": "zh_CN"}
ADVICE_SEPARATOR = "#advice#"


class I18n(object):
    def __init__(self):
        # self.lang = "zh"
        self.gettext_zh = gettext.translation('zh_CN', LOCALE_PATH,
                                              languages=['zh_CN'])
        self.gettext_en = gettext.translation('en_US', LOCALE_PATH,
                                              languages=['en_US'])


    def get_label(self, msg_id, lang, *args, **kwargs):
        if not msg_id:
            return ""

        if lang == "zh":
            current_gettext = self.gettext_zh.gettext
        else:
            current_gettext = self.gettext_en.gettext

        msgstr = current_gettext(msg_id)
        if kwargs and kwargs.get(lang):
            args = kwargs.get(lang, ())
            if not isinstance(args, tuple):
                args = (args,)
        msgstr = msgstr if not args else msgstr % args

        index = msgstr.find(ADVICE_SEPARATOR)
        if index > 0:
            message = msgstr[:index]
            advice = msgstr[index + len(ADVICE_SEPARATOR):]
        else:
            message = msgstr
            advice = ""

        return {
            "code": msg_id,
            "message": message,
            "advice": advice
        }
