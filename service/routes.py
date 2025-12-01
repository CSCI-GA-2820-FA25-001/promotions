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

######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
######################################################################


"""
RESTX version of Promotions API routes
"""


import logging
from datetime import datetime
from functools import wraps
from flask import request
from flask import current_app as app
from flask_restx import Resource
from flask_restx import Api
from service.models import Promotion, StatusEnum, db
from service.common import status


# Document the type of authorization required
authorizations = {"apikey": {"type": "apiKey", "in": "header", "name": "X-Api-Key"}}

api = Api(
    app,
    version="1.0",
    title="Promotions API",
    description="RESTX API for Promotions Service",
    doc="/apidocs",  # default also could use doc='/apidocs/'
    authorizations=authorizations,
    prefix="/api",
)
logger = logging.getLogger("flask.app")


######################################################################
# INDEX
######################################################################
@app.route("/", methods=["GET"])
def index():
    """Root URL for the Promotions microservice"""
    logger.info("Root URL accessed.")
    return app.send_static_file("index.html")


######################################################################
# CREATE / GET ALL
######################################################################
@api.route("/promotions")
class PromotionCollection(Resource):
    """Handles /api/promotions"""

    @api.doc("list_promotions")
    def get(self):
        """List promotions with role, keyword, and date filters"""
        role = (
            request.headers.get("X-Role") or request.args.get("role", "customer")
        ).lower()
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        keyword = request.args.get("q") or request.args.get("keyword")

        # auto expire
        expired = Promotion.query.filter(
            Promotion.expiration_date < datetime.now(),
            Promotion.status == StatusEnum.active,
        ).all()
        for pro in expired:
            pro.status = StatusEnum.expired
            pro.update()

        if role == "customer":
            query = Promotion.query.filter(Promotion.status == StatusEnum.active)
        elif role == "supplier":
            query = Promotion.query.filter(
                Promotion.status.in_([StatusEnum.active, StatusEnum.expired])
            )
        elif role == "manager":
            query = Promotion.query
        else:
            return (
                {"error": "Bad Request", "message": "Invalid role value"},
                status.HTTP_400_BAD_REQUEST,
            )

        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                (Promotion.product_name.ilike(like))
                | (Promotion.description.ilike(like))
            )

        try:
            if start_date_str and end_date_str:
                start_date = datetime.fromisoformat(
                    start_date_str.replace("Z", "+00:00")
                )
                end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                query = query.filter(
                    Promotion.start_date >= start_date,
                    Promotion.expiration_date <= end_date,
                )
        except ValueError:
            return (
                {"error": "Bad Request", "message": "Invalid date format"},
                status.HTTP_400_BAD_REQUEST,
            )

        result = [p.serialize() for p in query.all()]
        return result, status.HTTP_200_OK

    @api.doc("create_promotion")
    # @api.expect(promotion_model)
    def post(self):
        """Create a new promotion"""
        if not request.is_json:
            return (
                {
                    "error": "Unsupported Media Type",
                    "message": "Content-Type must be application/json",
                },
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        promotion, error_code, error_type, error_message = (
            Promotion.create_promotion_with_error_handling(request.get_json())
        )

        if error_code:
            return {"error": error_type, "message": error_message}, error_code

        location_url = api.url_for(
            PromotionResource,
            promotion_id=promotion.id,
            _external=True,
        )

        return (
            promotion.serialize(),
            status.HTTP_201_CREATED,
            {"Location": location_url},
        )


######################################################################
# READ / UPDATE / DELETE
######################################################################
@api.route("/promotions/<int:promotion_id>")
@api.response(404, "Promotion not found")
class PromotionResource(Resource):
    """Handles /api/promotions/<promotion_id>"""

    @api.doc("get_promotion")
    def get(self, promotion_id):
        """Retrieve a single promotion"""
        promotion = Promotion.find(promotion_id)
        if not promotion:
            return (
                {
                    "error": "Not Found",
                    "message": f"Promotion with id '{promotion_id}' was not found.",
                },
                status.HTTP_404_NOT_FOUND,
            )
        return promotion.serialize(), status.HTTP_200_OK

    @api.doc("update_promotion")
    # @api.expect(promotion_model)
    def put(self, promotion_id):
        """Update a promotion"""
        if not request.is_json:
            return (
                {
                    "error": "Unsupported Media Type",
                    "message": "Content-Type must be application/json",
                },
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        promotion, error_code, error_type, error_message = (
            Promotion.update_promotion_with_error_handling(
                promotion_id, request.get_json()
            )
        )

        if error_code:
            return {"error": error_type, "message": error_message}, error_code

        return promotion.serialize(), status.HTTP_200_OK

    @api.doc("delete_promotion")
    def delete(self, promotion_id):
        """Delete a promotion"""
        promotion = Promotion.find(promotion_id)

        if not promotion:
            return "", status.HTTP_204_NO_CONTENT

        if promotion.status == StatusEnum.active:
            return (
                {"error": "Conflict", "message": "Cannot delete active promotion"},
                status.HTTP_409_CONFLICT,
            )

        promotion.delete()
        return "", status.HTTP_204_NO_CONTENT


######################################################################
# DUPLICATE ACTION
######################################################################
@api.route("/promotions/<int:promotion_id>/duplicate")
class PromotionDuplicate(Resource):
    """POST /api/promotions/<id>/duplicate"""

    @api.doc("duplicate_promotion")
    def post(self, promotion_id):
        """Duplicate an existing promotion (Action)"""
        role = request.headers.get("X-Role")
        if not role:
            return (
                {"error": "Unauthorized", "message": "Authentication required"},
                status.HTTP_401_UNAUTHORIZED,
            )

        if role.lower() != "administrator":
            return (
                {
                    "error": "Forbidden",
                    "message": "Administrator privileges required to duplicate promotions",
                },
                status.HTTP_403_FORBIDDEN,
            )

        if not request.is_json:
            return (
                {
                    "error": "Unsupported Media Type",
                    "message": "Content-Type must be application/json",
                },
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        new_promotion, error_code, error_type, error_message = (
            Promotion.duplicate_promotion_with_error_handling(promotion_id)
        )

        if error_code:
            return {"error": error_type, "message": error_message}, error_code

        location_url = api.url_for(
            PromotionResource,
            promotion_id=new_promotion.id,
            _external=True,
        )
        return (
            new_promotion.serialize(),
            status.HTTP_201_CREATED,
            {"Location": location_url},
        )


######################################################################
# RESET DATABASE (BDD)
######################################################################
@api.route("/promotions/reset")
class PromotionReset(Resource):
    """DELETE /api/promotions/reset"""

    @api.doc("reset_promotions")
    def delete(self):
        """DELETE the target"""
        Promotion.query.delete()
        db.session.commit()
        return "", status.HTTP_204_NO_CONTENT


######################################################################
# HEALTH CHECK
######################################################################
@api.route("/health")
class Health(Resource):
    """ Health /api.health"""

    def get(self):
        """Test Health"""
        return {"status": "OK"}, status.HTTP_200_OK
