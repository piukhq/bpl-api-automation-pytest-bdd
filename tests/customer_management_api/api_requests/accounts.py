from typing import TYPE_CHECKING

from .base import Endpoints, send_get_request, send_invalid_get_request, send_malformed_get_request

if TYPE_CHECKING:
    from requests import Response


def send_get_accounts(retailer_slug: str, uuid: str, *, headers: dict = None) -> "Response":
    return send_get_request(retailer_slug, Endpoints.ACCOUNTS, params=uuid, headers=headers)


def send_get_accounts_status(retailer_slug: str, uuid: str, *, headers: dict = None) -> "Response":
    params = f"{uuid}/status"
    return send_get_request(retailer_slug, endpoint=Endpoints.ACCOUNTS, params=params, headers=headers)


def send_malformed_get_accounts(retailer_slug: str) -> "Response":
    return send_malformed_get_request(retailer_slug, Endpoints.ACCOUNTS, param="not-a-uuid")


def send_invalid_get_accounts(retailer_slug: str, uuid: str) -> "Response":
    return send_invalid_get_request(retailer_slug, Endpoints.ACCOUNTS, param=uuid)
