from telegram.ext import CommandHandler
from bot.helper.telegram_helper.message_utils import *
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import new_thread
from bot.helper.ext_utils.rclone_upload import rc_upload
from bot import dispatcher, DOWNLOAD_DIR
import os.path


@new_thread
def cloneNode(update,context):
    args = update.message.text.split(" ",maxsplit=1)
    if len(args) > 1:
        try:
            path = os.path.join(DOWNLOAD_DIR,args[1])
            msg = sendMessage(f"Cloning: <code>{path}</code>",context.bot,update)
            upload_message = rc_upload(path)
        except Exception as e:
            deleteMessage(context.bot,msg)
            sendMessage(e,context.bot,update)
        else:
            deleteMessage(context.bot,msg)
            sendMessage(upload_message,context.bot,update)
    else:
        sendMessage("Provide file path to Clone.",context.bot,update)

clone_handler = CommandHandler(BotCommands.CloneCommand,cloneNode,filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
dispatcher.add_handler(clone_handler)
