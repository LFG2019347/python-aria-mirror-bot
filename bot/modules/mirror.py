import requests
from telegram.ext import CommandHandler, run_async

from bot import Interval, LOGGER, AUTO_RCLONE
from bot import dispatcher, DOWNLOAD_DIR, DOWNLOAD_STATUS_UPDATE_INTERVAL, download_dict, download_dict_lock
from bot.helper.ext_utils import fs_utils, bot_utils
from bot.helper.ext_utils.generate_photo import ju_file
from bot.helper.ext_utils.pornhb import generat_pornhb_url
from bot.helper.ext_utils.rclone_upload import rc_upload
from bot.helper.ext_utils.bot_utils import setInterval
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException, NotSupportedExtractionArchive
from bot.helper.mirror_utils.download_utils.aria2_download import AriaDownloadHelper
from bot.helper.mirror_utils.download_utils.direct_link_generator import direct_link_generator
from bot.helper.mirror_utils.download_utils.telegram_downloader import TelegramDownloadHelper
from bot.helper.mirror_utils.status_utils import listeners
from bot.helper.mirror_utils.status_utils.extract_status import ExtractStatus
from bot.helper.mirror_utils.status_utils.tar_status import TarStatus
from bot.helper.mirror_utils.status_utils.upload_status import UploadStatus
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import *
import pathlib
import os
import subprocess
import threading

ariaDlManager = AriaDownloadHelper()
ariaDlManager.start_listener()

class MirrorListener(listeners.MirrorListeners):
    def __init__(self, bot, update, isTar=False,tag=None, extract=False):
        super().__init__(bot, update)
        self.isTar = isTar
        self.tag = tag
        self.extract = extract

    def onDownloadStarted(self):
        pass

    def onDownloadProgress(self):
        # We are handling this on our own!
        pass

    def clean(self):
        try:
            Interval[0].cancel()
            del Interval[0]
            delete_all_messages()
        except IndexError:
            pass

    def onDownloadComplete(self):
        with download_dict_lock:
            LOGGER.info(f"Download completed: {download_dict[self.uid].name()}")
            download = download_dict[self.uid]
            name = download.name()
            size = download.size_raw()
            m_path = f'{DOWNLOAD_DIR}{self.uid}/{download.name()}'
        if self.isTar:
            download.is_archiving = True
            try:
                with download_dict_lock:
                    download_dict[self.uid] = TarStatus(name, m_path, size)
                path = fs_utils.tar(m_path)
            except FileNotFoundError:
                LOGGER.info('File to archive not found!')
                self.onUploadError('Internal error occurred!!')
                return
        elif self.extract:
            download.is_extracting = True
            try:
                path = fs_utils.get_base_name(m_path)
                LOGGER.info(
                    f"Extracting : {name} "
                )
                with download_dict_lock:
                    download_dict[self.uid] = ExtractStatus(name, m_path, size)
                archive_result = subprocess.run(["extract", m_path])
                if archive_result.returncode == 0:
                    threading.Thread(target=os.remove, args=(m_path,)).start()
                    LOGGER.info(f"Deleting archive : {m_path}")
                else:
                    LOGGER.warning('Unable to extract archive! Uploading anyway')
                    path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
                LOGGER.info(
                    f'got path : {path}'
                )

            except NotSupportedExtractionArchive:
                LOGGER.info("Not any valid archive, uploading file as it is.")
                path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
        else:
            path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
            
        upload_path = ju_file(path,self.bot,self.update)
        if AUTO_RCLONE:
            upload_message = rc_upload(upload_path)
            if upload_message is not None:
                sendMessage(upload_message, self.bot, self.update)
            LOGGER.info(upload_message)
        update_all_messages()

    def onDownloadError(self, error):
        error = error.replace('<', ' ')
        error = error.replace('>', ' ')
        LOGGER.info(self.update.effective_chat.id)
        with download_dict_lock:
            try:
                download = download_dict[self.uid]
                del download_dict[self.uid]
                LOGGER.info(f"Deleting folder: {download.path()}")
                fs_utils.clean_download(download.path())
                LOGGER.info(str(download_dict))
            except Exception as e:
                LOGGER.error(str(e))
                pass
            count = len(download_dict)
        if self.message.from_user.username:
            uname = f"@{self.message.from_user.username}"
        else:
            uname = f'<a href="tg://user?id={self.message.from_user.id}">{self.message.from_user.first_name}</a>'
        msg = f"{uname} your download has been stopped due to: {error}"
        sendMessage(msg, self.bot, self.update)
        if count == 0:
            self.clean()
        else:
            update_all_messages()

    def onUploadStarted(self):
        pass

    def onUploadProgress(self):
        pass

    def onUploadComplete(self, link: str):
        pass

    def onUploadError(self, error):
        pass

def _mirror(bot, update, isTar=False, extract=False):
    message_args = update.message.text.split(' ')
    try:
        link = message_args[1]
    except IndexError:
        link = ''
    LOGGER.info(link)
    link = link.strip()
    reply_to = update.message.reply_to_message
    if reply_to is not None:
        file = None
        tag = reply_to.from_user.username
        media_array = [reply_to.document, reply_to.video, reply_to.audio, reply_to.photo]
        for i in media_array:
            if i is not None:
                file = i
                break

        if len(link) == 0:
            if file is not None:
                if isinstance(file,list):
                    link = file[-1].get_file().file_path
                elif file.mime_type != "application/x-bittorrent":
                    listener = MirrorListener(bot, update, isTar, tag, extract)
                    tg_downloader = TelegramDownloadHelper(listener)
                    tg_downloader.add_download(reply_to, f'{DOWNLOAD_DIR}{listener.uid}/')
                    sendStatusMessage(update, bot)
                    if len(Interval) == 0:
                        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))
                    return
                else:
                    link = file.get_file().file_path
    else:
        tag = None
    if not bot_utils.is_url(link) and not bot_utils.is_magnet(link):
        sendMessage('No download source provided', bot, update)
        return
    
    if "pornhub" in link:
        try:  
            link=generat_pornhb_url(link)
        except Exception as e:
            LOGGER.info(f'{link}: {e}')
            
    try:
        link = direct_link_generator(link)
    except DirectDownloadLinkException as e:
        LOGGER.info(f'{link}: {e}')

    listener = MirrorListener(bot, update, isTar, tag, extract)
    ariaDlManager.add_download(link, f'{DOWNLOAD_DIR}/{listener.uid}/',listener)
    sendStatusMessage(update, bot)
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))


@run_async
def mirror(update, context):
    _mirror(context.bot, update)


@run_async
def tar_mirror(update, context):
    _mirror(context.bot, update, True)


@run_async
def unzip_mirror(update, context):
    _mirror(context.bot,update, extract=True)


mirror_handler = CommandHandler(BotCommands.MirrorCommand, mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
tar_mirror_handler = CommandHandler(BotCommands.TarMirrorCommand, tar_mirror,
                                    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
unzip_mirror_handler = CommandHandler(BotCommands.UnzipMirrorCommand, unzip_mirror,
                                      filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
dispatcher.add_handler(mirror_handler)
dispatcher.add_handler(tar_mirror_handler)
dispatcher.add_handler(unzip_mirror_handler)
