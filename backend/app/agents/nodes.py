from app.agents.model import llm
from app.agents.schemas import RecoveryDecision
from app.agents.state import RecoveryState
from app.services.policy import validate_recovery

diagnosis_prompt = """
You are a payment recovery analyst.

Analyze the failed payment below.

Determine:
1. The likely reason the payment failed.
2. Whether the failure is potentially recoverable.
3. What evidence supports your conclusion.

Payment:
{payment}

Return a concise operational diagnosis.
"""


def diagnose(state: RecoveryState) -> RecoveryState:

    payment = state["payment"]

    response = llm.invoke(
        diagnosis_prompt.format(
            payment=payment.model_dump_json()
        )
    )

    return {
        "diagnosis": response.content
    }


decision_llm = llm.with_structured_output(
    RecoveryDecision
)


decision_prompt = """
You are a payment recovery decision agent.

Based on the payment information and diagnosis,
select ONE recovery action.

Allowed actions:

- retry
- payment_link
- reminder
- escalate
- no_action

Rules:

- Transient/network failures are usually suitable for retry.
- Customer abandonment may justify a payment link.
- Bank declines should generally not be blindly retried.
- Unknown failures should be escalated.
- Never invent a payment action outside the allowed list.

Payment:
{payment}

Diagnosis:
{diagnosis}
"""


def choose_recovery(state: RecoveryState) -> RecoveryState:

    decision = decision_llm.invoke(
        decision_prompt.format(
            payment=state["payment"].model_dump_json(),
            diagnosis=state["diagnosis"],
        )
    )

    return {
        "decision": decision
    }


def policy_check(state: RecoveryState) -> RecoveryState:

    result = validate_recovery(
        payment=state["payment"],
        decision=state["decision"],
    )

    return {
        "policy_allowed": result.allowed,
        "requires_approval": result.requires_approval,
        "policy_reason": result.reason,
    }