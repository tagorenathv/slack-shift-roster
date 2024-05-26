import logging
import json
import functions_framework
from flask import jsonify, request
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import os
from blocks import get_create_rotation_modal, get_delete_rotation_modal, get_edit_rotation_modal, get_rotation_blocks
from google.cloud import firestore

logging.basicConfig(level=logging.INFO)

load_dotenv()
slack_token = os.getenv("TOKEN")
client = WebClient(token=slack_token)
db = firestore.Client(database=os.getenv("FIRESTORE_DB"))

@functions_framework.http
def slack_events(request):
    slack_event = request.get_json(silent=True)

    if not slack_event:
        return jsonify({"status": "invalid request"}), 400

    if slack_event.get("type") == "url_verification":
        return jsonify({"challenge": slack_event.get("challenge")})

    elif slack_event.get("event"):
        data = slack_event.get("event")
        event_type = data.get("type")

        if event_type == "app_mention":
            channel_id = data.get("channel")
            text = data.get("text")
            thread_ts = data.get("thread_ts", data.get("ts"))
            user_id = data.get("user")
            handle_app_mention(channel_id, user_id, thread_ts, text)

    return jsonify({"status": "ok"})

@functions_framework.http
def slack_interactions(request):
    payload = json.loads(request.form["payload"])
    trigger_id = payload["trigger_id"]
    actions = payload.get("actions", [])

    if actions:
        action_id = actions[0]["action_id"]
        if action_id == "create_rotation_button":
            return open_create_rotation_modal(trigger_id)
        elif action_id == "delete_rotation_button":
            rotation_name = actions[0]["value"].split("_")[1]
            channel_id = payload["channel"]["id"]
            thread_ts = payload["message"]["ts"]
            return show_delete_rotation_modal(trigger_id, rotation_name, channel_id, thread_ts)
        elif action_id == "notify_button":
            # Perform the rotation operations asynchronously
            from threading import Thread
            thread = Thread(target=handle_notify_button, args=(payload,))
            thread.start()
            
            return jsonify({"status": "ok"})
        elif action_id == "next_pick_button":
            rotation_name = actions[0]["value"].split("_")[2]
            user_id = payload["user"]["id"]
            channel_id = payload["channel"]["id"]
            thread_ts = payload["message"]["ts"]            
        
            # Perform the rotation operations asynchronously
            from threading import Thread
            thread = Thread(target=rotate_user, args=(rotation_name, user_id, channel_id, thread_ts))
            thread.start()
            
            return jsonify({"status": "ok"})
        elif action_id == "edit_rotation_button":
            rotation_name = actions[0]["value"].split("_")[1]
            current_channel = get_current_reminder_channel(rotation_name)
            selected_users = get_selected_users(rotation_name)
            return show_edit_rotation_modal(trigger_id, rotation_name, current_channel, selected_users)
    
    if payload["type"] == "view_submission":
        callback_id = payload["view"]["callback_id"]
        if callback_id == "create_rotation":
            return handle_create_rotation_submission(payload)
        elif callback_id == "confirm_delete_rotation":
            return handle_delete_rotation_submission(payload)
        elif callback_id == "confirm_edit_rotation":
            return handle_edit_rotation_submission(payload)

    return jsonify({"status": "ok"})

def open_create_rotation_modal(trigger_id):
    modal = get_create_rotation_modal()

    try:
        client.views_open(
            trigger_id=trigger_id,
            view=modal
        )
        return jsonify({"status": "modal opened"})
    except SlackApiError as e:
        logging.error(f"Error opening modal: {e.response['error']}")
        return jsonify({"status": "error", "error": e.response['error']}), 500

def get_normalized_rotation_name(rotation_name):
    return rotation_name.lower()

