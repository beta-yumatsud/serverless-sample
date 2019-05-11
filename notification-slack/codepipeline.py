import json
import os
import boto3
import logging
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime

# Slack
HOOK_URL      = os.environ['WEBHOOK_URL']
SLACK_CHANNEL = os.environ['CHANNEL']

# Url including Message
CODEPIPELINE_URL = "https://{0}.console.aws.amazon.com/codepipeline/home?region={0}#/view/{1}"
GITHUB_URL       = "https://github.com/{0}/{1}/tree/{2}"
CODEBUILD_URL    = "https://{0}.console.aws.amazon.com/codebuild/home?region={0}#/projects/{1}/view"
ECS_URL          = "https://{0}.console.aws.amazon.com/ecs/home?region={0}#/clusters/{1}/services/{2}/details"

# Start Message format
SLACK_START_MESSAGE_FORMAT = '''\
*{0}* `{1}` {2}
```execution_id: {3}```
{4}
'''

SLACK_FAILED_MESSAGE_FORMAT = '''\
*{0}* _{1}_ `{2}` {3}
```execution_id: {4}```
'''

SLACK_SUCCESS_MESSAGE_FORMAT = '''\
*{0}* `{1}` {2}
```execution_id: {3}```
'''

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

STATE_ICONS = {
    'STARTED': ':runner:',
    'FAILED': ':bow:',
    'SUCCEEDED': ':nicerun:'
}

STATE_COLORS = {
    'STARTED': '#2E64FE',
    'FAILED': 'danger',
    'SUCCEEDED': 'good'
}

def handler(event, context):
    logger.debug("Event: " + str(event))

    # event info
    region       = event["region"]
    date_str     = event["time"]
    pipeline     = event["detail"]["pipeline"]
    version      = event["detail"]["version"]
    execution_id = event["detail"]["execution-id"]
    state        = event["detail"]["state"]
    stage        = event["detail"]["stage"]

    url       = CODEPIPELINE_URL.format(region, pipeline)
    date      = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    unix_time = int(time.mktime(date.timetuple()))

    if state == 'STARTED' and stage == 'Source':
        detail = pipeline_details(pipeline, version, region)
        text = SLACK_START_MESSAGE_FORMAT.format(
            pipeline,
            state,
            STATE_ICONS.get(state, ''),
            execution_id,
            detail)
    elif state == 'FAILED':
        text = SLACK_FAILED_MESSAGE_FORMAT.format(
            pipeline,
            stage,
            state,
            STATE_ICONS.get(state, ''),
            execution_id)
    elif state == 'SUCCEEDED' and stage == 'Deploy':
        text = SLACK_SUCCESS_MESSAGE_FORMAT.format(
            pipeline,
            state,
            STATE_ICONS.get(state, ''),
            execution_id)
    else:
        return

    slack_message = {
        'channel': SLACK_CHANNEL,
        'parse':  'none',
        'attachments': [
            {
                "fallback":    "Code Pipeline attachments",
                "color":       STATE_COLORS.get(state, ''),
                "title":       "CodePipeline",
                "title_link":  url,
                "text":        text,
                "footer":      pipeline,
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


def pipeline_details(name, version, region):
    codepipeline = boto3.client('codepipeline').get_pipeline(
        name = name, version = int(version))
    logger.debug("get-pipeline: " + str(codepipeline))
    stages = []
    for stage in codepipeline['pipeline']['stages']:
        actions = []
        for action in stage["actions"]:
            provider = action["actionTypeId"]["provider"]
            if provider == 'GitHub':
                action_url = GITHUB_URL.format(
                    action["configuration"]["Owner"],
                    action["configuration"]["Repo"],
                    action["configuration"]["Branch"])
                actions.append(":octocat: <{0}|{1}>".format(
                    action_url, provider))
            elif provider == 'CodeBuild':
                action_url = CODEBUILD_URL.format(
                    region,
                    action["configuration"]["ProjectName"])
                actions.append(":codebuild: <{0}|{1}>".format(
                    action_url, provider))
            elif provider == 'ECS':
                action_url = ECS_URL.format(
                    region,
                    action["configuration"]["ClusterName"],
                    action["configuration"]["ServiceName"])
                actions.append(":ecs: <{0}|{1}>".format(
                    action_url, provider))
            else:
                actions.append(provider)
        stages.append("_{0}_ ( {1} )".format(stage["name"], ' | '.join(actions)))

    return ' => '.join(stages)