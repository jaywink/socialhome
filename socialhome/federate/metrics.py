from prometheus_client import Summary

TASK_TIME = Summary(
    "socialhome_federate_tasks_processing_seconds",
    "Time spent processing a task",
    ("task",),
)
TASK_TIME_FORWARD_ENTITY = TASK_TIME.labels("forward_entity")
TASK_TIME_RECEIVE_TASK = TASK_TIME.labels("receive_task")
TASK_TIME_SEND_CONTENT = TASK_TIME.labels("send_content")
TASK_TIME_SEND_CONTENT_RETRACTION = TASK_TIME.labels("send_content_retraction")
TASK_TIME_SEND_FOLLOW_CHANGE = TASK_TIME.labels("send_follow_change")
TASK_TIME_SEND_PROFILE = TASK_TIME.labels("send_profile")
TASK_TIME_SEND_PROFILE_RETRACTION = TASK_TIME.labels("send_profile_retraction")
TASK_TIME_SEND_REPLY = TASK_TIME.labels("send_reply")
TASK_TIME_SEND_SHARE = TASK_TIME.labels("send_share")