def handle_create_rotation_submission(payload):
    rotation_name = payload["view"]["state"]["values"]["rotation_name"]["rotation_name_input"]["value"]
    create_user_group = payload["view"]["state"]["values"]["create_user_group_toggle"]["create_user_group_radio"]["selected_option"]["value"]
    logging.info("Payload view state values: %s", json.dumps(payload["view"]["state"]["values"], indent=2))

    users_in_rotation = payload["view"]["state"]["values"]["users_in_rotation"]["users_select"]["selected_conversations"]
    reminder_channel = payload["view"]["state"]["values"]["reminder_channel"]["channel_select"]["selected_conversation"]

    # Respond to Slack to close the modal
    response = jsonify({"response_action": "clear"})
    response.status_code = 200

    # Perform validation for existing rotation
    normalized_rotation_name = get_normalized_rotation_name(rotation_name)
    rotation_ref = db.collection('rotations').document(normalized_rotation_name)
    rotation = rotation_ref.get()

    if rotation.exists:
        return {
            "response_action": "errors",
            "errors": {
                "rotation_name": "Rotation with this name already exists."
            }
        }

    # Perform the save/creation operations asynchronously
    from threading import Thread
    thread = Thread(target=process_rotation_creation, args=(normalized_rotation_name, rotation_name, create_user_group, users_in_rotation, reminder_channel))
    thread.start()

    return response

# use normatised name ===> continue from
def process_rotation_creation(normalized_rotation_name, rotation_name, create_user_group, users_in_rotation, reminder_channel):    
    try:
        user_group_id = None
        user_group_handle = None
        if create_user_group == 'yes':
            user_group_id, user_group_handle = get_or_create_user_group(rotation_name)

        current_on_call = users_in_rotation[0]  # Assuming the first user is the initial on-call user

        store_rotation_data(normalized_rotation_name, rotation_name, create_user_group, users_in_rotation, reminder_channel, user_group_id, user_group_handle, current_on_call)

        # Set the initial on-call user in the user group
        if create_user_group == 'yes' and user_group_id:
            set_user_group_member(user_group_id, current_on_call)

        # Send success message to the reminder channel
        send_confirmation_message(reminder_channel, rotation_name, success=True, user_group=user_group_handle)
    except Exception as e:
        logging.error(f"Error processing rotation creation: {e}")
        # Send failure message to the reminder channel
        send_confirmation_message(reminder_channel, rotation_name, success=False, error=str(e))

def generate_user_group_handle(rotation_name):
    return rotation_name.lower().replace(' ', '-')

def get_or_create_user_group(rotation_name):
    user_group_handle = generate_user_group_handle(rotation_name)
    user_group_id = get_user_group_by_handle(user_group_handle)
    
    if user_group_id is None:
        try:
            response = client.usergroups_create(
                name=rotation_name,
                handle=user_group_handle,
                description=f"User group for {rotation_name}"
            )
            user_group_id = response['usergroup']['id']
        except SlackApiError as e:
            logging.error(f"Error creating user group: {e.response['error']}")
    
    return user_group_id, user_group_handle

def get_user_group_by_handle(user_group_handle):
    try:
        response = client.usergroups_list()
        for group in response['usergroups']:
            if group['handle'] == user_group_handle:
                return group['id']
    except SlackApiError as e:
        logging.error(f"Error fetching user groups: {e.response['error']}")
    return None

def set_user_group_member(user_group_id, current_on_call):
    try:
        client.usergroups_users_update(
            usergroup=user_group_id,
            users=current_on_call
        )
    except SlackApiError as e:
        logging.error(f"Error setting user group members: {e.response['error']}")

def store_rotation_data(normalized_rotation_name, rotation_name, create_user_group, users_in_rotation, reminder_channel, user_group_id, user_group_handle, current_on_call):
    rotation_ref = db.collection('rotations').document(normalized_rotation_name)
    rotation_ref.set({
        'name': rotation_name,
        'create_user_group': create_user_group,
        'users_in_rotation': users_in_rotation,
        'reminder_channel': reminder_channel,
        'user_group_id': user_group_id,
        'user_group_handle': user_group_handle,
        'current_on_call': current_on_call
    })

