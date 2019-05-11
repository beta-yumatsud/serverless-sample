import json
import os
import logging

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Slack
HOOK_URL      = os.environ['WEBHOOK_URL']
SLACK_CHANNEL = os.environ['CHANNEL']

# Url including Message
TASK_URL               = "https://{0}.console.aws.amazon.com/ecs/home?region={0}#/clusters/{1}/tasks/{2}/details"
TASK_DEFINITION_URL    = "https://{0}.console.aws.amazon.com/ecs/home?region={0}#/taskDefinitions/{1}"

# Start Message format
SLACK_MESSAGE_TEXT = '''\
*{0}* `{1}` {2} <{3}|Task> ( _<{4}|{5}>_ )
'''

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

STATE_ICONS = {
    'RUNNING': ':runner:',
    'STOPPED': ':bow:',
}

def handler(event, context):
    logger.debug("Event: " + str(event))

    # event info
    region                = event["region"]
    cluster_id            = event["detail"]["clusterArn"].split('/')[1]
    task_id               = event["detail"]["taskArn"].split('/')[1]
    task_definition_id    = event["detail"]["taskDefinitionArn"].split('/')[1]
    desired_status        = event["detail"]["desiredStatus"]
    last_status           = event["detail"]["lastStatus"]

    task_url               = TASK_URL.format(region, cluster_id, task_id)
    task_definition_url    = TASK_DEFINITION_URL.format(region, task_definition_id.replace(':', '/'))

    if desired_status != last_status:
        return

    slack_message = {
        'channel': SLACK_CHANNEL,
        'text': SLACK_MESSAGE_TEXT.format(
            cluster_id,
            last_status,
            STATE_ICONS.get(last_status, ''),
            task_url,
            task_definition_url,
            task_definition_id),
        'parse': 'none'
    }

    req = Request(HOOK_URL, json.dumps(slack_message).encode('utf-8'))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to %s", slack_message['channel'])
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)

