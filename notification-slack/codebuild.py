import json
import os
import logging
import time

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime

# Slack
HOOK_URL      = os.environ['WEBHOOK_URL']
SLACK_CHANNEL = os.environ['CHANNEL']

# Url including Message
CODEBUILD_URL = "https://{0}.console.aws.amazon.com/codebuild/home?{0}#/builds/{1}/view/new"

# Start Message format
SLACK_MESSAGE_TEXT = '''\
*{0}* `{1}` {2}
'''

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

STATE_ICONS = {
    'IN_PROGRESS': ':runner:',
    'FAILED':      ':bow:',
    'SUCCEEDED':   ':nicerun:'
}

STATE_COLORS = {
    'IN_PROGRESS': '#2E64FE',
    'FAILED':      'danger',
    'SUCCEEDED':   'good'
}

def handler(event, context):
    logger.debug("Event: " + str(event))

    # event info
    region   = event["region"]
    date_str = event["time"]
    build_id = event["detail"]["build-id"].split('/')[1]
    project  = event["detail"]["project-name"]
    state    = event["detail"]["build-status"]

    url       = CODEBUILD_URL.format(region, build_id)
    date      = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    unix_time = int(time.mktime(date.timetuple()))

    slack_message = {
        'channel': SLACK_CHANNEL,
        'parse': 'none',
        'attachments': [
            {
                "fallback":    "Code Pipeline attachments",
                "color":       STATE_COLORS.get(state, ''),
                "title":       "CodeBuild",
                "title_link":  url,
                "text": SLACK_MESSAGE_TEXT.format(
                    project,
                    state,
                    STATE_ICONS.get(state, '')),
                "footer":      project,
                "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                "ts":          unix_time
            }
        ]
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

