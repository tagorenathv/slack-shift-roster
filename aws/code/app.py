import re
from handler_functions import (
    app_home_opened,
    create_list,
    create_message,
    create_view,
    delete,
    help_message,
    list_view,
    manage,
    pick,
    pick_view,
    stats,
    update_users,
)
from slack_sdk.errors import SlackApiError
import json
import base64
import urllib.parse
from app_config import logger


def lambda_handler(event, context):
    if event.get("isBase64Encoded", False):
        # Decode from Base64
        base64_message = event["body"]
        base64_bytes = base64_message.encode("utf-8")
        message_bytes = base64.b64decode(base64_bytes)

        # Decode the bytes to a string (URL-encoded)
        url_encoded_body = message_bytes.decode("utf-8")

        # Parse the URL-encoded data into a dictionary
        parsed_body = urllib.parse.parse_qs(url_encoded_body)

        # Convert the dictionary values from lists to single values
        slack_event = {k: v[0] for k, v in parsed_body.items()}
    else:
        slack_event = json.loads(event["body"])

    try:
        if slack_event.get("type") == "url_verification":
            return {"statusCode": 200, "body": slack_event.get("challenge")}
        elif slack_event.get("command"):
            handle_command(slack_event)
        elif slack_event.get("event"):
            handle_event(slack_event)
        elif slack_event.get("payload"):
            payload = json.loads(slack_event["payload"])
            if payload.get("type") == "block_actions":
                handle_block_actions(payload)
            elif payload.get("type") == "view_submission":
                handle_view_submissions(payload)
        else:
            logger.error("Unsupported request: %s", slack_event)
            return {"statusCode": 404, "body": "Unsupported request"}

        return {"statusCode": 200}
    except SlackApiError as e:
        logger.error("Error: %s", e.response["error"], e)
        return {"statusCode": 500, "body": "Error communicating with Slack"}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"statusCode": 500, "body": "An unexpected error occurred"}


def handle_command(payload):
    command = payload.get("command")
    channel_id = payload.get("channel_id")
    trigger_id = payload.get("trigger_id")

    if command == "/pick":
        pick_view(channel_id)
    elif command == "/list":
        list_view(channel_id)
    elif command == "/create":
        create_view(channel_id, trigger_id)
    else:
        logger.warning("Unknown command: %s", command)
        help_message(channel_id)


def handle_event(data):
    event_type = data.get("event").get("type")
    if event_type == "app_mention":
        text = data.get("event").get("text")
        channel_id = data.get("event").get("channel")
        regex_create = r"<[^>]*>\s+create$"
        regex_pick = r"<[^>]*>\s+pick$"
        regex_list = r"<[^>]*>\s+list$"
        if re.search(regex_create, text):
            create_message(channel_id)
            return
        elif re.search(regex_pick, text):
            pick_view(channel_id)
            return
        elif re.search(regex_list, text):
            list_view(channel_id)
            return
        else:
            logger.error("Unhandled app_mention event: %s", event_type)
            help_message(channel_id)
            return
    elif event_type == "app_home_opened":
        app_home_opened()
        return
    else:
        logger.error("Unhandled event type: %s", event_type)
        help_message(channel_id)
        return

    return


def handle_block_actions(payload):
    block_action_handler_dict = {
        "stats": stats,
        "pick": pick,
        "manage": manage,
        "delete": delete,
    }
    action = payload.get("actions")[0]["action_id"].split("__")[0]
    channel_id = payload.get("channel").get("id")
    trigger_id = payload.get("trigger_id")
    if action == "create":
        create_view(channel_id, trigger_id)
        return
    else:
        table_id = payload.get("actions")[0]["action_id"].split("__")[1]
        if table_id == "select_user":
            table_id = payload.get("actions")[0].get("selected_option").get("value")
        message_ts = payload.get("message").get("ts")
        block_action_handler_dict[action](table_id, channel_id, trigger_id, message_ts)
        return


def handle_view_submissions(payload):
    callback_id = payload.get("view").get("callback_id").split("__")[0]
    view_submission_handler_dict = {
        "create_list_modal": create_list,
        "manage_users_modal": update_users,
    }
    view_submission_handler_dict[callback_id](payload)
    return
