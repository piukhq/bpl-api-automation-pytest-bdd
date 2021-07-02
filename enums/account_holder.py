from enum import Enum


class UserVoucherStatuses(Enum):
    ISSUED = "issued"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REDEEMED = "redeemed"
