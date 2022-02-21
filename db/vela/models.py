from enum import Enum

from sqlalchemy.ext.automap import automap_base

from db.vela.session import engine

Base = automap_base()
Base.prepare(engine, reflect=True)

# get models from Base mapping
RetailerRewards = Base.classes.retailer_rewards
Campaign = Base.classes.campaign
EarnRule = Base.classes.earn_rule
Transaction = Base.classes.transaction
ProcessedTransaction = Base.classes.processed_transaction
RewardRule = Base.classes.reward_rule


class CampaignStatuses(str, Enum):
    ACTIVE = "ACTIVE"
    DRAFT = "DRAFT"
    CANCELLED = "CANCELLED"
    ENDED = "ENDED"


class LoyaltyTypes(str, Enum):
    ACCUMULATOR = "ACCUMULATOR"
    STAMPS = "STAMPS"