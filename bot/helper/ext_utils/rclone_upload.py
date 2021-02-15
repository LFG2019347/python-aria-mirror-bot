import logging
import os
import subprocess
from bot import REMOTE_ID,REMOTE_PATH

logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
LOGGER = logging.getLogger(__name__)


def execute_cmd(filepath,remoteid,remotepath):
	commands_to_execute = [
			"rclone",
			"copy",
			"-v",
			filepath,
			"{}:/{}".format(remoteid,remotepath)
			]
	process = subprocess.Popen(
			commands_to_execute,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			)
	stdout, stderr = process.communicate()
	try:
		upload_message='\n'.join([i for i in str(stderr,encoding = "utf-8").split('\n') if 'INFO' not in i and len(i) > 1])
	except BaseException as e:
		LOGGER.error(e)
		return None
	else:
		return upload_message

def rc_upload(path):
	if os.path.isfile(path):
		filepath = path
		remoteid = REMOTE_ID
		remotepath = REMOTE_PATH
		upload_message = execute_cmd(filepath,remoteid,remotepath)
	else:
		filepath = path
		remoteid = REMOTE_ID
		remotepath = os.path.join(REMOTE_PATH,os.path.split(path)[-1])
		upload_message = execute_cmd(filepath,remoteid,remotepath)
	return upload_message

