from boto3.dynamodb.conditions import Attr
from app_config import shift_rosters_table


def get_shift_rosters(channel_id):
    teams = shift_rosters_table.scan(FilterExpression=Attr("channel_id").eq(channel_id))
    return teams


def add_shift_roster(item):
    shift_rosters_table.put_item(Item=item)
    return True


def get_shift_roster(shift_roster_id):
    team = shift_rosters_table.get_item(Key={"id": shift_roster_id})
    return team


def update_shift_roster(shift_roster_id, selected_member, index, selected_count):
    shift_rosters_table.update_item(
        Key={"id": shift_roster_id},
        UpdateExpression=f"SET current_index = :index, stats.{selected_member} = :count",
        ExpressionAttributeValues={":index": index, ":count": selected_count},
    )
    return True


def delete_shift_roster(table_id):
    shift_rosters_table.delete_item(Key={"id": table_id})
    return True
