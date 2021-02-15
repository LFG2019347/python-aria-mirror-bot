#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This script is sourced from Shrimadhav's AnyDLBot project

# the logging things
import logging
logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
LOGGER = logging.getLogger(__name__)
import subprocess
import os
import time
import telegram
import pathlib
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from bot.helper.telegram_helper.message_utils import sendGroup


def place_water_mark(input_file, output_file, water_mark_file):
    watermarked_file = output_file + ".watermark.png"
    metadata = extractMetadata(createParser(input_file))
    width = metadata.get("width")
    # https://stackoverflow.com/a/34547184/4723940
    shrink_watermark_file_genertor_command = [
        "ffmpeg",
        "-i", water_mark_file,
        "-y -v quiet",
        "-vf",
        "scale={}*0.5:-1".format(width),
        watermarked_file
    ]
    # print(shrink_watermark_file_genertor_command)
    process = subprocess.Popen(
        shrink_watermark_file_genertor_command,
        # stdout must a pipe to be accessible as process.stdout
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    commands_to_execute = [
        "ffmpeg",
        "-i", input_file,
        "-i", watermarked_file,
        "-filter_complex",
        # https://stackoverflow.com/a/16235519
        # "\"[0:0] scale=400:225 [wm]; [wm][1:0] overlay=305:0 [out]\"",
        # "-map \"[out]\" -b:v 896k -r 20 -an ",
        "\"overlay=(main_w-overlay_w):(main_h-overlay_h)\"",
        # "-vf \"drawtext=text='@FFMovingPictureExpertGroupBOT':x=W-(W/2):y=H-(H/2):fontfile=" + Config.FONT_FILE + ":fontsize=12:fontcolor=white:shadowcolor=black:shadowx=5:shadowy=5\"",
        output_file
    ]
    # print(commands_to_execute)
    process = subprocess.Popen(
        commands_to_execute,
        # stdout must a pipe to be accessible as process.stdout
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    return output_file


def take_screen_shot(video_file, output_directory, ttl):
    # https://stackoverflow.com/a/13891070/4723940
    out_put_file_name = output_directory + \
        "/" + str(time.time()) + ".jpg"
    file_genertor_command = [
        "ffmpeg",
        "-ss",
        str(ttl),
        "-i",
        video_file,
        "-vframes",
        "1",
        out_put_file_name
    ]
    # width = "90"
    process = subprocess.Popen(
        file_genertor_command,
        # stdout must a pipe to be accessible as process.stdout
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    else:
        return None

# https://github.com/Nekmo/telegram-upload/blob/master/telegram_upload/video.py#L26

def cult_small_video(video_file, output_directory, start_time, end_time):
    # https://stackoverflow.com/a/13891070/4723940
    out_put_file_name = output_directory + \
        "/" + str(round(time.time())) + ".mp4"
    file_genertor_command = [
        "ffmpeg",
        "-i",
        video_file,
        "-ss",
        start_time,
        "-to",
        end_time,
        "-async",
        "1",
        "-strict",
        "-2",
        out_put_file_name
    ]
    process = subprocess.Popen(
        file_genertor_command,
        # stdout must a pipe to be accessible as process.stdout
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    else:
        return None


def generate_screen_shots(
    video_file,
    output_directory,
    is_watermarkable,
    wf,
    min_duration,
    no_of_photos
):
    metadata = extractMetadata(createParser(video_file))
    duration = 0
    if metadata is not None:
        if metadata.has("duration"):
            duration = metadata.get('duration').seconds
    if duration > min_duration:
        images = []
        ttl_step = duration // no_of_photos
        current_ttl = ttl_step
        for looper in range(0, no_of_photos):
            ss_img = take_screen_shot(video_file, output_directory, current_ttl)
            current_ttl = current_ttl + ttl_step
            if is_watermarkable:
                ss_img = place_water_mark(ss_img, output_directory + "/" + str(time.time()) + ".jpg", wf)
            images.append(ss_img)
        return images
    else:
        return None


def send_photo(filepath, bot, update):
    os.mkdir(os.path.splitext(filepath)[0])
    is_w_f = False
    images = generate_screen_shots(filepath, os.path.splitext(filepath)[0], is_w_f, "", 150, 9)
    media_album_p = []
    if images is not None:
        for image in images:
            with open(image,'rb') as fp:
                media_album_p.append(telegram.InputMediaPhoto(media=fp))
        sendGroup(media_album_p, bot, update)
    LOGGER.info(images)


def ju_file(path,bot,update):
    list_video=['.mp4','.m4v','.mkv','.webm','.mov','.avi','.wmv','.flv']
    if os.path.isfile(path):
        up_name = pathlib.PurePath(path).name
        if os.path.splitext(up_name)[-1].lower() in list_video:
            send_photo(path,bot,update)
            upload_dir = os.path.split(path)[0]
            return upload_dir
        else:
            return path
    else:
        all_path = [os.path.join(path,i) for i in os.listdir(path) if os.path.isfile(os.path.join(path,i)) and os.path.splitext(i)[-1].lower() in list_video]
        if len(all_path) < 4:
            for i in all_path:
                send_photo(os.path.join(path,i),bot,update)
        return path

