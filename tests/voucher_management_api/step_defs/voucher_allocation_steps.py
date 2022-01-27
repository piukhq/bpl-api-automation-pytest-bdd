import json
import logging
import uuid

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse
from retry_tasks_lib.enums import RetryTaskStatuses

from db.carina.models import Reward, RewardConfig
from tests.voucher_management_api.api_requests.voucher_allocation import (
    send_post_malformed_voucher_allocation,
    send_post_voucher_allocation,
)
from tests.voucher_management_api.db_actions.voucher import (
    get_allocated_voucher,
    get_count_unallocated_vouchers_by_voucher_config,
    get_last_created_voucher_allocation,
    get_voucher_config,
    get_voucher_config_with_available_vouchers,
    get_voucher_configs_ids_by_retailer,
)
from tests.voucher_management_api.payloads.voucher_allocation import (
    get_malformed_request_body,
    get_voucher_allocation_payload,
)
from tests.voucher_management_api.response_fixtures.voucher_allocation import VoucherAllocationResponses

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

voucher_allocation_responses = VoucherAllocationResponses


@given(parse("there are vouchers that can be allocated for the existing voucher configs"))
def check_vouchers(carina_db_session: "Session", request_context: dict) -> None:

    count_unallocated_vouchers = get_count_unallocated_vouchers_by_voucher_config(
        carina_db_session=carina_db_session, voucher_configs_ids=request_context["voucher_configs_ids"]
    )
    logging.info(
        "checking that voucher table containers at least 1 voucher that can be allocated, "
        f"found: {count_unallocated_vouchers}"
    )
    assert count_unallocated_vouchers >= 1


@given(parse("there are at least {amount:d} voucher configs for {retailer_slug}"))
def check_voucher_configs(carina_db_session: "Session", amount: int, retailer_slug: str, request_context: dict) -> None:
    voucher_configs_ids = get_voucher_configs_ids_by_retailer(
        carina_db_session=carina_db_session, retailer_slug=retailer_slug
    )
    count_voucher_configs = len(voucher_configs_ids)
    logging.info(
        "checking that voucher config table containers at least 1 config for retailer {retailer_slug}, "
        f"found: {count_voucher_configs}"
    )
    assert count_voucher_configs >= amount
    request_context["voucher_configs_ids"] = voucher_configs_ids


@then(parse("a Voucher code will be allocated asynchronously"))
def check_async_voucher_allocation(carina_db_session: "Session", request_context: dict) -> None:
    """Check that the voucher in the Voucher table has been marked as 'allocated' and that it has an id"""
    voucher_allocation_task = get_last_created_voucher_allocation(
        carina_db_session=carina_db_session, voucher_config_id=request_context["voucher_config"].id
    )

    assert voucher_allocation_task != RetryTaskStatuses.WAITING

    voucher = carina_db_session.query(Reward).filter_by(id=voucher_allocation_task.get_params()["voucher_id"]).one()
    assert voucher.allocated
    assert voucher.id

    request_context["voucher_allocation"] = voucher_allocation_task
    request_context["voucher_allocation_task_params"] = voucher_allocation_task.get_params()


# fmt: off
@then(parse("the expiry date is calculated using the expiry window for the voucher_type_slug from the Voucher Management Config"))  # noqa: E501
# fmt: on
def check_voucher_allocation_expiry_date(carina_db_session: "Session", request_context: dict) -> None:
    """Check that validity_days have been used to assign an expiry date"""
    # TODO: it may be possible to put back the check for hours ("%Y-%m-%d %H") once
    # https://hellobink.atlassian.net/browse/BPL-129 is done
    date_time_format = "%Y-%m-%d"
    now = datetime.utcnow()
    expiry_datetime: str = datetime.fromtimestamp(
        request_context["voucher_allocation_task_params"]["expiry_date"], tz=timezone.utc
    ).strftime(date_time_format)
    expected_expiry: str = (now + timedelta(days=request_context["voucher_config"].validity_days)).strftime(
        date_time_format
    )
    assert expiry_datetime == expected_expiry


