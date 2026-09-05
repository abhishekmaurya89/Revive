from app.agents.model import llm
from app.agents.schemas import Diagnosis, RecoveryDecision
from app.agents.state import RecoveryState
from app.services.policy import validate_recovery


diagnosis_llm = llm.with_structured_output(Diagnosis)

diagnosis_prompt = """
You are a payment recovery analyst for a payment operations platform.

Analyze this failed payment. Use only the supplied payment data.
Do not invent gateway errors or customer behavior that is not supported by the data.

Determine:
1. The most likely reason for failure.
2. Whether recovery is potentially appropriate.
3. Evidence from the fields provided.

Payment:
{payment}
"""


decision_llm = llm.with_structured_output(RecoveryDecision)

decision_prompt = """
You are a payment recovery decision agent.

Select exactly one action from:
retry, payment_link, reminder, mandate_retry, voice_call, escalate, no_action.

Rules:
- Only payment_link is currently connected to an external execution provider.
- Customer-action or abandoned-checkout failures should choose payment_link when
    policy may allow recovery; do not choose reminder for an automated case.
- Transient/network failures may use retry, subject to policy.
- Bank declines should generally not be blindly retried.
- Recurring/subscription failures should use a payment_link fallback because
    mandate retry is not connected to an external provider in this service.
- Use voice_call only as a recommendation for human review; it is not automated.
- Unknown failures should use escalate.
- If evidence is insufficient, prefer escalate.

Payment:
{payment}

Diagnosis:
{diagnosis}
"""


def diagnose(state: RecoveryState) -> RecoveryState:
    payment = state["payment"]
    diagnosis = diagnosis_llm.invoke(
        diagnosis_prompt.format(payment=payment.model_dump_json())
    )
    return {"diagnosis": diagnosis}


def choose_recovery(state: RecoveryState) -> RecoveryState:
    decision = decision_llm.invoke(
        decision_prompt.format(
            payment=state["payment"].model_dump_json(),
            diagnosis=state["diagnosis"].model_dump_json(),
        )
    )
    return {"decision": decision}


def policy_check(state: RecoveryState) -> RecoveryState:
    result = validate_recovery(
        payment=state["payment"],
        decision=state["decision"],
    )
    return {
        "policy_allowed": result.allowed,
        "requires_approval": result.requires_approval,
        "policy_reason": result.reason,
        "stopped": result.stopped,
    }
