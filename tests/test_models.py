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
Test cases for Promotions Model
"""

# pylint: disable=duplicate-code
import os
import logging
from datetime import datetime
from decimal import Decimal
from unittest import TestCase
from unittest.mock import patch
import pytest
from wsgi import app
from service.models import db, Promotion, DiscountTypeEnum, PromotionTypeEnum, StatusEnum, DataValidationError
from .factories import PromotionFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  P R O M O T I O N   M O D E L   T E S T   C A S E S
######################################################################
class TestPromotionModel(TestCase):  # pylint: disable=too-many-public-methods
    """Promotion Model Test Cases"""

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
    #  C R U D   T E S T S
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

    def test_delete_promotion(self):
        """It should delete a Promotion"""
        promo = PromotionFactory()
        promo.create()
        promo_id = promo.id
        promo.delete()

        found = Promotion.find(promo_id)
        self.assertIsNone(found)

    ######################################################################
    #  S E R I A L I Z A T I O N   T E S T S
    ######################################################################
    def test_serialize_promotion(self):
        """It should serialize a Promotion"""
        promo = PromotionFactory()
        data = promo.serialize()
        self.assertIn("product_name", data)
        self.assertEqual(data["product_name"], promo.product_name)
        self.assertIn("original_price", data)
        self.assertIn("discounted_price", data)

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
            "status": "active"
        }
        promo = Promotion()
        promo.deserialize(data)
        self.assertEqual(promo.product_name, "Apple Watch")
        self.assertEqual(promo.discount_type, DiscountTypeEnum.amount)

    def test_deserialize_missing_required_field(self):
        """It should raise DataValidationError when required field missing"""
        data = {
            "original_price": 100.0,
            "promotion_type": "discount",
            "expiration_date": "2025-12-31T00:00:00"
        }
        promotion = Promotion()
        with pytest.raises(DataValidationError):
            promotion.deserialize(data)

    def test_deserialize_wrong_type(self):
        """It should raise DataValidationError for wrong data types"""
        data = {
            "product_name": 123,  # wrong type - should be string
            "original_price": 100.0,
            "promotion_type": "discount",
            "expiration_date": "2025-12-31T00:00:00"
        }
        promotion = Promotion()
        with pytest.raises(DataValidationError):
            promotion.deserialize(data)

    def test_deserialize_invalid_enum_value(self):
        """It should raise DataValidationError for invalid enum values"""
        data = {
            "product_name": "Test",
            "original_price": 10.00,
            "discount_type": "invalid_enum",
            "promotion_type": "discount",
            "expiration_date": "2025-12-31T00:00:00",
        }
        promo = Promotion()
        with self.assertRaises(DataValidationError):
            promo.deserialize(data)

    def test_deserialize_promotion_type_other_with_discount(self):
        """It should raise error if promotion_type='other' has discount_value"""
        data = {
            "product_name": "wrong_test",
            "original_price": 123,
            "discount_value": 12,
            "discount_type": "percent",
            "promotion_type": "other",
            "expiration_date": "2025-12-31T00:00:00",
        }
        promo = Promotion()
        with self.assertRaises(DataValidationError):
            promo.deserialize(data)

    def test_deserialize_none_data(self):
        """It should raise DataValidationError for None input"""
        promo = Promotion()
        with self.assertRaises(DataValidationError):
            promo.deserialize(None)

    ######################################################################
    #  D I S C O U N T E D   P R I C E   T E S T S
    ######################################################################
    def test_discounted_price_amount(self):
        """It should correctly compute discounted price when using amount"""
        promo = PromotionFactory(
            promotion_type=PromotionTypeEnum.discount,
            discount_type=DiscountTypeEnum.amount,
            original_price=Decimal("100.00"),
            discount_value=Decimal("20.00")
        )
        expected = Decimal("80.00")
        self.assertEqual(promo.discounted_price, expected)

    def test_discounted_price_percent(self):
        """It should correctly compute discounted price when using percent"""
        promo = PromotionFactory(
            promotion_type=PromotionTypeEnum.discount,
            discount_type=DiscountTypeEnum.percent,
            original_price=Decimal("200.00"),
            discount_value=Decimal("10.00")
        )
        expected = Decimal("180.00")
        self.assertAlmostEqual(float(promo.discounted_price), float(expected), places=2)

    def test_discounted_price_non_discount_type(self):
        """It should return original price if promotion type is not discount"""
        promo = PromotionFactory(
            promotion_type=PromotionTypeEnum.other,
            discount_type=None,
            discount_value=None
        )
        self.assertEqual(promo.discounted_price, promo.original_price)

    def test_discounted_price_no_negative(self):
        """It should not return negative prices"""
        promo = PromotionFactory(
            promotion_type=PromotionTypeEnum.discount,
            discount_type=DiscountTypeEnum.amount,
            original_price=Decimal("5.00"),
            discount_value=Decimal("10.00")
        )
        self.assertEqual(promo.discounted_price, Decimal("0.00"))

    def test_discounted_price_percent_over_100(self):
        """It should not go below 0 when percent discount > 100"""
        promo = PromotionFactory(
            promotion_type=PromotionTypeEnum.discount,
            discount_type=DiscountTypeEnum.percent,
            original_price=Decimal("10.00"),
            discount_value=Decimal("150.00")
        )
        self.assertGreaterEqual(promo.discounted_price, Decimal("0.00"))

    ######################################################################
    #  Q U E R Y   M E T H O D S   T E S T S
    ######################################################################
    def test_find_by_name(self):
        """It should return promotions matching the given name"""
        promo = PromotionFactory(product_name="FindMe")
        promo.create()
        results = Promotion.find_by_name("FindMe")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].product_name, "FindMe")

    def test_find_by_status(self):
        """It should return promotions matching the given status"""
        promo_active = PromotionFactory(status=StatusEnum.active)
        promo_active.create()
        promo_draft = PromotionFactory(status=StatusEnum.draft)
        promo_draft.create()

        results = Promotion.find_by_status(StatusEnum.active)
        self.assertTrue(all(p.status == StatusEnum.active for p in results))
        self.assertIn(promo_active, results)
        self.assertNotIn(promo_draft, results)

    def test_find_by_discount_type(self):
        """It should return promotions matching the given discount_type"""
        promo_amount = PromotionFactory(discount_type=DiscountTypeEnum.amount)
        promo_amount.create()
        promo_percent = PromotionFactory(discount_type=DiscountTypeEnum.percent)
        promo_percent.create()

        results = Promotion.find_by_discount_type(DiscountTypeEnum.amount)
        self.assertTrue(all(p.discount_type == DiscountTypeEnum.amount for p in results))

    def test_find_by_promotion_type(self):
        """It should return promotions matching the given promotion_type"""
        promo_discount = PromotionFactory(promotion_type=PromotionTypeEnum.discount)
        promo_discount.create()
        promo_other = PromotionFactory(
            promotion_type=PromotionTypeEnum.other,
            discount_type=None,
            discount_value=None
        )
        promo_other.create()

        results = Promotion.find_by_promotion_type(PromotionTypeEnum.discount)
        self.assertTrue(all(p.promotion_type == PromotionTypeEnum.discount for p in results))

    def test_find_and_all(self):
        """It should find promotions by id and return all promotions"""
        promo1 = PromotionFactory(product_name="One")
        promo2 = PromotionFactory(product_name="Two")
        promo1.create()
        promo2.create()

        results = Promotion.all()
        self.assertGreaterEqual(len(results), 2)

        found = Promotion.find(promo1.id)
        self.assertEqual(found.id, promo1.id)

    ######################################################################
    #  E R R O R   H A N D L I N G   T E S T S
    ######################################################################
    def test_create_rollback_on_exception(self):
        """It should rollback if create() raises an exception"""
        promo = PromotionFactory()
        with patch("service.models.db.session.commit", side_effect=Exception("DB fail")):
            with self.assertRaises(DataValidationError):
                promo.create()

    def test_update_rollback_on_exception(self):
        """It should rollback if update() fails"""
        promo = PromotionFactory()
        promo.create()
        with patch("service.models.db.session.commit", side_effect=Exception("DB fail")):
            with self.assertRaises(DataValidationError):
                promo.update()

    def test_delete_rollback_on_exception(self):
        """It should rollback if delete() fails"""
        promo = PromotionFactory()
        promo.create()
        with patch("service.models.db.session.commit", side_effect=Exception("DB fail")):
            with self.assertRaises(DataValidationError):
                promo.delete()

    ######################################################################
    #  E D G E   C A S E S   F O R   F U L L   C O V E R A G E
    ######################################################################

    def test_discounted_price_unknown_type(self):
        """It should return original price for unknown discount_type"""
        promo = PromotionFactory(
            promotion_type=PromotionTypeEnum.discount,
            discount_type=None,  # triggers final fallback return
            discount_value=Decimal("10.00"),
            original_price=Decimal("100.00"),
        )
        self.assertEqual(promo.discounted_price, promo.original_price)

    def test_deserialize_key_error(self):
        """It should raise DataValidationError for missing key error"""
        bad_data = {"wrong_key": "value"}
        promo = Promotion()
        with self.assertRaises(DataValidationError):
            promo.deserialize(bad_data)

    def test_deserialize_type_error(self):
        """It should raise DataValidationError for invalid input type"""
        promo = Promotion()
        with self.assertRaises(DataValidationError):
            promo.deserialize("not_a_dict")  # triggers TypeError branch

    def test_find_by_expiration_date(self):
        """It should find promotions by expiration_date"""
        promo = PromotionFactory()
        promo.create()
        results = Promotion.find_by_expiration_date(promo.expiration_date)
        self.assertGreaterEqual(len(results), 1)
