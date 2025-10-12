######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Test cases for Pet Model
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from .factories import PromotionFactory
from datetime import datetime
from service.models import (
    db,
    Promotion,
    DiscountTypeEnum,
    PromotionTypeEnum,
    StatusEnum,
    DataValidationError,
)
from decimal import Decimal
import pytest
from unittest.mock import patch


DATABASE_URI = os.getenv(
    "DATABASE_URI", "mysql+pymysql://root:mysecret@mysql:3306/mydb"
)

######################################################################
#  YourResourceModel   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods


class TestPromotionModel(TestCase):
    @classmethod
    def setUpClass(cls):
        """This runs once before the test suite"""
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the test suite"""
        db.session.close()
        db.drop_all()

    def setUp(self):
        """Runs before each test"""
        db.session.query(Promotion).delete()
        db.session.commit()

    def tearDown(self):
        """Runs after each test"""
        db.session.remove()

    ######################################################################
    #   T E S T   C A S E S
    ######################################################################

    def test_create_a_promotion(self):
        """It should create a Promotion"""
        promo = PromotionFactory()
        promo.create()
        self.assertIsNotNone(promo.id)

        found = Promotion.all()
        self.assertEqual(len(found), 1)

        data = Promotion.find(promo.id)
        self.assertEqual(data.product_name, promo.product_name)

    def test_read_promotion(self):
        """It should read a Promotion from the database"""
        promo = PromotionFactory()
        promo.create()
        found = Promotion.find(promo.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.product_name, promo.product_name)

    def test_update_promotion(self):
        """It should update an existing Promotion"""
        promo = PromotionFactory()
        promo.create()
        promo.description = "Updated description"
        promo.update()
        updated = Promotion.find(promo.id)
        self.assertEqual(updated.description, "Updated description")

    def test_serialize_promotion(self):
        """It should serialize a Promotion"""
        promo = PromotionFactory()
        data = promo.serialize()
        self.assertIn("product_name", data)
        self.assertEqual(data["product_name"], promo.product_name)

    def test_deserialize_promotion(self):
        """It should deserialize a Promotion"""
        data = {
            "product_name": "Apple Watch",
            "description": "Smart watch discount",
            "original_price": 299.99,
            "discount_value": 50,
            "discount_type": "amount",
            "promotion_type": "discount",
            "expiration_date": datetime.utcnow().isoformat(),
            "status": "active",
        }
        promo = Promotion()
        promo.deserialize(data)
        self.assertEqual(promo.product_name, "Apple Watch")
        self.assertEqual(promo.discount_type, DiscountTypeEnum.amount)

    def test_discounted_price_amount(self):
        """It should correctly compute discounted price when using amount"""
        promo = PromotionFactory(
            discount_type=DiscountTypeEnum.amount, discount_value=20
        )
        expected = promo.original_price - 20
        self.assertEqual(promo.discounted_price, expected)

    def test_discounted_price_percent(self):
        """It should correctly compute discounted price when using percent"""
        promo = PromotionFactory(
            discount_type=DiscountTypeEnum.percent, discount_value=10
        )
        expected = Decimal(promo.original_price) * Decimal(0.9)
        self.assertAlmostEqual(promo.discounted_price, expected, places=2)

    def test_find_by_status(self):
        """It should find promotions by status"""
        promo1 = PromotionFactory(status=StatusEnum.active)
        promo2 = PromotionFactory(status=StatusEnum.draft)
        promo1.create()
        promo2.create()
        active_promos = Promotion.query.filter_by(status=StatusEnum.active).all()
        self.assertEqual(len(active_promos), 1)
        self.assertEqual(active_promos[0].status, StatusEnum.active)

    def test_invalid_data_deserialization(self):
        """It should raise DataValidationError for bad input"""
        promo = Promotion()
        with self.assertRaises(DataValidationError):
            promo.deserialize(None)

    def test_delete_promotion(self):
        """It should delete a Promotion"""
        promo = PromotionFactory()
        promo.create()
        promo.delete()

        found = Promotion.query.get(promo.id)
        self.assertIsNone(found)

    def test_deserialize_valid_data(self):
        """It should deserialize valid data"""
        data = {
            "product_name": "Test Product",
            "description": "Test Desc",
            "original_price": 100,
            "promotion_type": "discount",
            "discount_type": "amount",
            "discount_value": 10,
            "start_date": "2024-01-01T00:00:00",
            "expiration_date": "2024-12-31T00:00:00",
            "status": "active",
        }
        promo = Promotion()
        promo.deserialize(data)
        assert promo.product_name == "Test Product"
        assert promo.discount_value == 10

    def test_deserialize_missing_field(self):
        """It should raise DataValidationError if a field is missing"""
        promo = Promotion()
        with pytest.raises(DataValidationError):
            promo.deserialize({"product_name": "Test"})

    def test_deserialize_invalid_type(self):
        """It should raise DataValidationError on invalid type"""
        promo = Promotion()
        bad_data = {"product_name": 123, "original_price": "abc"}
        with pytest.raises(DataValidationError):
            promo.deserialize(bad_data)

    def test_discounted_price_no_discount(self):
        """It should return original price if not discount type"""
        promo = PromotionFactory(promotion_type="other")
        assert promo.discounted_price == promo.original_price

    def test_discounted_price_amount(self):
        """It should compute discounted price for amount type"""
        promo = PromotionFactory(
            promotion_type="discount",
            discount_type="amount",
            original_price=Decimal("100.00"),
            discount_value=Decimal("10.00"),
        )
        assert promo.discounted_price == Decimal("90.00")

    def test_discounted_price_percent(self):
        """It should compute discounted price for percent type"""
        promo = PromotionFactory(
            promotion_type="discount",
            discount_type="percent",
            original_price=Decimal("200.00"),
            discount_value=Decimal("10.00"),
        )
        assert promo.discounted_price == Decimal("180.00")

    def test_discounted_price_edge_cases(self):
        """It should not return negative prices"""
        promo = PromotionFactory(
            promotion_type="discount",
            discount_type="amount",
            original_price=Decimal("5.00"),
            discount_value=Decimal("10.00"),
        )
        assert promo.discounted_price == Decimal("0.00")

    def test_create_rollback_on_exception(self):
        """It should rollback if create() raises an exception"""
        promo = PromotionFactory()
        promo.product_name = None  # will cause NOT NULL constraint
        with self.assertRaises(DataValidationError):
            promo.create()

    def test_update_rollback_on_exception(self):
        """It should rollback if update() fails"""
        promo = PromotionFactory()
        promo.create()
        # 手动触发异常（mock db.session.commit）
        with patch(
            "service.models.db.session.commit", side_effect=Exception("DB fail")
        ):
            with self.assertRaises(DataValidationError):
                promo.update()

    def test_delete_rollback_on_exception(self):
        """It should rollback if delete() fails"""
        promo = PromotionFactory()
        promo.create()
        with patch(
            "service.models.db.session.commit", side_effect=Exception("DB fail")
        ):
            with self.assertRaises(DataValidationError):
                promo.delete()

    def test_deserialize_invalid_value(self):
        """It should raise DataValidationError for invalid enum values"""
        data = {
            "product_name": "Test",
            "original_price": "10.00",
            "discount_type": "invalid_enum",
            "promotion_type": "discount",
            "expiration_date": "2025-12-31T00:00:00",
            "status": "draft",
        }
        promo = Promotion()
        with self.assertRaises(DataValidationError):
            promo.deserialize(data)

    def test_promotion_type_invalid_type(self):
        """It should raise DataValidationError for wrong data types"""
        data = {
            "product_name": "wrong_test",
            "original_price": 123,
            "discount_value": 12,
            "discount_type": DiscountTypeEnum.percent,
            "promotion_type": PromotionTypeEnum.other,
            "expiration_date": "2025-12-31T00:00:00",
            "status": "draft",
        }
        promo = Promotion()
        with self.assertRaises(DataValidationError):
            promo.deserialize(data)

    def test_deserialize_missing_required_field(self):
        """It should raise DataValidationError when required field missing"""
        data = {
            "original_price": 100.0,
            "promotion_type": "BOGO",
            "expiration_date": "2025-12-31T00:00:00",
        }
        promotion = Promotion()
        with pytest.raises(DataValidationError):
            promotion.deserialize(data)

    def test_deserialize_wrong_type(self):
        """It should raise DataValidationError for wrong data types"""
        data = {
            "product_name": 123,  # wrong type
            "original_price": 100.0,
            "promotion_type": "BOGO",
            "expiration_date": "2025-12-31T00:00:00",
        }
        promotion = Promotion()
        with pytest.raises(DataValidationError):
            promotion.deserialize(data)

    def test_discounted_price_non_discount_type(self):
        """It should return original price if promotion type is not discount"""
        promo = PromotionFactory(promotion_type=PromotionTypeEnum.other)
        assert promo.discounted_price == promo.original_price

    def test_discounted_price_amount(self):
        """It should calculate correct price for amount discount"""
        promo = PromotionFactory(
            discount_type=DiscountTypeEnum.amount,
            discount_value=Decimal("5.00"),
            original_price=Decimal("20.00"),
        )
        assert promo.discounted_price == Decimal("15.00")

    def test_discounted_price_percent_over_100(self):
        """It should not go below 0 when percent discount > 100"""
        promo = PromotionFactory(
            discount_type=DiscountTypeEnum.percent,
            discount_value=Decimal("150.00"),
            original_price=Decimal("10.00"),
        )
        assert promo.discounted_price == Decimal("0.00")

    def test_find_by_name(self):
        """It should return promotions matching the given name"""
        promo = PromotionFactory(product_name="FindMe")
        promo.create()
        results = Promotion.find_by_name("FindMe")
        assert len(results) == 1
        assert results[0].product_name == "FindMe"

    def test_find_by_status(self):
        """It should return promotions matching the given status"""
        promo_active = PromotionFactory(status=StatusEnum.active)
        promo_active.create()
        promo_draft = PromotionFactory(status=StatusEnum.draft)
        promo_draft.create()

        results = Promotion.find_by_status(StatusEnum.active)
        assert all(p.status == StatusEnum.active for p in results)
        assert promo_active in results
        assert promo_draft not in results

    def test_find_by_discount_type(self):
        """It should return promotions matching the given discount_type"""
        promo_amount = PromotionFactory(discount_type=DiscountTypeEnum.amount)
        promo_amount.create()
        promo_percent = PromotionFactory(discount_type=DiscountTypeEnum.percent)
        promo_percent.create()

        results = Promotion.find_by_discount_type(DiscountTypeEnum.amount)
        assert all(p.discount_type == DiscountTypeEnum.amount for p in results)
        assert promo_amount in results
        assert promo_percent not in results

    def test_find_by_expiration_date(self):
        """It should return promotions matching the given expiration_date"""
        promo1 = PromotionFactory()
        promo1.expiration_date = promo1.start_date
        promo1.create()
        promo2 = PromotionFactory()
        promo2.create()

        results = Promotion.find_by_expiration_date(promo1.expiration_date)
        assert promo1 in results
        assert promo2 not in results

    def test_find_by_promotion_type(self):
        """It should return promotions matching the given promotion_type"""
        promo_discount = PromotionFactory(promotion_type=PromotionTypeEnum.discount)
        promo_discount.create()
        promo_other = PromotionFactory(
            promotion_type=PromotionTypeEnum.other,
            discount_type=None,
            discount_value=None,
        )
        promo_other.create()

        results_discount = Promotion.find_by_promotion_type(PromotionTypeEnum.discount)
        results_other = Promotion.find_by_promotion_type(PromotionTypeEnum.other)

        assert all(
            p.promotion_type == PromotionTypeEnum.discount for p in results_discount
        )
        assert promo_discount in results_discount
        assert promo_other not in results_discount

        assert all(p.promotion_type == PromotionTypeEnum.other for p in results_other)
        assert promo_other in results_other
        assert promo_discount not in results_other

    def test_find_and_all(self):
        """It should find promotions by id and return all promotions"""
        promo1 = PromotionFactory(product_name="One")
        promo2 = PromotionFactory(product_name="Two")
        promo1.create()
        promo2.create()

        results = Promotion.all()
        assert len(results) >= 2

        found = Promotion.find(promo1.id)
        assert found.id == promo1.id
