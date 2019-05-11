import json
import os
import boto3
import logging

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

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
*{0}* `{1}` {3} <{2}|CodePipeline>
```execution_id: {4}```
{5}
'''

SLACK_FAILED_MESSAGE_FORMAT = '''\
*{0}* _{1}_ `{2}` {3} <{4}|CodePipeline>
```execution_id: {5}```
'''

# Message format
SLACK_MESSAGE_TEXT = '''\
*{0}* _{1}_ `{2}` {3} <{4}|CodePipeline>
'''

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

STATE_ICONS = {
    'STARTED': ':runner:',
    'FAILED': ':bow:',
    'SUCCEEDED': ':nicerun:'
}

def handler(event, context):
    logger.debug("Event: " + str(event))

    # event info
    region       = event["region"]
    pipeline     = event["detail"]["pipeline"]
    version      = event["detail"]["version"]
    execution_id = event["detail"]["execution-id"]
    state        = event["detail"]["state"]
    stage        = event["detail"]["stage"]

    url    = CODEPIPELINE_URL.format(region, pipeline)
    if state == 'STARTED' and stage == 'Source':
        detail = pipeline_details(pipeline, version, region)
        slack_message = {
            'channel': SLACK_CHANNEL,
            'text': SLACK_START_MESSAGE_FORMAT.format(
                pipeline,
                state,
                url,
                STATE_ICONS.get(state, ''),
                execution_id,
                detail),
            'parse': 'none'
        }
    elif state == 'FAILED':
        slack_message = {
            'channel': SLACK_CHANNEL,
            'text': SLACK_FAILED_MESSAGE_FORMAT.format(
                pipeline,
                stage,
                state,
                STATE_ICONS.get(state, ''),
                url,
                execution_id),
            'parse': 'none'
        }
    else:
        slack_message = {
            'channel': SLACK_CHANNEL,
            'text': SLACK_MESSAGE_TEXT.format(
                pipeline,
                stage,
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