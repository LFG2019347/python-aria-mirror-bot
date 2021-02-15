from telegram.ext import CommandHandler, run_async
from bot import LOGGER, dispatcher, DOWNLOAD_DIR
from bot.helper.telegram_helper.message_utils import auto_delete_message, sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
import threading
from bot.helper.telegram_helper.bot_commands import BotCommands
import os, os.path,shutil

@run_async
def clean_dir(update,context):
    args = update.message.text.split(" ",maxsplit=1)
    if len(args) > 1:
        try:
            path = os.path.join(DOWNLOAD_DIR,args[1])
            LOGGER.info(f"Cleaning download: {path}")
            shutil.rmtree(path)
        except Exception as e:
            sendMessage(e,context.bot,update)
            LOGGER.info(f"Cleaning download:{e}")
        else:
            sendMessage("Cleaning Complete",context.bot,update)
    else:
        sendMessage("Please enter the file path that you want to delete.",context.bot,update)
        
    threading.Thread(target=auto_delete_message, args=(context.bot, update.message, reply_message)).start()

list_handler = CommandHandler(BotCommands.CleanCommand, clean_dir,filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
dispatcher.add_handler(list_handler)
