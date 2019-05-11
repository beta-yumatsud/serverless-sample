import json
import os
import logging

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Slack
HOOK_URL      = os.environ['WEBHOOK_URL']
SLACK_CHANNEL = os.environ['CHANNEL']

# Url including Message
CODEBUILD_URL = "https://{0}.console.aws.amazon.com/codebuild/home?{0}#/builds/{1}/view/new"

# Start Message format
SLACK_MESSAGE_TEXT = '''\
*{0}* `{1}` {2} <{3}|CodeBuild>
'''

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

STATE_ICONS = {
    'IN_PROGRESS': ':runner:',
    'FAILED': ':bow:',
    'SUCCEEDED': ':nicerun:'
}

def handler(event, context):
    logger.debug("Event: " + str(event))

    # event info
    region   = event["region"]
    build_id = event["detail"]["build-id"].split('/')[1]
    project  = event["detail"]["project-name"]
    state    = event["detail"]["build-status"]

    url = CODEBUILD_URL.format(region, build_id)

    slack_message = {
        'channel': SLACK_CHANNEL,
        'text': SLACK_MESSAGE_TEXT.format(
            project,
            state,
            STATE_ICONS.get(state, ''),
            url),
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

