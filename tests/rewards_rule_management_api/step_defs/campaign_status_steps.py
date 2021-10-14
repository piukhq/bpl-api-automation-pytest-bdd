import json
import logging
import uuid

from typing import TYPE_CHECKING, Callable
from unittest.mock import ANY

from pytest_bdd import given, parsers, then, when

from db.vela.models import Campaign, CampaignStatuses, RetailerRewards
from tests.rewards_rule_management_api.api_requests.campaign_status import (
    send_post_campaign_status_change,
    send_post_malformed_campaign_status_change,
)
from tests.rewards_rule_management_api.db_actions.campaigns import get_active_campaigns, get_retailer_rewards
from tests.rewards_rule_management_api.payloads.campaign_status_change import (
    get_campaign_status_change_payload,
    get_malformed_request_body,
)
from tests.rewards_rule_management_api.response_fixtures.campaign_status import CampaignStatusResponses
from tests.voucher_management_api.payloads.voucher_allocation import get_malformed_request_body

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

status_change_responses = CampaignStatusResponses


def _change_campaign_status(vela_db_session: "Session", campaign: Campaign, requested_status: CampaignStatuses):
    campaign.status = requested_status  # type: ignore
    vela_db_session.commit()


@given(parsers.parse("{retailer_slug} has at least {campaigns_total:d} {status} campaign(s)"))
def make_campaigns_available_for_test(
    vela_db_session: "Session",
    create_mock_campaign: Callable,
    retailer_slug: str,
    campaigns_total: int,
    status: str,
    request_context: dict,
) -> None:
    retailer: RetailerRewards = get_retailer_rewards(vela_db_session, retailer_slug)
    if request_context.get("active_campaigns"):
        mock_campaigns: list[Campaign] = request_context["active_campaigns"]
    else:
        mock_campaigns: list[Campaign] = []  # get_active_campaigns(vela_db_session, retailer_slug)
    for _ in range(campaigns_total):
        mock_campaign: Campaign = create_mock_campaign(
            retailer=retailer,
            **{
                "status": CampaignStatuses(status).name,
                "name": str(uuid.uuid4()),
                "slug": str(uuid.uuid4())[:32],
            },
        )
        mock_campaigns.append(mock_campaign)

    request_context["retailer_slug"] = retailer_slug
    request_context["active_campaigns"] = mock_campaigns


@when(
    parsers.parse(
        "I perform a POST operation against the status change endpoint with the {payload_type} payload for a {status} status for "
        "a {retailer_slug} retailer "
        "with a {token} auth token"
    )
)
def send_post_campaign_change_request(
    vela_db_session: "Session", payload_type: str, status: str, retailer_slug: str, token: str, request_context: dict
) -> None:
    # request_context["active_campaigns"] = request_context["active_campaigns"][:1]  # only need the first one

    payload = {}
    if payload_type == "correct":
        payload = get_campaign_status_change_payload(request_context, status)
    elif payload_type == "incorrect":
        payload = {
            "bad_field_1": 1,
            "bad_field_2": [2],
        }

    if token == "valid":
        auth = True
    elif token == "invalid":
        auth = False
    else:
        raise ValueError(f"{token} is an invalid value for token")

    resp = send_post_campaign_status_change(retailer_slug=retailer_slug, request_body=payload, auth=auth)

    request_context["response"] = resp


@when(
    parsers.parse(
        "I perform a POST operation against the status change endpoint for a {status} status for a {campaign_slug} "
        "campaign for a {retailer_slug} retailer"
    )
)
def send_post_campaign_change_request(
    vela_db_session: "Session", status: str, campaign_slug: str, retailer_slug: str, request_context: dict
) -> None:
    payload = {
        "requested_status": status,
        "campaign_slugs": [campaign_slug],
    }

    resp = send_post_campaign_status_change(retailer_slug=retailer_slug, request_body=payload, auth=True)

    request_context["response"] = resp


@then(parsers.parse("the campaign status should be updated in Vela"))
def check_campaign_status(vela_db_session: "Session", request_context: dict) -> None:
    campaign = request_context["active_campaigns"][0]
    vela_db_session.refresh(campaign)
    assert campaign.status == CampaignStatuses.ENDED

    # Restore ACTIVE status
    _change_campaign_status(
        vela_db_session=vela_db_session, campaign=campaign, requested_status=CampaignStatuses.ACTIVE
    )


@when(
    parsers.parse(
        "I perform a POST operation against the status change endpoint for a {retailer_slug} retailer with a "
        "malformed request"
    )
)
def send_post_malformed_status_change_request(
    vela_db_session: "Session", retailer_slug: str, request_context: dict
) -> None:
    payload = get_malformed_request_body()
    request_context["active_campaigns"] = request_context["active_campaigns"][:1]  # only need the first one

    resp = send_post_malformed_campaign_status_change(retailer_slug=retailer_slug, request_body=payload)

    request_context["response"] = resp


@then(parsers.parse("I get a {response_fixture} status change response body"))
def check_status_change_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = status_change_responses.get_json(response_fixture)
    resp = request_context["response"]
    logging.info(
        f"POST campaign status change expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST campaign status change actual response: {json.dumps(resp.json(), indent=4)}"
    )
    assert resp.json() == expected_response_body


@then(parsers.parse("I get an incomplete status update response body"))
def check_status_change_response(request_context: dict) -> None:
    expected_response_body = {
        "display_message": "Not all campaigns were updated as requested.",
        "error": "INCOMPLETE_STATUS_UPDATE",
        "failed_campaigns": [ANY, ANY],
    }
    resp = request_context["response"]
    logging.info(f"POST campaign status change actual response: {json.dumps(resp.json(), indent=4)}")
    assert resp.json() == expected_response_body
