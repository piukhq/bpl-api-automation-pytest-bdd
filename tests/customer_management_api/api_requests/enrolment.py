from typing import TYPE_CHECKING

from .base import Endpoints, send_invalid_post_request, send_malformed_post_request, send_post_request

if TYPE_CHECKING:
    from requests import Response


def send_post_enrolment(retailer_slug: str, request_body: dict, headers: dict = None) -> "Response":
    return send_post_request(retailer_slug, request_body, Endpoints.ENROL, headers=headers)


def send_malformed_post_enrolment(retailer_slug: str, request_body: str) -> "Response":
    return send_malformed_post_request(retailer_slug, request_body, Endpoints.ENROL)


def send_invalid_post_enrolment(retailer_slug: str, request_body: dict) -> "Response":
    return send_invalid_post_request(retailer_slug, request_body, Endpoints.ENROL)