def send_confirmation_message(channel, rotation_name, success=True, error=None, user_group=None):
    if success:
        if user_group:
            message = f":large_green_circle: Rotation *{rotation_name}* has been created with user group <@{user_group}>! 🥳🎊🎉"
        else:
            message = f":large_green_circle: Rotation *{rotation_name}* has been created! 🥳🎊🎉"
    else:
        message = f":red_circle: *Failed to Create Rotation*\n"
        message += f"Rotation *{rotation_name}* could not be created.\n"
        message += f"Error: {error}"

    try:
        client.chat_postMessage(
            channel=channel,
            text=message
        )
    except SlackApiError as e:
        logging.error(f"Error sending confirmation message: {e.response['error']}")

#### App Mention

def handle_app_mention(channel_id, user_id, thread_ts, text):
    if "rotate" in text.lower():
        rotation_name = extract_rotation_name(text)
        if rotation_name:
            rotate_user(rotation_name, user_id, channel_id, thread_ts)
        else:
            client.chat_postMessage(
                channel=channel_id,
                text="Please provide a rotation name after the *'rotate'* command.\nExample: `rotate catlog-hero`"
            )
    else:
        show_rotation_help(channel_id)
        
def show_rotation_help(channel_id):
    try:
        all_rotations = db.collection('rotations').stream()

        rotations = {
            "channel_rotations": [],
            "other_rotations": []
        }

        for rotation in all_rotations:
            rotation_data = rotation.to_dict()
            reminder_channel = rotation_data.get('reminder_channel')
            current_on_call = rotation_data.get('current_on_call', 'Nobody')

            if reminder_channel == channel_id:
                rotations['channel_rotations'].append({
                    "name": rotation_data['name'],
                    "current_on_call": current_on_call
                })
            else:
                status = f"Currently on call: <@{current_on_call}>" if current_on_call != 'Nobody' else "Nobody is on call at the moment."
                rotations['other_rotations'].append({
                    "name": rotation_data['name'],
                    "status": status
                })

        blocks = get_rotation_blocks(rotations)

        client.chat_postMessage(
            channel=channel_id,
            blocks=blocks,
            text="Rotation App"
        )
    except SlackApiError as e:
        logging.error(f"Error posting message: {e.response['error']}")
    except Exception as e:
        logging.error(f"Error fetching rotations: {str(e)}")


def extract_rotation_name(text):
    # Extract rotation name from the mention text
    parts = text.split()
    if len(parts) > 2:
        return parts[2]
    return None

def rotate_user(rotation_name, user_id, channel_id=None, thread_ts=None):
    normalized_rotation_name = get_normalized_rotation_name(rotation_name)
    rotation_ref = db.collection('rotations').document(normalized_rotation_name)
    rotation = rotation_ref.get()
    
    if not rotation.exists:
        send_error_message(user_id, channel_id, thread_ts, f"Rotation *{rotation_name}* does not exist.")
        return
    
    rotation_data = rotation.to_dict()
    users_in_rotation = rotation_data['users_in_rotation']
    
    new_on_call = users_in_rotation.pop(0)
    users_in_rotation.append(new_on_call)
    
    # Update the rotation in Firestore
    rotation_ref.update({
        'users_in_rotation': users_in_rotation,
        'current_on_call': new_on_call
    })
    
    # Update the user group if it exists
    user_group_id = rotation_data.get('user_group_id')
    user_group_handle = rotation_data.get('user_group_handle')
    if user_group_id:
        set_user_group_member(user_group_id, new_on_call)
    
    # Send rotation update message to the reminder channel
    reminder_channel = rotation_data.get('reminder_channel')
    send_rotation_update_message(reminder_channel, new_on_call, rotation_name, user_group_handle)


def set_user_group_member(user_group_id, new_on_call):
    try:
        client.usergroups_users_update(
            usergroup=user_group_id,
            users=new_on_call
        )
    except SlackApiError as e:
        logging.error(f"Error setting user group members: {e.response['error']}")

def send_rotation_update_message(channel, new_on_call, rotation_name, user_group_handle):
    message = f":mega: Rotation update: <@{new_on_call}> is now on call for *{rotation_name}*"
    if user_group_handle:
        message += f" and assigned to <@{user_group_handle}>."
    else:
        message += "."
    
    try:
        client.chat_postMessage(
            channel=channel,
            text=message
        )
    except SlackApiError as e:
        logging.error(f"Error sending rotation update message: {e.response['error']}")

