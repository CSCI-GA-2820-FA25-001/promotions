"""
Test Factory to make fake objects for testing
"""

import factory
from datetime import datetime, timedelta
from service.models import Promotion, DiscountTypeEnum, PromotionTypeEnum, StatusEnum,db


class PromotionFactory(factory.Factory):
    """Creates fake pets that you don't have to feed"""

    class Meta:
        model = Promotion

    id = factory.Sequence(lambda n: n + 1)
    product_name = factory.Sequence(lambda n: f"Product_{n}")
    description = factory.Faker("sentence", nb_words=6)
    original_price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    discount_value = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    discount_type = DiscountTypeEnum.amount
    promotion_type = PromotionTypeEnum.discount
    start_date = factory.LazyFunction(datetime.now)
    expiration_date = factory.LazyFunction(lambda: datetime.now() + timedelta(days=30))
    status = StatusEnum.draft

    # Todo: Add your other attributes here...
