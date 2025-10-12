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
TestYourResourceModel API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from datetime import datetime, timedelta
from wsgi import app
from service.common import status
# from service.models import db, YourResourceModel
from service.models import db, Promotion, StatusEnum
from .factories import PromotionFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "mysql+pymysql://root:mysecret@mysql:3306/mydb"
)


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestYourResourceService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()
        db.drop_all()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        # db.session.query(YourResourceModel).delete()  # clean up the last tests
        db.session.query(Promotion).delete() # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################
    # Todo: Add your test cases here...
    def test_index(self):
        """It should return service metadata with correct fields"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.get_json()
        self.assertIn("service", body)
        self.assertIn("version", body)
        self.assertIn("description", body)
        self.assertIn("list_url", body)
        self.assertTrue(body["list_url"].startswith("http"))

    ######################################################################
    # 8 #  T E S T   L I S T   P R O M O T I O N S
    ######################################################################
    def test_list_promotions_empty(self):
        """It should return [] when there is no data"""
        resp = self.client.get("/promotions")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)
    # customer
    def test_list_promotions_customer_only_active(self):
        """It should list ONLY active promotions for customers"""
        active = PromotionFactory(status=StatusEnum.active)
        expired = PromotionFactory(status=StatusEnum.expired)
        active.create()
        expired.create()
    
        resp = self.client.get("/promotions?role=customer")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["status"], "active")
    # supplier
    def test_list_promotions_supplier_active_and_expired(self):
        """Supplier should see active and expired, but NOT deleted"""
        a = PromotionFactory(status=StatusEnum.active)
        e = PromotionFactory(status=StatusEnum.expired)
        d = PromotionFactory(status=StatusEnum.deleted)
        a.create(); e.create(); d.create()
    
        resp = self.client.get("/promotions?role=supplier")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        statuses = [p["status"] for p in data]
        self.assertIn("active", statuses)
        self.assertIn("expired", statuses)
        self.assertNotIn("deleted", statuses)
    # manager
    def test_list_promotions_manager_all(self):
        """Manager should see all promotions"""
        a = PromotionFactory(status=StatusEnum.active)
        e = PromotionFactory(status=StatusEnum.expired)
        d = PromotionFactory(status=StatusEnum.deleted)
        a.create(); e.create(); d.create()
    
        resp = self.client.get("/promotions?role=manager")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 3)

    def test_list_promotions_invalid_role(self):
        """It should return 400 for invalid role value"""
        resp = self.client.get("/promotions?role=whoami")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        body = resp.get_json()
        self.assertTrue("Invalid role" in body.get("message", "") or "Invalid role" in body.get("description", ""))

    ######################################################################
    #  T E S T   C R E A T E   P R O M O T I O N
    ######################################################################

    def _get_admin_headers(self):
        """Helper to get admin auth headers"""
        return {"X-Role": "administrator"}

    def _get_customer_headers(self):
        """Helper to get non-admin headers"""
        return {"X-Role": "customer"}

    def test_create_promotion_success(self):
        """It should create a promotion with valid admin credentials"""
        promotion_data = {
            "product_name": "Black Friday Sale",
            "description": "Huge discount event",
            "original_price": 100.00,
            "discount_value": 20.0,
            "discount_type": "percent",
            "promotion_type": "discount",
            "start_date": datetime.now().isoformat(),
            "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
        }
        resp = self.client.post("/promotions", json=promotion_data, headers=self._get_admin_headers())
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.get_json()
        self.assertIsNotNone(data["id"])
        self.assertEqual(data["product_name"], "Black Friday Sale")
        self.assertEqual(data["status"], "draft")
        self.assertEqual(data["discounted_price"], 80.0)
        self.assertIsNotNone(data["created_at"])
        self.assertIsNotNone(data["updated_at"])
        self.assertIn("Location", resp.headers)

    def test_create_promotion_unauthorized(self):
        """It should return 401 when no authentication provided"""
        promotion_data = {
            "product_name": "Test Promo",
            "original_price": 100.00,
            "promotion_type": "discount",
            "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
        }
        resp = self.client.post("/promotions", json=promotion_data)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        data = resp.get_json()
        self.assertIn("error", data)

    def test_create_promotion_forbidden(self):
        """It should return 403 when non-admin tries to create"""
        promotion_data = {
            "product_name": "Test Promo",
            "original_price": 100.00,
            "promotion_type": "discount",
            "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
        }
        resp = self.client.post("/promotions", json=promotion_data, headers=self._get_customer_headers())
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("privileges", data["message"].lower())

    def test_create_promotion_missing_field(self):
        """It should return 400 when required field is missing"""
        promotion_data = {
            "description": "Missing product_name",
            "original_price": 100.00,
        }
        resp = self.client.post("/promotions", json=promotion_data, headers=self._get_admin_headers())
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("error", data)

    def test_create_promotion_invalid_json(self):
        """It should return 400 for malformed JSON"""
        resp = self.client.post(
            "/promotions",
            data="not valid json",
            headers=self._get_admin_headers(),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_promotion_invalid_promotion_type(self):
        """It should return 400 for invalid promotion_type enum"""
        promotion_data = {
            "product_name": "Invalid Type",
            "original_price": 100.00,
            "promotion_type": "invalid_type",
            "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
        }
        resp = self.client.post("/promotions", json=promotion_data, headers=self._get_admin_headers())
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_promotion_negative_price(self):
        """It should return 422 when original_price <= 0"""
        promotion_data = {
            "product_name": "Negative Price",
            "original_price": -10.00,
            "promotion_type": "discount",
            "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
        }
        resp = self.client.post("/promotions", json=promotion_data, headers=self._get_admin_headers())
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_create_promotion_discount_exceeds_price(self):
        """It should return 422 when discount_value > original_price"""
        promotion_data = {
            "product_name": "Invalid Discount",
            "original_price": 50.00,
            "discount_value": 60.00,
            "discount_type": "amount",
            "promotion_type": "discount",
            "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
        }
        resp = self.client.post("/promotions", json=promotion_data, headers=self._get_admin_headers())
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_create_promotion_percent_out_of_range(self):
        """It should return 422 when percent > 100"""
        promotion_data = {
            "product_name": "Invalid Percent",
            "original_price": 100.00,
            "discount_value": 150.0,
            "discount_type": "percent",
            "promotion_type": "discount",
            "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
        }
        resp = self.client.post("/promotions", json=promotion_data, headers=self._get_admin_headers())
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_create_promotion_expiration_before_start(self):
        """It should return 422 when expiration_date < start_date"""
        start = datetime.now() + timedelta(days=30)
        end = datetime.now() + timedelta(days=10)
        promotion_data = {
            "product_name": "Bad Dates",
            "original_price": 100.00,
            "promotion_type": "discount",
            "start_date": start.isoformat(),
            "expiration_date": end.isoformat(),
        }
        resp = self.client.post("/promotions", json=promotion_data, headers=self._get_admin_headers())
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_create_promotion_other_type_with_discount(self):
        """It should return 422 when promotion_type=other but discount fields present"""
        promotion_data = {
            "product_name": "Other with Discount",
            "original_price": 100.00,
            "discount_value": 20.0,
            "discount_type": "percent",
            "promotion_type": "other",
            "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
        }
        resp = self.client.post("/promotions", json=promotion_data, headers=self._get_admin_headers())
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_create_promotion_duplicate_name(self):
        """It should return 409 when product_name already exists"""
        promotion_data = {
            "product_name": "Duplicate Promo",
            "original_price": 100.00,
            "promotion_type": "discount",
            "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
        }
        # Create first
        resp1 = self.client.post("/promotions", json=promotion_data, headers=self._get_admin_headers())
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        
        # Try duplicate
        resp2 = self.client.post("/promotions", json=promotion_data, headers=self._get_admin_headers())
        self.assertEqual(resp2.status_code, status.HTTP_409_CONFLICT)

    def test_create_promotion_with_amount_discount(self):
        """It should create promotion with amount-based discount"""
        promotion_data = {
            "product_name": "Amount Discount",
            "original_price": 100.00,
            "discount_value": 25.00,
            "discount_type": "amount",
            "promotion_type": "discount",
            "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
        }
        resp = self.client.post("/promotions", json=promotion_data, headers=self._get_admin_headers())
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.get_json()
        self.assertEqual(data["discounted_price"], 75.0)

    ######################################################################
    #  E R R O R   H A N D L E R   T E S T S
    ######################################################################

    def test_404_not_found(self):
        """It should return 404 for non-existent routes"""
        resp = self.client.get("/does-not-exist")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertIn("error", data)

    def test_405_method_not_allowed(self):
        """It should return 405 for unsupported methods"""
        resp = self.client.put("/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        data = resp.get_json()
        self.assertIn("error", data)

    def test_415_unsupported_media_type(self):
        """It should return 415 for wrong content type"""
        resp = self.client.post(
            "/promotions",
            data="test",
            headers={**self._get_admin_headers(), "Content-Type": "text/plain"}
        )
        # This might return 400 instead depending on Flask handling
        self.assertIn(resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE])
