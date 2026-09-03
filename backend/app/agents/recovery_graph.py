from app.agents.nodes import (
    choose_recovery,
    diagnose,
    policy_check,
)
from app.agents.state import RecoveryState
from app.services.recovery import execute_recovery
from langgraph.graph import END, START, StateGraph


def route_after_policy(state: RecoveryState):

    if state["requires_approval"]:
        return "approval"

    if not state["policy_allowed"]:
        return "blocked"

    return "execute"


def blocked(state: RecoveryState) -> RecoveryState:

    return {
        "execution_success": False,
        "execution_message": (f"Recovery blocked: {state['policy_reason']}"),
    }


def approval(state: RecoveryState) -> RecoveryState:

    return {
        "execution_success": False,
        "execution_message": (f"Human approval required: {state['policy_reason']}"),
    }


def execute(state: RecoveryState) -> RecoveryState:

    result = execute_recovery(
        payment=state["payment"],
        action=state["decision"].action,
    )

    return {
        "execution_success": result["success"],
        "execution_message": result["message"],
        "recovered_amount": result["recovered_amount"],
    }


def build_recovery_graph():

    graph = StateGraph(RecoveryState)

    graph.add_node("diagnose", diagnose)
    graph.add_node("choose_recovery", choose_recovery)
    graph.add_node("policy_check", policy_check)
    graph.add_node("execute", execute)
    graph.add_node("blocked", blocked)
    graph.add_node("approval", approval)

    graph.add_edge(START, "diagnose")
    graph.add_edge("diagnose", "choose_recovery")
    graph.add_edge("choose_recovery", "policy_check")

    graph.add_conditional_edges(
        "policy_check",
        route_after_policy,
        {
            "execute": "execute",
            "blocked": "blocked",
            "approval": "approval",
        },
    )

    graph.add_edge("execute", END)
    graph.add_edge("blocked", END)
    graph.add_edge("approval", END)

    return graph.compile()
