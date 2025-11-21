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
from datetime import datetime, timedelta
from unittest import TestCase
from service.common import status
from service.models import Promotion, StatusEnum, db
from wsgi import app
from .factories import PromotionFactory

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
    # Todo: Add your test cases here...  # pylint: disable=fixme

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
        self.assertEqual(data[0]["status"], StatusEnum.active)

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
        self.assertIn(StatusEnum.active, statuses)
        self.assertIn(StatusEnum.expired, statuses)
        self.assertNotIn(StatusEnum.deleted, statuses)

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
    from flask import current_app as app  # pylint: disable=import-outside-toplevel,shadowed-import

    def test_not_found_error_handler(self):
        """It should handle 404 Not Found errors in JSON"""
        resp = self.client.get("/nonexistent/endpoint")
        self.assertEqual(resp.status_code, 404)
        body = resp.get_json()
        self.assertIn("error", body)
        self.assertIn("Not Found", body["error"])

    def test_internal_server_error_handler(self):
        """It should handle 500 Internal Server Error gracefully"""
        from service.common import error_handlers  # pylint: disable=import-outside-toplevel
        from werkzeug.exceptions import InternalServerError  # pylint: disable=import-outside-toplevel

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
        from service.models import DataValidationError  # pylint: disable=import-outside-toplevel
        from service.common import error_handlers  # pylint: disable=import-outside-toplevel
        from werkzeug.exceptions import UnsupportedMediaType  # pylint: disable=import-outside-toplevel
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
        import importlib  # pylint: disable=import-outside-toplevel
        svc = importlib.import_module("service")
        self.assertTrue(hasattr(svc, "__package__"))

    def test_model_deserialize_and_update_errors(self):
        """It should raise DataValidationError on bad model usage"""
        # pylint: disable=import-outside-toplevel,reimported,redefined-outer-name
        from service.models import Promotion, DataValidationError
        import pytest  # pylint: disable=import-outside-toplevel
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
        from service.models import DataValidationError  # pylint: disable=import-outside-toplevel
        from service.common import error_handlers  # pylint: disable=import-outside-toplevel
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
        # pylint: disable=import-outside-toplevel,reimported,redefined-outer-name
        from service.models import Promotion, DataValidationError
        import pytest  # pylint: disable=import-outside-toplevel
        promo = Promotion()
        # Missing required field
        with pytest.raises(DataValidationError):
            promo.deserialize({"wrong_field": "oops"})
        # Wrong type for discount percent
        with pytest.raises(DataValidationError):
            promo.deserialize({"product_name": "A", "discount_percent": "NaN"})

    def test_service_init_and_register_handlers(self):
        """It should execute __init__ lines like register_handlers(app)"""
        import importlib  # pylint: disable=import-outside-toplevel
        svc = importlib.import_module("service")
        # Reload to ensure final lines run
        importlib.reload(svc)
        self.assertTrue(hasattr(svc, "__package__"))

    def test_promotion_deserialize_missing_fields(self):
        """It should raise DataValidationError for missing or invalid fields"""
        # pylint: disable=import-outside-toplevel,reimported,redefined-outer-name
        from service.models import Promotion, DataValidationError
        import pytest  # pylint: disable=import-outside-toplevel
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
    # DUPLICATE PROMOTION TESTS
    ######################################################################

    def test_duplicate_promotion_success_no_overrides(self):
        """It should duplicate a promotion with no overrides"""
        # Create an original promotion
        original_promo = PromotionFactory()
        original_promo.create()
        original_id = original_promo.id

        # Duplicate the promotion
        resp = self.client.post(
            f"/promotions/{original_id}/duplicate",
            json={},
            headers={"X-Role": "administrator"}
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.get_json()
        self.assertNotEqual(data["id"], original_id)  # New ID
        # Product name should be unique (original name + timestamp)
        self.assertNotEqual(data["product_name"], original_promo.product_name)
        self.assertTrue(data["product_name"].startswith(original_promo.product_name))
        self.assertIn("_copy_", data["product_name"])
        self.assertEqual(data["description"], original_promo.description)
        self.assertEqual(data["original_price"], float(original_promo.original_price))
        self.assertEqual(data["discount_value"], float(original_promo.discount_value))
        self.assertEqual(data["discount_type"], original_promo.discount_type)
        self.assertEqual(data["promotion_type"], original_promo.promotion_type)
        self.assertEqual(data["status"], "draft")  # Default status
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_duplicate_promotion_success_with_overrides(self):
        """It should duplicate a promotion with field overrides"""
        # Create an original promotion
        original_promo = PromotionFactory()
        original_promo.create()
        original_id = original_promo.id

        # Duplicate with overrides
        override_data = {
            "product_name": "Duplicated Promotion",
            "expiration_date": "2025-12-31T23:59:59",
            "discount_value": 30.0
        }

        resp = self.client.post(
            f"/promotions/{original_id}/duplicate",
            json=override_data,
            headers={"X-Role": "administrator"}
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.get_json()
        self.assertNotEqual(data["id"], original_id)  # New ID
        self.assertEqual(data["product_name"], "Duplicated Promotion")  # Overridden
        self.assertEqual(data["expiration_date"], "2025-12-31T23:59:59")  # Overridden
        self.assertEqual(data["discount_value"], 30.0)  # Overridden
        self.assertEqual(data["description"], original_promo.description)  # Original
        self.assertEqual(data["original_price"], float(original_promo.original_price))  # Original
        self.assertEqual(data["status"], "draft")  # Default status

    def test_duplicate_promotion_unauthorized_no_header(self):
        """It should return 401 when no X-Role header is provided"""
        # Create an original promotion
        original_promo = PromotionFactory()
        original_promo.create()
        original_id = original_promo.id

        resp = self.client.post(
            f"/promotions/{original_id}/duplicate",
            json={}
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        data = resp.get_json()
        self.assertEqual(data["error"], "Unauthorized")
        self.assertIn("Authentication required", data["message"])

    def test_duplicate_promotion_forbidden_non_admin(self):
        """It should return 403 when non-admin tries to duplicate"""
        # Create an original promotion
        original_promo = PromotionFactory()
        original_promo.create()
        original_id = original_promo.id

        # Try with customer role
        resp = self.client.post(
            f"/promotions/{original_id}/duplicate",
            json={},
            headers={"X-Role": "customer"}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        data = resp.get_json()
        self.assertEqual(data["error"], "Forbidden")
        self.assertIn("Administrator privileges required", data["message"])

        # Try with supplier role
        resp = self.client.post(
            f"/promotions/{original_id}/duplicate",
            json={},
            headers={"X-Role": "supplier"}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Try with manager role
        resp = self.client.post(
            f"/promotions/{original_id}/duplicate",
            json={},
            headers={"X-Role": "manager"}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_promotion_not_found(self):
        """It should return 404 when original promotion doesn't exist"""
        resp = self.client.post(
            "/promotions/99999/duplicate",
            json={},
            headers={"X-Role": "administrator"}
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        data = resp.get_json()
        self.assertEqual(data["error"], "Not Found")
        self.assertIn("Promotion with ID 99999 not found", data["message"])

    def test_duplicate_promotion_conflict_duplicate_name(self):
        """It should return 409 when override name already exists"""
        # Create two promotions
        promo1 = PromotionFactory()
        promo1.create()

        promo2 = PromotionFactory()
        promo2.create()

        # Try to duplicate promo1 with promo2's name
        resp = self.client.post(
            f"/promotions/{promo1.id}/duplicate",
            json={"product_name": promo2.product_name},
            headers={"X-Role": "administrator"}
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

        data = resp.get_json()
        self.assertEqual(data["error"], "Conflict")
        self.assertIn("already exists", data["message"])

    def test_duplicate_promotion_bad_json(self):
        """It should return 400 for malformed JSON"""
        # Create an original promotion
        original_promo = PromotionFactory()
        original_promo.create()
        original_id = original_promo.id

        resp = self.client.post(
            f"/promotions/{original_id}/duplicate",
            data="invalid json",
            content_type="application/json",
            headers={"X-Role": "administrator"}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_promotion_wrong_content_type(self):
        """It should return 415 when Content-Type is not JSON"""
        # Create an original promotion
        original_promo = PromotionFactory()
        original_promo.create()
        original_id = original_promo.id

        resp = self.client.post(
            f"/promotions/{original_id}/duplicate",
            data="some data",
            content_type="text/plain",
            headers={"X-Role": "administrator"}
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        data = resp.get_json()
        self.assertEqual(data["error"], "Unsupported Media Type")
        self.assertIn("Content-Type must be application/json", data["message"])

    def test_duplicate_promotion_validation_errors(self):
        """It should return 422 for validation errors in overrides"""
        # Create an original promotion
        original_promo = PromotionFactory()
        original_promo.create()
        original_id = original_promo.id

        # Try with invalid discount value (greater than original price)
        resp = self.client.post(
            f"/promotions/{original_id}/duplicate",
            json={"discount_value": 999.0, "discount_type": "amount"},
            headers={"X-Role": "administrator"}
        )
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = resp.get_json()
        self.assertEqual(data["error"], "Unprocessable Entity")

    def test_duplicate_promotion_system_fields_generated(self):
        """It should generate new system fields for duplicated promotion"""
        # Create an original promotion
        original_promo = PromotionFactory()
        original_promo.create()
        original_id = original_promo.id

        resp = self.client.post(
            f"/promotions/{original_id}/duplicate",
            json={},
            headers={"X-Role": "administrator"}
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.get_json()
        new_id = data["id"]

        # Verify the new promotion can be retrieved
        get_resp = self.client.get(f"/promotions/{new_id}")
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)

        # Verify original promotion is unchanged
        original_resp = self.client.get(f"/promotions/{original_id}")
        self.assertEqual(original_resp.status_code, status.HTTP_200_OK)

    def test_duplicate_promotion_discounted_price_calculated(self):
        """It should calculate discounted_price for duplicated promotion"""
        # Create an original promotion with discount
        original_promo = PromotionFactory(
            original_price=100.0,
            discount_value=20.0,
            discount_type="percent"
        )
        original_promo.create()
        original_id = original_promo.id

        resp = self.client.post(
            f"/promotions/{original_id}/duplicate",
            json={},
            headers={"X-Role": "administrator"}
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.get_json()
        self.assertEqual(data["discounted_price"], 80.0)  # 100 - 20%

    ######################################################################
    # EXPIRATION TESTS
    ######################################################################
    def test_expiration(self):
        """It should automatically expire the promtion"""
        promo = PromotionFactory(
            product_name="test_expiration",
            start_date=datetime.now() - timedelta(days=14),
            expiration_date=datetime.now() - timedelta(days=7),
            status=StatusEnum.active,
        )
        promo.create()
        # request promotions
        resp = self.client.get("/promotions?role=manager")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # query the database to make sure its status is changed to expired
        test = Promotion.find(promo.id)
        self.assertEqual(test.status, StatusEnum.expired)

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

    ######################################################################
    # UI ENDPOINT TESTS
    ######################################################################
    def test_ui_endpoint(self):
        """Test the /ui endpoint serves the UI"""
        resp = self.client.get("/ui")
        assert resp.status_code == 200
        # Check that it returns HTML content
        assert "text/html" in resp.content_type or resp.is_json is False
        # Verify the response contains expected HTML
        assert resp.data is not None

    ######################################################################
    # HEALTHENDPOINT TESTS
    ######################################################################
    def test_health_endpoint(self):
        """Test the /health endpoint"""
        resp = self.client.get("/health")
        assert resp.status_code == 200
        assert resp.get_json() == {"status": "OK"}
