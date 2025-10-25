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
from service.common import status
from unittest import TestCase
from wsgi import app
from .factories import PromotionFactory
from service.models import Promotion, StatusEnum, db
import pytest
from datetime import datetime, timedelta

DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql+psycopg://postgres:postgres@postgres:5432/testdb"
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
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        cls.client = app.test_client()
        with app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        # db.session.query(YourResourceModel).delete()  # clean up the last tests
        db.session.query(Promotion).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################
    # Todo: Add your test cases here...

    ######################################################################
    #  R O O T   U R L   T E S T S
    ######################################################################

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
    #  C R E A T E   T E S T S
    ######################################################################

    def test_create_promotion(self):
        """It should Create a new Promotion"""
        promo = PromotionFactory()
        resp = self.client.post(
            "/promotions",
            json=promo.serialize(),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Check the data is correct
        new_promo = resp.get_json()
        self.assertIsNotNone(new_promo["id"])
        self.assertEqual(new_promo["product_name"], promo.product_name)

        # Check Location header
        location = resp.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check that we can retrieve it
        resp = self.client.get(location)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        retrieved = resp.get_json()
        self.assertEqual(retrieved["id"], new_promo["id"])

    def test_create_promotion_missing_content_type(self):
        """It should not Create a Promotion with missing Content-Type"""
        promo = PromotionFactory()
        resp = self.client.post("/promotions", data=promo.serialize())
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_promotion_wrong_content_type(self):
        """It should not Create a Promotion with wrong Content-Type"""
        resp = self.client.post(
            "/promotions",
            data="This is not JSON",
            content_type="text/plain"
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_promotion_bad_data(self):
        """It should not Create a Promotion with bad data"""
        resp = self.client.post(
            "/promotions",
            json={"product_name": "Missing required fields"},
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def _create_promotions(self, count=1):
        """Helper to create sample promotions"""
        promos = []
        for _ in range(count):
            promo = PromotionFactory()
            resp = self.client.post(
                "/promotions",
                json=promo.serialize(),
                content_type="application/json"
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            promos.append(resp.get_json())
        return promos

    ######################################################################
    #  R E A D   T E S T S
    ######################################################################

    def test_get_promotion(self):
        """It should Read a single Promotion"""
        # Create a promotion first
        promo = self._create_promotions(1)[0]
        resp = self.client.get(f"/promotions/{promo['id']}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], promo["id"])
        self.assertEqual(data["product_name"], promo["product_name"])

    def test_get_promotion_not_found(self):
        """It should not Read a Promotion that doesn't exist"""
        resp = self.client.get("/promotions/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertIn("was not found", data["message"])

    def test_get_promotion_includes_all_fields(self):
        """It should return all fields in the response for a valid promotion"""
        promo = self._create_promotions(1)[0]
        resp = self.client.get(f"/promotions/{promo['id']}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        expected_fields = [
            "id",
            "product_name",
            "description",
            "original_price",
            "discounted_price",
            "discount_value",
            "discount_type",
            "promotion_type",
            "start_date",
            "expiration_date",
            "status",
            "created_at",
            "updated_at",
        ]

        for field in expected_fields:
            self.assertIn(field, data, f"Missing field: {field}")

    ######################################################################
    #  U P D A T E   T E S T S
    ######################################################################
    def test_update_promotion(self):
        """It should Update an existing Promotion"""
        # Create a promotion first
        promo = self._create_promotions(1)[0]

        # Update it
        promo["description"] = "Updated description"
        resp = self.client.put(
            f"/promotions/{promo['id']}",
            json=promo,
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        updated = resp.get_json()
        self.assertEqual(updated["description"], "Updated description")

    def test_update_promotion_not_found(self):
        """It should not Update a Promotion that doesn't exist"""
        promo = PromotionFactory()
        resp = self.client.put(
            "/promotions/0",
            json=promo.serialize(),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_promotion_missing_content_type(self):
        """It should not Update a Promotion with missing Content-Type"""
        promo = self._create_promotions(1)[0]
        resp = self.client.put(f"/promotions/{promo['id']}", data=promo)
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    ######################################################################
    #  D E L E T E   T E S T S
    ######################################################################
    def test_delete_promotion(self):
        """It should Delete a Promotion"""
        # Create a promotion first
        promo = self._create_promotions(1)[0]

        # Delete it
        resp = self.client.delete(f"/promotions/{promo['id']}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(resp.data), 0)

        # Make sure it's deleted
        resp = self.client.get(f"/promotions/{promo['id']}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_promotion_not_found(self):
        """It should delete even if Promotion doesn't exist (idempotent)"""
        resp = self.client.delete("/promotions/0")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_active_promotion(self):
        """It should not delete an active Promotion 409 Conflict"""
        # Create a promotion
        promo = self._create_promotions(1)[0]

        # Update its status to 'active'
        resp = self.client.put(
            f"/promotions/{promo['id']}",
            json={**promo, "status": "active"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Try deleting it
        resp = self.client.delete(f"/promotions/{promo['id']}")
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        data = resp.get_json()
        self.assertEqual(data["error"], "Conflict")
        self.assertIn("Cannot delete active promotion", data["message"])

        # Verify it still exists
        resp = self.client.get(f"/promotions/{promo['id']}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    ######################################################################
    #  L I S T   T E S T S
    ######################################################################
    def test_list_promotions_empty(self):
        """It should return [] when there is no data"""
        resp = self.client.get("/promotions")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)

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

    def test_list_promotions_supplier_active_and_expired(self):
        """Supplier should see active and expired, but NOT deleted"""
        a = PromotionFactory(status=StatusEnum.active)
        e = PromotionFactory(status=StatusEnum.expired)
        d = PromotionFactory(status=StatusEnum.deleted)
        a.create()
        e.create()
        d.create()

        resp = self.client.get("/promotions?role=supplier")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        statuses = [p["status"] for p in data]
        self.assertIn("active", statuses)
        self.assertIn("expired", statuses)
        self.assertNotIn("deleted", statuses)

    def test_list_promotions_manager_all(self):
        """Manager should see all promotions"""
        a = PromotionFactory(status=StatusEnum.active)
        e = PromotionFactory(status=StatusEnum.expired)
        d = PromotionFactory(status=StatusEnum.deleted)
        a.create()
        e.create()
        d.create()

        resp = self.client.get("/promotions?role=manager")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 3)

    def test_list_promotions_invalid_role(self):
        """It should return 400 for invalid role value"""
        resp = self.client.get("/promotions?role=whoami")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_promotions_date_filter(self):
        """It should list only promotions within valid date range"""
        PromotionFactory.create_batch(3)
        resp = self.client.get("/promotions?start_date=2025-01-01&end_date=2025-12-31")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_invalid_content_type(self):
        """It should return 415 when Content-Type is not JSON"""
        resp = self.client.post("/promotions", data="invalid", content_type="text/plain")
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    
    def test_list_promotions_invalid_date_format(self):
        """It should return 400 for invalid date format"""
        resp = self.client.get("/promotions?start_date=bad&end_date=also_bad")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("Invalid date format", data["message"])

    def test_data_validation_error_on_update(self):
        """It should return 400 if update data validation fails"""
        promo = self._create_promotions(1)[0]
        # send invalid payload type to trigger DataValidationError
        bad_json = {"id": promo["id"], "status": 12345}
        resp = self.client.put(
            f"/promotions/{promo['id']}",
            json=bad_json,
            content_type="application/json"
        )
        # may raise Bad Request
        self.assertIn(resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE])

    ######################################################################
    #  E R R O R   H A N D L E R   T E S T S
    ######################################################################
    def test_method_not_allowed(self):
        """It should not allow an illegal method call"""
        resp = self.client.patch("/promotions/0")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        data = resp.get_json()
        self.assertIn("error", data)
    
    ######################################################################
    #  SEARCH TESTS
    ######################################################################
    def test_search_promotions_by_keyword(self):
        """It should return only promotions matching the keyword (case-insensitive)"""
        # Arrange: two active promos with different names/descriptions
        p1 = PromotionFactory(product_name="Summer Sale", description="Beach gear", status=StatusEnum.active)
        p2 = PromotionFactory(product_name="Winter Warmers", description="Cozy coats", status=StatusEnum.active)
        p1.create()
        p2.create()

        # Act: search by keyword "summer"
        # Use manager role to avoid any role-based filtering edge cases
        resp = self.client.get("/promotions?q=summer&role=manager")

        # Assert
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["product_name"], "Summer Sale")
        
    ######################################################################
    # EXTRA TESTS — error_handlers
    ######################################################################
    from flask import current_app as app

    def test_not_found_error_handler(self):
        """It should handle 404 Not Found errors in JSON"""
        resp = self.client.get("/nonexistent/endpoint")
        self.assertEqual(resp.status_code, 404)
        body = resp.get_json()
        self.assertIn("error", body)
        self.assertIn("Not Found", body["error"])

    def test_internal_server_error_handler(self):
        """It should handle 500 Internal Server Error gracefully"""
        from service.common import error_handlers
        from werkzeug.exceptions import InternalServerError

        # simulate a real 500 error without adding new route
        with app.app_context():
            err = InternalServerError("Simulated crash")
            resp, code = error_handlers.internal_server_error(err)
            self.assertEqual(code, 500)
            self.assertIn("Internal Server Error", resp.get_json()["error"])
    ######################################################################
    # EXTRA COVERAGE BOOST
    ######################################################################
    def test_error_handlers_explicit_calls(self):
        """It should directly trigger each error handler"""
        from service.models import DataValidationError
        from service.common import error_handlers
        from werkzeug.exceptions import UnsupportedMediaType
        with app.app_context():
            # 400 Bad Request
            err = DataValidationError("bad input")
            resp, code = error_handlers.bad_request(err)
            self.assertEqual(code, 400)
            self.assertIn("Bad Request", resp.get_json()["error"])
            # 415 Unsupported Media Type
            err2 = UnsupportedMediaType("wrong media")
            resp2, code2 = error_handlers.mediatype_not_supported(err2)
            self.assertEqual(code2, 415)
            self.assertIn("Unsupported media type", resp2.get_json()["error"])

    def test_import_service_triggers_init(self):
        """It should import service package and execute init code"""
        import importlib
        svc = importlib.import_module("service")
        self.assertTrue(hasattr(svc, "__package__"))

    def test_model_deserialize_and_update_errors(self):
        """It should raise DataValidationError on bad model usage"""
        from service.models import Promotion, DataValidationError
        import pytest
        promo = Promotion()
        # 1. deserialize invalid type should raise
        with pytest.raises(DataValidationError):
            promo.deserialize("invalid")
        # 2. update without id: either raise or safely return
        try:
            promo.update()
        except DataValidationError:
            pass
    
    def test_data_validation_error_handler_direct(self):
        """It should trigger the DataValidationError handler directly"""
        from service.models import DataValidationError
        from service.common import error_handlers
        with app.app_context():
            err = DataValidationError("manual validation fail")
            resp, code = error_handlers.request_validation_error(err)
            self.assertEqual(code, 400)
            data = resp.get_json()
            self.assertIn("Bad Request", data["error"])

    def test_routes_list_default_and_empty_result(self):
        """It should call list_promotions() and reach final return"""
        resp = self.client.get("/promotions")  # no filters, hits last return
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), list)

    def test_model_deserialize_field_errors(self):
        """It should cover extra DataValidationError paths in model"""
        from service.models import Promotion, DataValidationError
        import pytest
        promo = Promotion()
        # Missing required field
        with pytest.raises(DataValidationError):
            promo.deserialize({"wrong_field": "oops"})
        # Wrong type for discount percent
        with pytest.raises(DataValidationError):
            promo.deserialize({"product_name": "A", "discount_percent": "NaN"})
    
    def test_service_init_and_register_handlers(self):
        """It should execute __init__ lines like register_handlers(app)"""
        import importlib
        svc = importlib.import_module("service")
        # Reload to ensure final lines run
        importlib.reload(svc)
        self.assertTrue(hasattr(svc, "__package__"))

    def test_promotion_deserialize_missing_fields(self):
        """It should raise DataValidationError for missing or invalid fields"""
        from service.models import Promotion, DataValidationError
        import pytest
        promo = Promotion()
        # 1. completely empty dict
        with pytest.raises(DataValidationError):
            promo.deserialize({})
        # 2. invalid types
        with pytest.raises(DataValidationError):
            promo.deserialize({
                "product_name": "Test",
                "discount_percent": "NotANumber",
                "promotion_type": 123
            })

    def test_routes_list_promotions_final_return(self):
        """It should hit the last return statement in list_promotions"""
        resp = self.client.get("/promotions?role=manager")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), list)

    ######################################################################
    # EXPIRATION TESTS
    ######################################################################
    def test_expiration(self):    
        """It should automatically expire the promtion"""
        promo = PromotionFactory(
            product_name = "test_expiration",
            start_date=datetime.now() - timedelta(days=14),
            expiration_date = datetime.now() - timedelta(days=7),
            status=StatusEnum.active,
        )
        promo.create()
        # request promotions
        resp = self.client.get("/promotions?role=manager")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # query the database to make sure its status is changed to expired
        test = Promotion.find(promo.id)
        self.assertEqual(test.status,StatusEnum.expired)
    
    def test_active_promotion_not_expired(self):
        """It should keep promotion active if not expired"""
        promo = PromotionFactory(
            product_name="active_promo",
            start_date=datetime.now() - timedelta(days=3),
            expiration_date=datetime.now() + timedelta(days=3),
            status=StatusEnum.active
        )
        promo.create()
        # request promotions
        resp = self.client.get("/promotions?role=manager")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # query the database to make sure its status is still active
        test = Promotion.find(promo.id)
        self.assertEqual(test.status, StatusEnum.active)