### delete
def show_delete_rotation_modal(trigger_id, rotation_name, channel_id=None, thread_ts=None):
    modal_view = get_delete_rotation_modal(rotation_name)

    normalized_rotation_name = get_normalized_rotation_name(rotation_name)
    if channel_id and thread_ts:
        modal_view["private_metadata"] = json.dumps({
            "rotation_id": normalized_rotation_name,
            "rotation_name": rotation_name,
            "channel_id": channel_id,
            "thread_ts": thread_ts
        })
    else:
        modal_view["private_metadata"] = json.dumps({
            "rotation_id": normalized_rotation_name,
            "rotation_name": rotation_name
        })

    try:
        client.views_open(
            trigger_id=trigger_id,
            view=modal_view
        )
    except SlackApiError as e:
        logging.error(f"Error opening modal: {e.response['error']}")
    
    return jsonify({"status": "modal opened"})


def handle_delete_rotation_submission(view_submission_payload):
    private_metadata = json.loads(view_submission_payload["view"]["private_metadata"])
    rotation_id = private_metadata["rotation_id"]
    rotation_name = private_metadata["rotation_name"]
    user_id = view_submission_payload["user"]["id"]
    channel_id = private_metadata.get("channel_id")
    thread_ts = private_metadata.get("thread_ts")

    delete_rotation(rotation_id, rotation_name, channel_id, thread_ts, user_id)
    
    response = jsonify({"response_action": "clear"})
    response.status_code = 200
    
    return response

def delete_rotation(rotation_id, rotation_name, channel_id, thread_ts, user_id):
    rotation_ref = db.collection('rotations').document(rotation_id)
    rotation = rotation_ref.get()
    
    if not rotation.exists:
        send_error_message(user_id, channel_id, thread_ts, f"Rotation *{rotation_name}* does not exist.")
        return

    try:
        rotation_data = rotation.to_dict()
        user_group_id = rotation_data.get('user_group_id')

        # Delete the rotation document from Firestore
        rotation_ref.delete()

        # Delete the user group from Slack if it exists
        if user_group_id:
            try:
                client.usergroups_disable(usergroup=user_group_id)
                logging.info(f"User group {user_group_id} disabled successfully.")
            except SlackApiError as e:
                logging.error(f"Error disabling user group: {e.response['error']}")
                
        send_delete_confirmation_message(channel_id, rotation_name, success=True)
    except Exception as e:
        send_update_confirmation_message(channel_id, rotation_name, success=False, error=str(e))

def send_error_message(user_id, channel_id, thread_ts, error_message):
    if channel_id:
        # Send message as a reply in the thread if channel_id is available
        try:
            client.chat_postMessage(
                channel=channel_id,
                text=f"❌ {error_message}",
                thread_ts=thread_ts
            )
        except SlackApiError as e:
            logging.error(f"Error sending error message: {e.response['error']}")
    else:
        # Send direct message to the user if channel_id is not available
        try:
            client.chat_postMessage(
                channel=user_id,
                text=f"❌ {error_message}",
                timestamp=thread_ts
            )
        except SlackApiError as e:
            logging.error(f"Error sending direct error message: {e.response['error']}")

### notify them button

def handle_notify_button(action_payload):
    rotation_name = action_payload["actions"][0]["value"].replace("notify_", "")
    channel_id = action_payload["channel"]["id"]
    thread_ts = action_payload["message"]["ts"]
    normalized_rotation_name = get_normalized_rotation_name(rotation_name)

    rotation_ref = db.collection('rotations').document(normalized_rotation_name)
    rotation = rotation_ref.get()

    if rotation.exists:
        rotation_data = rotation.to_dict()
        current_on_call = rotation_data.get('current_on_call', 'Nobody')

        if current_on_call != 'Nobody':
            notify_message = f"🔔 Reminder: <@{current_on_call}>, you are currently on call for the *{rotation_name}* rotation."

            try:
                client.chat_postMessage(
                    channel=channel_id,
                    text=notify_message,
                    thread_ts=thread_ts
                )
            except SlackApiError as e:
                logging.error(f"Error sending notify message: {e.response['error']}")
                
    return jsonify({"status": "ok"})