@then(parse("a POST to /vouchers will be made to update the users account with the voucher allocation"))
def check_voucher_created(polaris_db_session: "Session", request_context: dict) -> None:
    voucher = get_allocated_voucher(polaris_db_session, request_context["voucher_allocation_task_params"]["voucher_id"])
    assert voucher.account_holder_id == request_context["account_holder"].id
    assert voucher.voucher_type_slug == request_context["voucher_config"].voucher_type_slug
    assert voucher.issued_date is not None
    assert voucher.expiry_date is not None
    assert voucher.status == "ISSUED"


# fmt: off
@when(parse("I perform a POST operation against the allocation endpoint for a {retailer_slug} account holder with a {token} auth token"))  # noqa: E501
# fmt: on
def send_post_voucher_allocation_request(
    carina_db_session: "Session", retailer_slug: str, token: str, request_context: dict
) -> None:
    voucher_config: RewardConfig = get_voucher_config_with_available_vouchers(
        carina_db_session=carina_db_session, retailer_slug=retailer_slug
    )
    payload = get_voucher_allocation_payload(request_context)
    if token == "valid":
        auth = True
    elif token == "invalid":
        auth = False
    else:
        raise ValueError(f"{token} is an invalid value for token")

    resp = send_post_voucher_allocation(
        retailer_slug=retailer_slug, voucher_type_slug=voucher_config.voucher_type_slug, request_body=payload, auth=auth
    )

    request_context["response"] = resp
    request_context["voucher_config"] = voucher_config


# fmt: off
@when(parse("I perform a POST operation against the allocation endpoint for a {retailer_slug} account holder with a malformed request"))  # noqa: E501
# fmt: on
def send_post_malformed_voucher_allocation_request(
    carina_db_session: "Session", retailer_slug: str, request_context: dict
) -> None:
    payload = get_malformed_request_body()
    voucher_config: RewardConfig = get_voucher_config(carina_db_session=carina_db_session, retailer_slug=retailer_slug)
    resp = send_post_malformed_voucher_allocation(
        retailer_slug=retailer_slug, voucher_type_slug=voucher_config.voucher_type_slug, request_body=payload
    )

    request_context["response"] = resp
    request_context["voucher_config"] = voucher_config


# fmt: off
@when(parse("I allocate a specific voucher type to an account for {retailer_slug} with a voucher_type_slug that does not exist in the Vouchers table"))  # noqa: E501
# fmt: on
def send_post_bad_voucher_allocation_request(
    carina_db_session: "Session", retailer_slug: str, request_context: dict
) -> None:
    payload = get_voucher_allocation_payload(request_context)
    voucher_type_slug = str(uuid.uuid4())
    resp = send_post_voucher_allocation(
        retailer_slug=retailer_slug, voucher_type_slug=voucher_type_slug, request_body=payload
    )

    request_context["response"] = resp


# fmt: off
@when(parse("I perform a POST operation against the allocation endpoint for an account holder with a non-existent retailer"))  # noqa: E501
# fmt: on
def send_post_voucher_allocation_request_no_retailer(carina_db_session: "Session", request_context: dict) -> None:
    payload = get_voucher_allocation_payload(request_context)

    resp = send_post_voucher_allocation(
        retailer_slug="non-existent-retailer-slug", voucher_type_slug="mock-voucher-type-slug", request_body=payload
    )

    request_context["response"] = resp


@then(parse("I get a {response_fixture} voucher allocation response body"))
def check_voucher_allocation_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = voucher_allocation_responses.get_json(response_fixture)
    resp = request_context["response"]
    logging.info(
        f"POST enrol expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST enrol actual response: {json.dumps(resp.json(), indent=4)}"
    )
    assert resp.json() == expected_response_body
