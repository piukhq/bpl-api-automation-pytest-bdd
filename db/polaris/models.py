import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import relationship

from db.polaris.session import engine
from enums.account_holder import UserVoucherStatuses

Base = automap_base()
utc_timestamp_sql = text("TIMEZONE('utc', CURRENT_TIMESTAMP)")


class AccountHolder(Base):  # type: ignore
    __tablename__ = "account_holder"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=utc_timestamp_sql, nullable=False)
    updated_at = Column(DateTime, server_default=utc_timestamp_sql, onupdate=utc_timestamp_sql, nullable=False)


class UserVoucher(Base):  # type: ignore
    __tablename__ = "user_voucher"

    id = Column(Integer, primary_key=True, index=True)
    voucher_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    voucher_code = Column(String, nullable=False, unique=True, index=True)
    issued_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    status = Column(Enum(UserVoucherStatuses), nullable=False, default=UserVoucherStatuses.ISSUED)
    redeemed_date = Column(DateTime, nullable=True)
    cancelled_date = Column(DateTime, nullable=True)
    voucher_type_slug = Column(String(32), index=True, nullable=False)
    account_holder_id = Column(UUID(as_uuid=True), ForeignKey("account_holder.id", ondelete="CASCADE"))
    account_holder = relationship("AccountHolder", back_populates="vouchers")

    __mapper_args__ = {"eager_defaults": True}


Base.prepare(engine, reflect=True)

# get models from Base mapping
AccountHolderProfile = Base.classes.account_holder_profile
AccountHolderActivation = Base.classes.account_holder_activation
RetailerConfig = Base.classes.retailer_config
