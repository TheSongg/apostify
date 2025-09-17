from core.comm.serializers import AccountSerializer
import unicodedata
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.static import PLATFORM_TYPE_CHOICES


def get_display_width(s):
    """计算字符在等宽字体下的显示宽度，中文为 2，英文为 1"""
    width = 0
    for c in s:
        if unicodedata.east_asian_width(c) in ('F', 'W', 'A'):
            width += 2
        else:
            width += 1
    return width


def pad_string(s, width):
    """根据显示宽度填充空格"""
    s = str(s)
    display_width = get_display_width(s)
    return s + ' ' * (width - display_width)


def account_list_html_table():
    headers = ["序号", "平台", "昵称", "cookie过期时间"]
    account_list = []
    for instance in AccountSerializer(many=True).data:
        account_list.append(
            {
                "platfrom": PLATFORM_TYPE_CHOICES[instance["platform_type"]]["zh"],
                "nickname": instance["nickname"],
                "expiration_time": instance["expiration_time"]
            }
        )

    # 计算每列最大显示宽度
    col_widths = []
    for i, h in enumerate(headers):
        max_len = get_display_width(h)
        for idx, row in enumerate(account_list):
            value = str(idx + 1) if i == 0 else str(list(row.values())[i - 1])
            max_len = max(max_len, get_display_width(value))
        col_widths.append(max_len)

    # 构造表格
    table_lines = []
    header_line = "  ".join(pad_string(h, col_widths[i]) for i, h in enumerate(headers))
    table_lines.append(header_line)

    for idx, row in enumerate(account_list):
        line = "  ".join(
            pad_string(str(idx + 1) if i == 0 else str(list(row.values())[i - 1]), col_widths[i])
            for i in range(len(headers))
        )
        table_lines.append(line)

    table_text = "\n".join(table_lines)

    message = f"<b>账号列表</b>\n<pre>{table_text}</pre>"

    return message


def account_list_inline_keyboard():
    keyboard = [
      [
        InlineKeyboardButton("\u2795 新增账号", callback_data="add_account")
      ],
      [
        InlineKeyboardButton("\u270F\uFE0F 更新账号", callback_data="update_account")
      ],
      [
        InlineKeyboardButton("\U0001F504 刷新cookie", callback_data="refresh_cookie")
      ],
      [
        InlineKeyboardButton("\U0001F50D 查看账号详情", callback_data="account_detail")
      ]
    ]
    return InlineKeyboardMarkup(keyboard)