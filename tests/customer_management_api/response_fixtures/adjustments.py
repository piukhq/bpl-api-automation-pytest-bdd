from tests.shared_utils.response_fixtures.base import BaseResponses

MISSING_OR_INVALID_IDEMPOTENCY_TOKEN_HEADER = {
    "display_message": "Submitted headers are missing or invalid.",
    "code": "HEADER_VALIDATION_ERROR",
    "fields": [
        "idempotency-token",
    ],
}


class AdjustmentsResponses(BaseResponses):
    missing_idempotency_header = MISSING_OR_INVALID_IDEMPOTENCY_TOKEN_HEADER
