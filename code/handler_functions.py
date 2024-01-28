import datetime
import json
import uuid
from block_json import (
    pick_team,
    list_view_json,
    user_selection_json,
    list_view_blocks,
    manage_json,
    create_message_json,
)
from app_config import client, logger
from copy import deepcopy
from dynamodb_utils import (
    get_shift_rosters,
    add_shift_roster,
    get_shift_roster,
    update_shift_roster,
    delete_shift_roster,
    get_shift_rosters,
)


def pick_view(channel_id):
    response = get_shift_rosters(channel_id)
    if response and response.get("Items"):
        retrieved_items = response["Items"]
        options = [
            {
                "text": {"type": "plain_text", "text": item.get("team_name")},
                "value": item.get("id"),
            }
            for item in retrieved_items
        ]

        if options:
            pick_team["blocks"][0]["accessory"]["options"] = options
            client.chat_postMessage(
                channel=channel_id,
                text="Pick A Roaster",
                blocks=json.dumps(pick_team["blocks"]),
            )
    else:
        logger.info("No shift rosters found for channel: %s", channel_id)
        client.chat_postMessage(
            channel=channel_id, text="No shift rosters found for channel."
        )
    return


def list_view(channel_id):
    response = get_shift_rosters(channel_id)
    # Check if "Items" key exists and it is not empty
    if response.get("Items"):
        retrieved_items = response["Items"]
        all_blocks = []  # Initialize an empty list to collect all blocks

        for item in retrieved_items:
            # Simplify user formatting using list comprehension
            users = item.get("team_members", [])
            converted_users = ", ".join(f"<@{user}>" for user in users)

            # Assume each block needs to be uniquely built per team
            team_block = deepcopy(
                list_view_blocks
            )  # Make a copy of the template blocks

            # Assign values to specific locations in the block
            team_block[1]["text"]["text"] = item.get("team_name", "No Name")
            team_block[2]["elements"][0]["text"] = converted_users
            team_block[3]["elements"][0][
                "text"
            ] = f"Created by <@{item.get('created_user')}>"

            # Assign action ids
            actions = ["stats", "pick", "manage", "delete"]
            for i, action in enumerate(actions):
                team_block[4]["elements"][i][
                    "action_id"
                ] = f"{action}__{item.get('id')}"

            all_blocks.extend(
                team_block
            )  # Add the constructed team block to all_blocks

        # Copy the base structure once and update its blocks
        view_payload = deepcopy(list_view_json)
        view_payload["blocks"].extend(all_blocks)

        client.chat_postMessage(
            channel=channel_id,
            text="List Overview",
            blocks=json.dumps(view_payload["blocks"]),
        )
    else:
        # Send a message if there are no items in the database.
        client.chat_postMessage(channel=channel_id, text="No shift rosters available.")

    return


def create_view(channel_id, trigger_id):
    if not trigger_id:
        logger.warning("Trigger ID is missing. Cannot open view.")
        return

    user_selection_json_copy = deepcopy(user_selection_json)
    user_selection_json_copy["private_metadata"] = channel_id
    client.views_open(trigger_id=trigger_id, view=json.dumps(user_selection_json_copy))

    return


def app_home_opened():
    print("---app_home_opened---")
    return {"statusCode": 200}


##


def pick(table_id, channel_id, _, message_ts):
    res = get_shift_roster(table_id)

    if "Item" in res:
        current_index = int(res["Item"].get("current_index"))
        team_members = res["Item"].get("team_members")
        if current_index + 1 < len(team_members):
            index = current_index + 1
        else:
            index = 0
        selected_member = team_members[index]
        if res["Item"].get("stats").get(selected_member):
            selected_count = res["Item"].get("stats").get(selected_member) + 1
        else:
            selected_count = 1

        update_shift_roster(table_id, selected_member, index, selected_count)

        client.chat_delete(channel=channel_id, ts=message_ts)
        client.chat_postMessage(
            channel=channel_id, text=f"<@{selected_member}> you are selected"
        )

    else:
        client.chat_delete(channel=channel_id, ts=message_ts)
        client.chat_postMessage(channel=channel_id, text="Roster/Members not found")
    return


def stats(table_id, channel_id, _, message_ts):
    res = get_shift_roster(table_id)
    client.chat_delete(channel=channel_id, ts=message_ts)
    if "Item" in res:
        team_members = res["Item"].get("team_members")
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "Position | Picks | @User",
                    "emoji": True,
                },
            }
        ]
        for i, j in enumerate(team_members):
            picks = res["Item"].get("stats").get(j)
            if picks:
                blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"{i+1} | {picks} | <@{j}>"},
                    }
                )

    client.chat_postMessage(channel=channel_id, text="stats", blocks=json.dumps(blocks))

    return


def manage(table_id, channel_id, trigger_id, message_ts):
    res = get_shift_roster(table_id)
    client.chat_delete(channel=channel_id, ts=message_ts)
    manage_json_copy = deepcopy(manage_json)
    if "Item" in res:
        team_id = res["Item"].get("id")
        team_name = res["Item"].get("team_name")
        team_members = res["Item"].get("team_members")
        created_by = res["Item"].get("created_user")
        current_index = int(res["Item"].get("current_index"))
        picked_user = res["Item"].get("team_members")[current_index]
        create_time = datetime.utcfromtimestamp(
            int(res["Item"].get("created_ts")) / 1000
        ).strftime("%b %d")
        updated_time = datetime.utcfromtimestamp(
            int(res["Item"].get("updated_ts")) / 1000
        ).strftime("%b %d")
        manage_json_copy["callback_id"] = f"manage_users_modal__{team_id}"
        manage_json_copy["blocks"][0]["text"]["text"] = f"Users on {team_name}"
        manage_json_copy["blocks"][0]["accessory"]["initial_users"] = [
            i for i in team_members
        ]
        manage_json_copy["blocks"][1]["elements"][0][
            "text"
        ] = f"Created by <@{created_by}> on {create_time}."
        manage_json_copy["blocks"][1]["elements"][1][
            "text"
        ] = f"<@{picked_user}> picked on {updated_time}"

    client.views_open(trigger_id=trigger_id, view=json.dumps(manage_json_copy))

    return


def delete(table_id, channel_id, _, message_ts):
    delete_shift_roster(table_id)
    client.chat_delete(channel=channel_id, ts=message_ts)
    return


def create_list(payload):
    team_name = (
        payload.get("view")
        .get("state")
        .get("values")
        .get("list_name_input")
        .get("name")
        .get("value")
    )
    team_members = (
        payload.get("view")
        .get("state")
        .get("values")
        .get("list_input")
        .get("multi_users_select_action")
        .get("selected_users")
    )
    user_id = payload.get("user").get("id")
    team_id = payload.get("team").get("id")
    trigger_id = payload.get("trigger_id")
    timestamp = int(trigger_id.split(".")[0])
    channel_id = payload.get("view").get("private_metadata")

    item = {
        "id": str(uuid.uuid4()),
        "team_name": team_name,
        "team_members": team_members,
        "created_user": user_id,
        "created_team": team_id,
        "channel_id": channel_id,
        "current_index": -1,
        "created_ts": timestamp,
        "updated_ts": timestamp,
        "stats": {},
    }

    add_shift_roster(item)

    return


def update_users(payload):
    # todo: finish
    return


def create_message(channel_id):
    client.chat_postMessage(
        channel=channel_id, text="create list", blocks=json.dumps(create_message_json)
    )
    return


def help_message(channel_id):
    # todo: need to finish this
    client.chat_postMessage(channel=channel_id, text="cult help message here")
    return
