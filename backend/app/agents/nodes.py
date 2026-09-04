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
- Customer-action or abandoned-checkout failures can use payment_link or reminder.
- Transient/network failures may use retry, subject to policy.
- Bank declines should generally not be blindly retried.
- Recurring/subscription (mandate) failures should prefer mandate_retry over a blind retry.
- Use voice_call only when lower-touch channels (reminder, payment_link) have already
  been attempted without success (see attempt_count) and the amount justifies it.
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
