def get_rotation_blocks(rotations):
    blocks = [
         {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ":gear: *Easily manage your rotations with the options below:*"
        }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Create a new rotation*"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "➕ Create Rotation",
                    "emoji": True
                },
                "value": "create_rotation",
                "action_id": "create_rotation_button",
                "style": "primary"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Channel Rotations:*"
            }
        }
    ]

    if not rotations['channel_rotations']:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "😞 No rotations are configured in this channel."
            }
        })
    else:
        for rotation in rotations['channel_rotations']:
            current_on_call = rotation['current_on_call']
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f":repeat: *{rotation['name']}*\nCurrently on call: <@{current_on_call}>"
                    }
                ]
            })
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔔 Notify",
                            "emoji": True
                        },
                        "value": f"notify_{rotation['name']}",
                        "action_id": "notify_button"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔄 Next Pick",
                            "emoji": True
                        },
                        "value": f"next_pick_{rotation['name']}",
                        "action_id": "next_pick_button"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✏️ Edit",
                            "emoji": True
                        },
                        "value": f"edit_{rotation['name']}",
                        "action_id": "edit_rotation_button"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ Delete",
                            "emoji": True
                        },
                        "value": f"delete_{rotation['name']}",
                        "action_id": "delete_rotation_button"
                    }
                ]
            })

    if rotations['other_rotations']:
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Other Rotations:*"
            }
        })

        for rotation in rotations['other_rotations']:
            current_on_call = rotation['current_on_call']
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f":repeat: *{rotation['name']}*\nCurrently on call: <@{current_on_call}>"
                    }
                ]
            })
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔔 Notify",
                            "emoji": True
                        },
                        "value": f"notify_{rotation['name']}",
                        "action_id": "notify_button"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔄 Next Pick",
                            "emoji": True
                        },
                        "value": f"next_pick_{rotation['name']}",
                        "action_id": "next_pick_button"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✏️ Edit",
                            "emoji": True
                        },
                        "value": f"edit_{rotation['name']}",
                        "action_id": "edit_rotation_button"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ Delete",
                            "emoji": True
                        },
                        "value": f"delete_{rotation['name']}",
                        "action_id": "delete_rotation_button"
                    }
                ]
            })

    return blocks



def get_create_rotation_modal():
    return {
        "type": "modal",
        "callback_id": "create_rotation",
        "title": {
            "type": "plain_text",
            "text": "Create Rotation",
            "emoji": True
        },
        "submit": {
            "type": "plain_text",
            "text": "Create",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "Close",
            "emoji": True
        },
        "blocks": [
            {
                "type": "input",
                "block_id": "rotation_name",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "rotation_name_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "e.g. Catalog Hero"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Rotation name",
                    "emoji": True
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "_Rotation names are case insensitive._"
                    }
                ]
            },
            {
                "type": "section",
                "block_id": "create_user_group_toggle",
                "text": {
                    "type": "mrkdwn",
                    "text": "*User group*\nWould you like to automatically create a user group (e.g., @catalog-hero) to easily mention the person on call?"
                },
                "accessory": {
                    "type": "radio_buttons",
                    "initial_option": {
                        "text": {
                            "type": "plain_text",
                            "text": "Yes",
                            "emoji": True
                        },
                        "value": "yes"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Yes",
                                "emoji": True
                            },
                            "value": "yes"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "No",
                                "emoji": True
                            },
                            "value": "no"
                        }
                    ],
                    "action_id": "create_user_group_radio"
                }
            },
            {
                "type": "input",
                "block_id": "users_in_rotation",
                "element": {
                    "type": "multi_conversations_select",
                    "action_id": "users_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select users"
                    },
                    "filter": {
                        "include": ["im"],
                        "exclude_external_shared_channels": True,
                        "exclude_bot_users": True
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "The users to include in the rotation",
                    "emoji": True
                },
                "optional": False
            },
            {
                "type": "input",
                "block_id": "reminder_channel",
                "element": {
                    "type": "conversations_select",
                    "action_id": "channel_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a channel"
                    },
                    "filter": {
                        "include": ["public", "private"]
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "The reminder channel",
                    "emoji": True
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "_For *private* channels, make sure you add App as a member._"
                    }
                ]
            }
        ]
    }

def get_delete_rotation_modal(rotation_name):
    return {
        "type": "modal",
        "callback_id": "confirm_delete_rotation",
        "title": {
            "type": "plain_text",
            "text": "Confirm Deletion",
            "emoji": True
        },
        "submit": {
            "type": "plain_text",
            "text": "Delete",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Are you sure you want to delete the rotation *{rotation_name}*?"
                }
            }
        ]
    }

def get_edit_rotation_modal(rotation_name, current_channel, selected_users):
    return {
        "type": "modal",
        "callback_id": "confirm_edit_rotation",
        "title": {
            "type": "plain_text",
            "text": "Edit Rotation",
            "emoji": True
        },
        "submit": {
            "type": "plain_text",
            "text": "Update",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Editing rotation *{rotation_name}*"
                }
            },
            {
                "type": "input",
                "block_id": "reminder_channel",
                "element": {
                    "type": "conversations_select",
                    "action_id": "channel_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a channel"
                    },
                    "default_to_current_conversation": True,
                    "initial_conversation": current_channel,
                    "filter": {
                        "include": ["public", "private"]
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Reminder Channel",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "block_id": "users_in_rotation",
                "element": {
                    "type": "multi_conversations_select",
                    "action_id": "users_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select users"
                    },
                    "filter": {
                        "include": ["im"],
                        "exclude_external_shared_channels": True,
                        "exclude_bot_users": True
                    },
                    "initial_conversations": selected_users
                },
                "label": {
                    "type": "plain_text",
                    "text": "The users to include in the rotation",
                    "emoji": True
                },
                "optional": False
            }
        ]
    }

def get_welcome_message_blocks(user_id):
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Hey <@{user_id}>! :wave:\n\nI'm thrilled to be your rotation app! :tada:\n\nTo get started quickly, press the button below to create your first rotation:"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "➕ Create a rotation",
                        "emoji": True
                    },
                    "value": "create_rotation",
                    "action_id": "create_rotation_button",
                    "style": "primary"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":bulb: You can manage your rotations, create new ones, and update existing rotations by mentioning this app. For example, to rotate a user, you can mention the app followed by 'rotate [rotation_name]'."
            }
        },
        {
            "type": "image",
            "image_url": "https://github.com/tagorenathv/slack-shift-roster/blob/master/gcp/user-group-recommended-settings.png",
            "alt_text": "user groups recommended settings",
            "title": {
                "type": "plain_text",
                "text": "Recommended Settings"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":information_source: *Tip:* Rotation App uses Slack's User Group feature to create an @mention for every rotation. Please make sure you have it enabled for everyone in the [workspace settings](https://slack.com/help/articles/212906697-Create-and-manage-user-groups)."
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":email: If you have any questions or feedback, feel free to reach out [here](https://github.com/tagorenathv/slack-shift-roster/issues). Have fun!"
            }
        }
    ]

