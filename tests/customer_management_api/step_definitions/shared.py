import json
import logging

from tests.customer_management_api.api_requests.base import get_headers
from tests.customer_management_api.api_requests.enrolment import send_post_enrolment
from tests.customer_management_api.payloads.enrolment import (
    all_required_and_all_optional_credentials,
    only_required_credentials,
)


def check_response_status_code(status_code: int, request_context: dict, endpoint: str) -> None:
    resp = request_context["response"]
    logging.info(f"POST {endpoint} response HTTP status code: {resp.status_code}")
    assert resp.status_code == status_code


def enrol_account_holder(retailer_slug: str, request_context: dict, incl_optional_fields: bool = True) -> None:
    request_context["retailer_slug"] = retailer_slug
    if incl_optional_fields:
        request_body = all_required_and_all_optional_credentials()
    else:
        request_body = only_required_credentials()
    resp = send_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp


def non_existent_account_holder(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_context["account_holder_exists"] = False

    class UnsentRequest:
        body = json.dumps(all_required_and_all_optional_credentials())

    class FakeResponse:
        status = 202
        request = UnsentRequest

    request_context["response"] = FakeResponse


def enrol_missing_channel_header(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = all_required_and_all_optional_credentials()
    headers = get_headers()
    headers.pop("bpl-user-channel")
    resp = send_post_enrolment(retailer_slug, request_body, headers=headers)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")
    assert resp.status_code == 400


def enrol_missing_third_party_identifier(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = all_required_and_all_optional_credentials()
    request_body.pop("third_party_identifier")
    resp = send_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")
    assert resp.status_code == 422
