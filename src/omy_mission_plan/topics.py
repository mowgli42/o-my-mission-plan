"""Redis ASB topic names for mission-plan messages.

Keep strings here. Aligns with o-my ``uci_common.topics`` for shared bus topics.
New plan-lifecycle topics are the contract this repo introduces.
"""

# Existing o-my / o-my-sim topics this planner produces or consumes
TOPIC_PLATFORM_STATUS = "uci.platform.status"
TOPIC_PLATFORM_ROUTE = "uci.platform.route"
TOPIC_TASK = "uci.task"
TOPIC_TASK_STATUS = "uci.task.status"
TOPIC_ENTITY = "uci.entity"
TOPIC_THREAT_NOTIFICATION = "uci.threat.notification"
TOPIC_OMS_STATE = "uci.oms.state"
TOPIC_ROUTE_THREAT = "uci.route.threat"
TOPIC_SCENARIO_EVENT = "uci.scenario.event"

# UCI 2.5 *Plan lifecycle (Tier B UCI-Lite bodies, catalog element names)
TOPIC_MISSION_PLAN = "uci.mission.plan"
TOPIC_MISSION_PLAN_COMMAND = "uci.mission.plan.command"
TOPIC_MISSION_PLAN_STATUS = "uci.mission.plan.status"
TOPIC_MISSION_PLAN_ACTIVATION = "uci.mission.plan.activation"
TOPIC_MISSION_PLAN_ACTIVATION_STATUS = "uci.mission.plan.activation.status"
TOPIC_MISSION_PLAN_EXECUTION = "uci.mission.plan.execution"
TOPIC_ROUTE_PLAN = "uci.route.plan"
TOPIC_TASK_PLAN = "uci.task.plan"
TOPIC_ROUTE_ACTIVITY_PLAN = "uci.route.activity.plan"
TOPIC_TASK_COMMAND = "uci.task.command"
TOPIC_TASK_CANCEL = "uci.task.cancel"
TOPIC_ROUTE_MODIFICATION = "uci.route.modification"

PLAN_PUBLISH_TOPICS = [
    TOPIC_MISSION_PLAN,
    TOPIC_ROUTE_PLAN,
    TOPIC_TASK_PLAN,
    TOPIC_ROUTE_ACTIVITY_PLAN,
    TOPIC_MISSION_PLAN_STATUS,
]

EXECUTION_FEEDBACK_TOPICS = [
    TOPIC_MISSION_PLAN_EXECUTION,
    TOPIC_MISSION_PLAN_ACTIVATION_STATUS,
    TOPIC_TASK_STATUS,
    TOPIC_PLATFORM_STATUS,
    TOPIC_THREAT_NOTIFICATION,
]
