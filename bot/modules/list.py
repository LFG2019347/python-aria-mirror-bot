from telegram.ext import CommandHandler, run_async
from bot import LOGGER, dispatcher, DOWNLOAD_DIR
from bot.helper.telegram_helper.message_utils import auto_delete_message, sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
import threading
from bot.helper.telegram_helper.bot_commands import BotCommands
import os, os.path,time

def get_FileSize(filePath,suffix='B'):
    num = 0
    for root, dirs, files in os.walk(filePath):
        num += sum([os.path.getsize(os.path.join(root, name)) for name in files])
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            num_str = "%3.1f%s%s" % (num, unit, suffix)
            return  num_str
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)
    
def get_FileModifyTime(filePath):
    t = os.path.getmtime(filePath)
    timeStruct = time.localtime(t)
    return time.strftime('%Y-%m-%d %H:%M:%S',timeStruct)

@run_async
def list_drive(update,context):
    try:
        file_paths = [os.path.join(DOWNLOAD_DIR,i) for i in os.listdir(DOWNLOAD_DIR)]
        mes = ''.join([f'<code>{os.path.split(i)[-1]}</code> {get_FileSize(i)} {get_FileModifyTime(i)}\n' for i in file_paths])
    except Exception as e:
        mes = None
    if mes:
        reply_message = sendMessage(mes, context.bot, update)
    else:
        reply_message = sendMessage('There is no file', context.bot, update)

    threading.Thread(target=auto_delete_message, args=(context.bot, update.message, reply_message)).start()


list_handler = CommandHandler(BotCommands.ListCommand, list_drive,filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
dispatcher.add_handler(list_handler)
