from core.read_services import register_growth_reader

from .bootstrap import register_growth_subscriptions
from .read_service import GrowthReadService
from .router import router

register_growth_reader(GrowthReadService())
register_growth_subscriptions()

__all__ = ["router"]
