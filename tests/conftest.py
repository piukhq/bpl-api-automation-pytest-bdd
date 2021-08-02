import logging

from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, Generator

import pytest

from db.polaris.models import UserVoucher
from db.polaris.session import PolarisSessionMaker
from db.vela.session import VelaSessionMaker
from enums.account_holder import UserVoucherStatuses

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# Hooks
def pytest_bdd_step_error(
    request: Any,
    feature: Any,
    scenario: Any,
    step: Any,
    step_func: Any,
    step_func_args: Any,
    exception: Any,
) -> None:
    """This function will log the failed BDD-Step at the end of logs"""
    logging.info(f"Step failed: {step}")


def pytest_html_report_title(report: Any) -> None:
    """Customized title for html report"""
    report.title = "BPL Test Automation Results"


@pytest.fixture(scope="function")
def request_context() -> dict:
    return {}


@pytest.fixture(scope="function")
def polaris_db_session() -> Generator:
    with PolarisSessionMaker() as db_session:
        yield db_session


@pytest.fixture(scope="function")
def vela_db_session() -> Generator:
    with VelaSessionMaker() as db_session:
        yield db_session


@pytest.fixture()
def create_mock_voucher(polaris_db_session: "Session") -> Callable:
    voucher = {
        "updated_at": None,
        "voucher_code": "test_voucher_code",
        "issued_date": None,
        "status": UserVoucherStatuses.ISSUED,
        "cancelled_date": None,
        "account_holder": None,  # Pass this in as an account_holder obj
        "created_at": datetime.now(),
        "voucher_id": None,
        "expiry_date": datetime(2121, 6, 25, 14, 30, 00),
        "redeemed_date": None,
        "voucher_type_slug": "test-voucher-slug",
    }

    def _create_mock_voucher(**voucher_params: Dict) -> UserVoucher:
        """
        Create a voucher in the test DB
        :param voucher_params: override any values for voucher
        :return: Callable function
        """
        assert voucher_params["account_holder"]
        voucher.update(voucher_params)  # type: ignore
        mock_voucher = UserVoucher(**voucher)

        polaris_db_session.add(mock_voucher)
        polaris_db_session.commit()

        return mock_voucher

    return _create_mock_voucher
