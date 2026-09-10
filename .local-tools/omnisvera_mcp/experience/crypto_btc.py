"""BTC direction Beta-Bernoulli updater; no market calls or writes."""
from .updater import ExperienceUpdateResult

PREDICTOR_ID = "crypto.btc.direction"
SCHEMA = "btc.direction.v1"


def direction_state(up_count, down_count):
    if any(type(n) is not int or n < 0 for n in (up_count, down_count)):
        raise ValueError("direction counts must be nonnegative integers")
    return dict(up_count=up_count, down_count=down_count,
                observations_used=up_count + down_count,
                p_up=(up_count + 1) / (up_count + down_count + 2))


class CryptoBtcDirectionUpdater:
    def describe(self):
        return dict(predictor_id=PREDICTOR_ID, predictor_version="v1",
                    predictor_type="statistical", description="BTC/USD direction frequency",
                    update_order_semantics="order_independent")

    def update(self, *, previous_experience, prediction, resolution, context=None):
        if not previous_experience or previous_experience.get("learned_state_schema") != SCHEMA:
            raise ValueError("btc.direction.v1 experience required")
        previous = previous_experience["learned_state"]
        if previous != direction_state(previous["up_count"], previous["down_count"]):
            raise ValueError("inconsistent direction state")
        outcome = resolution.get("outcome")
        if type(outcome) is not int or outcome not in (0, 1):
            raise ValueError("binary outcome required")
        state = direction_state(previous["up_count"] + outcome,
                                previous["down_count"] + 1 - outcome)
        return ExperienceUpdateResult(learned_state_schema=SCHEMA, learned_state=state,
                                      update_summary="Added one resolved BTC/USD direction")