### edit button

def show_edit_rotation_modal(trigger_id, rotation_name, current_channel, selected_users, channel_id=None, thread_ts=None):
    modal_view = get_edit_rotation_modal(rotation_name, current_channel, selected_users)

    if channel_id and thread_ts:
        modal_view["private_metadata"] = json.dumps({
            "rotation_name": rotation_name,
            "channel_id": channel_id,
            "thread_ts": thread_ts
        })
    else:
        modal_view["private_metadata"] = json.dumps({
            "rotation_name": rotation_name
        })

    try:
        client.views_open(
            trigger_id=trigger_id,
            view=modal_view
        )
    except SlackApiError as e:
        logging.error(f"Error opening modal: {e.response['error']}")
    
    return jsonify({"status": "modal opened"})

def handle_edit_rotation_submission(view_submission_payload):
    private_metadata = json.loads(view_submission_payload["view"]["private_metadata"])
    rotation_name = private_metadata["rotation_name"]
    new_channel_id = view_submission_payload["view"]["state"]["values"]["reminder_channel"]["channel_select"]["selected_conversation"]
    selected_users = view_submission_payload["view"]["state"]["values"]["users_in_rotation"]["users_select"]["selected_conversations"]
    
    rotation_id = get_normalized_rotation_name(rotation_name)
    rotation_ref = db.collection('rotations').document(rotation_id)
    rotation = rotation_ref.get()
    
    if not rotation.exists:
        send_error_message(view_submission_payload["user"]["id"], None, None, f"Rotation *{rotation_name}* does not exist.")
        return

    try:
        rotation_ref.update({
            'reminder_channel': new_channel_id,
            'users_in_rotation': selected_users
        })
        send_update_confirmation_message(new_channel_id, rotation_name, success=True)
    except Exception as e:
        send_update_confirmation_message(new_channel_id, rotation_name, success=False, error=str(e))

    response = jsonify({"response_action": "clear"})
    response.status_code = 200
    
    return response

def get_selected_users(rotation_name):
    rotation_id = get_normalized_rotation_name(rotation_name)
    rotation_ref = db.collection('rotations').document(rotation_id)
    rotation = rotation_ref.get()
    
    if rotation.exists:
        rotation_data = rotation.to_dict()
        return rotation_data.get('users_in_rotation', [])

    return []

def get_current_reminder_channel(rotation_name):
    rotation_id = get_normalized_rotation_name(rotation_name)
    rotation_ref = db.collection('rotations').document(rotation_id)
    rotation = rotation_ref.get()
    
    if rotation.exists:
        rotation_data = rotation.to_dict()
        return rotation_data.get('reminder_channel', '')

    return ''

def send_update_confirmation_message(channel, rotation_name, success=True, error=None):
    if success:
        message = f":large_green_circle: Rotation *{rotation_name}* has been updated with the new reminder channel and users! 🥳🎊🎉"
    else:
        message = f":red_circle: *Failed to Update Rotation*\n"
        message += f"Rotation *{rotation_name}* could not be updated.\n"
        message += f"Error: {error}"

    try:
        client.chat_postMessage(
            channel=channel,
            text=message
        )
    except SlackApiError as e:
        logging.error(f"Error sending update confirmation message: {e.response['error']}")
        
def send_delete_confirmation_message(channel, rotation_name, success=True, error=None):
    if success:
        message = f":large_green_circle: Rotation *{rotation_name}* has been deleted successfully! 🎉"
    else:
        message = f":red_circle: *Failed to Delete Rotation*\n"
        message += f"Rotation *{rotation_name}* could not be deleted.\n"
        message += f"Error: {error}"

    try:
        client.chat_postMessage(
            channel=channel,
            text=message
        )
    except SlackApiError as e:
        logging.error(f"Error sending delete confirmation message: {e.response['error']}")
