pick_team = {
    "blocks": [
        {
            "type": "section",
            "block_id": "list_selection",
            "text": {
                "type": "mrkdwn",
                "text": "Select a list to pick the next member:",
            },
            "accessory": {
                "type": "static_select",
                "placeholder": {"type": "plain_text", "text": "Select a list"},
                "action_id": "pick__select_user",
                "options": [],
            },
        }
    ]
}

list_view_json = {
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Created Lists Overview",
                "emoji": True,
            },
        }
    ]
}

list_view_blocks = [
    {"type": "divider"},
    {"type": "section", "text": {"type": "mrkdwn", "text": "*List One*"}},
    {
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": "@user1, @user2, @user3"}],
    },
    {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "Created by <@tagore.vuyyuru> on Dec 11.\nLast picked by <@tagore.vuyyuru> on Dec 11.",
            }
        ],
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Stats"},
                "value": "stats_list_one",
                "action_id": "stats_list_a_team",
            },
            {
                "type": "button",
                "style": "primary",
                "text": {"type": "plain_text", "text": "Pick"},
                "value": "pick_list_one",
                "action_id": "pick_list_one",
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Manage"},
                "value": "manage_list_one",
                "action_id": "manage_list_one",
            },
            {
                "type": "button",
                "style": "danger",
                "text": {"type": "plain_text", "text": "Delete"},
                "value": "delete_list_one",
                "action_id": "delete_list_one",
                "confirm": {
                    "title": {"type": "plain_text", "text": "Are you sure?"},
                    "text": {
                        "type": "mrkdwn",
                        "text": "This will delete *List One*. Are you sure you want to proceed?",
                    },
                    "confirm": {"type": "plain_text", "text": "Yes, delete it"},
                    "deny": {"type": "plain_text", "text": "Cancel"},
                },
            },
        ],
    },
]


manage_json = {
    "type": "modal",
    "callback_id": "manage_users_modal",
    "title": {"type": "plain_text", "text": "Manage List"},
    "submit": {"type": "plain_text", "text": "Save"},
    "close": {"type": "plain_text", "text": "Cancel"},
    "blocks": [
        {
            "type": "section",
            "block_id": "user_list_section",
            "text": {"type": "mrkdwn", "text": 'Users on "Rotation02"'},
            "accessory": {
                "type": "multi_users_select",
                "action_id": "user_selection",
                "initial_users": ["UJagadeeswarReddy", "Utagore.vuyyuru"],
                "placeholder": {"type": "plain_text", "text": "Select users"},
            },
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "Created by <@tagore.vuyyuru> on Dec 11."},
                {
                    "type": "mrkdwn",
                    "text": "Last picked by <@tagore.vuyyuru> on Dec 11.",
                },
            ],
        },
    ],
}

create_message_json = [
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Create a list of users to pick from."},
        "accessory": {
            "type": "button",
            "text": {"type": "plain_text", "text": "Create list", "emoji": True},
            "value": "create_list",
            "action_id": "create",
        },
    }
]

user_selection_json = {
    "type": "modal",
    "callback_id": "create_list_modal",
    "title": {"type": "plain_text", "text": "Create List", "emoji": True},
    "submit": {"type": "plain_text", "text": "Save", "emoji": True},
    "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
    "blocks": [
        {
            "type": "input",
            "block_id": "list_name_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "name",
                "placeholder": {
                    "type": "plain_text",
                    "text": "e.g., Project Alpha Team",
                    "emoji": True,
                },
            },
            "label": {"type": "plain_text", "text": "Name", "emoji": True},
        },
        {
            "type": "input",
            "block_id": "list_input",
            "element": {
                "type": "multi_users_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select users",
                    "emoji": True,
                },
                "action_id": "multi_users_select_action",
            },
            "label": {"type": "plain_text", "text": "Users", "emoji": True},
        },
    ],
}
