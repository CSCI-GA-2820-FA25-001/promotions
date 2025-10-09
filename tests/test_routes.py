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
from wsgi import app
from service.common import status
# from service.models import db, YourResourceModel
from service.models import db, Promotion, StatusEnum
from .factories import PromotionFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
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

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

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
        """It should call the home page and return service info"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.get_json()
        self.assertIn("name", body)
        self.assertIn("version", body)
        self.assertIn("endpoints", body)
        self.assertIn("list_promotions", body["endpoints"]) 
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
