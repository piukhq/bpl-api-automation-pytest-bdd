import json
import logging
import random
import string
import uuid

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse

from settings import POLARIS_BASE_URL
from tests.customer_management_api.api_requests.accounts_vouchers import send_post_accounts_voucher
from tests.customer_management_api.db_actions.account_holder import get_account_holder_voucher
from tests.customer_management_api.response_fixtures.vouchers import VoucherResponses

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# fmt: off
@when(parse("I POST a voucher expiring in the {past_or_future} for a {retailer_slug} account holder with a {token_validity} auth token"))  # noqa: E501
@given(parse("I POST a voucher expiring in the {past_or_future} for a {retailer_slug} account holder with a {token_validity} auth token"))  # noqa: E501
# fmt: on
def post_voucher(past_or_future: str, retailer_slug: str, token_validity: str, request_context: dict) -> None:
    if "account_holder" in request_context:
        account_holder_uuid = request_context["account_holder"].account_holder_uuid
    else:
        account_holder_uuid = str(uuid.uuid4())

    request_context["voucher_id"] = str(uuid.uuid4())

    payload = {
        "code": "".join(random.choice(string.ascii_lowercase) for i in range(10)),
        "issued_date": datetime.utcnow().timestamp(),
        "expiry_date": (datetime.utcnow() + timedelta(days=-7 if past_or_future == "past" else 7)).timestamp(),
        "status": "issued",
        "redeemed_date": "string",
        "reward_slug": "voucher-type-slug",
        "reward_uuid": account_holder_uuid,
    }
    resp = send_post_accounts_voucher(
        retailer_slug,
        account_holder_uuid,
        payload,
        "valid" if token_validity == "valid" else "invalid",  # jump through mypy hoops
    )
    logging.info(
        f"POST Reward Endpoint request body: {json.dumps(payload, indent=4)}\n"
        f"Post Reward URL:{POLARIS_BASE_URL}/{retailer_slug}/accounts/{account_holder_uuid}/rewards"
    )
    request_context["response"] = resp


@then(parse("I get a {response_fixture} voucher response body"))
def check_voucher_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = VoucherResponses.get_json(response_fixture)
    resp = request_context["response"]
    assert resp.json() == expected_response_body
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@then(parse("the returned voucher's status is {status} and the voucher data is well formed"))
def check_voucher_status(polaris_db_session: "Session", status: str, request_context: dict) -> None:
    correct_keys = ["voucher_code", "issued_date", "redeemed_date", "expiry_date", "status"]
    voucher_response = request_context["response"].json()
    voucher_list = voucher_response["vouchers"]
    assert len(voucher_list) == 1
    assert voucher_list[0]["status"] == status.lower()
    assert list(voucher_list[0].keys()) == correct_keys
    voucher_code = voucher_list[0].get("voucher_code")
    assert bool(voucher_code) is True
    account_holder_voucher = get_account_holder_voucher(
        polaris_db_session, voucher_code, request_context["retailer_slug"]
    )
    assert voucher_list[0]["issued_date"] == int(
        account_holder_voucher.issued_date.replace(tzinfo=timezone.utc).timestamp()
    )
    assert voucher_list[0]["expiry_date"] == int(
        account_holder_voucher.expiry_date.replace(tzinfo=timezone.utc).timestamp()
    )
    assert voucher_list[0]["redeemed_date"] is None
