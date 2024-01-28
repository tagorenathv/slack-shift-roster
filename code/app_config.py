import logging
import os
from slack_sdk import WebClient
import boto3


BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
client = WebClient(token=BOT_TOKEN)

dynamodb = boto3.resource("dynamodb")
shift_rosters_table = dynamodb.Table("shift-rosters")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
