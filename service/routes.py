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

import logging
from datetime import datetime
from flask import jsonify, request
from flask import current_app as app
from flask_restx import Namespace, Resource, fields
from service.models import Promotion, StatusEnum
from service.common import status

logger = logging.getLogger("flask.app")

# Create namespace
api = Namespace("promotions", description="Promotion operations")

# Swagger Model definition
promotion_model = api.model(
    "Promotion",
    {
        "id": fields.Integer(readOnly=True),
        "product_name": fields.String(required=True),
        "description": fields.String(required=True),
        "start_date": fields.String,
        "expiration_date": fields.String,
        "status": fields.String,
    },
)

######################################################################
# INDEX — This should NOT be an API route
######################################################################


@app.route("/", methods=["GET"])
def index():
    """Root URL for UI"""
    return jsonify({
        "service": "Promotions REST API Service",
        "version": "1.0",
        "description": "This service allows CRUD operations on promotions"
    }), status.HTTP_200_OK


######################################################################
# LIST + CREATE COLLECTION
######################################################################


@api.route("")
class PromotionCollection(Resource):
    """Handles listing and creating promotions"""

    @api.doc("list_promotions")
    @api.marshal_list_with(promotion_model)
    def get(self):
        """List promotions with filters"""

        role = request.headers.get("X-Role") or request.args.get("role", "customer")
        role = role.lower()
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        keyword = request.args.get("q") or request.args.get("keyword")

        # Expire outdated promotions
        expired = Promotion.query.filter(
            Promotion.expiration_date < datetime.now(),
            Promotion.status == StatusEnum.active,
        ).all()
        for p in expired:
            p.status = StatusEnum.expired
            p.update()

        # Filter by role
        if role == "customer":
            query = Promotion.query.filter(Promotion.status == StatusEnum.active)
        elif role == "supplier":
            query = Promotion.query.filter(
                Promotion.status.in_([StatusEnum.active, StatusEnum.expired])
            )
        elif role == "manager":
            query = Promotion.query
        else:
            api.abort(400, "Invalid role value")

        # Keyword filter
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                (Promotion.product_name.ilike(like)) |
                (Promotion.description.ilike(like))
            )

        # Date range filter
        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
                query = query.filter(
                    Promotion.start_date >= start_date,
                    Promotion.expiration_date <= end_date,
                )
            except ValueError:
                api.abort(400, "Invalid date format")

        promotions = query.all()
        return promotions, status.HTTP_200_OK

    @api.doc("create_promotion")
    @api.expect(promotion_model)
    @api.marshal_with(promotion_model, code=201)
    def post(self):
        """Create a new promotion"""
        if not request.is_json:
            api.abort(415, "Content-Type must be application/json")

        promotion, error_code, error_type, error_msg = \
            Promotion.create_promotion_with_error_handling(request.get_json())

        if error_code:
            api.abort(error_code, error_msg)

        return promotion, status.HTTP_201_CREATED


######################################################################
# ITEM OPERATIONS: GET / PUT / DELETE
######################################################################


@api.route("/<int:promotion_id>")
class PromotionResource(Resource):

    @api.doc("get_promotion")
    @api.marshal_with(promotion_model)
    def get(self, promotion_id):
        promotion = Promotion.find(promotion_id)
        if not promotion:
            api.abort(404, f"Promotion with id {promotion_id} not found")
        return promotion, status.HTTP_200_OK

    @api.expect(promotion_model)
    @api.marshal_with(promotion_model)
    def put(self, promotion_id):
        if not request.is_json:
            api.abort(415, "Content-Type must be application/json")

        promotion, err_code, err_type, err_msg = \
            Promotion.update_promotion_with_error_handling(
                promotion_id, request.get_json()
            )

        if err_code:
            api.abort(err_code, err_msg)

        return promotion, status.HTTP_200_OK

    def delete(self, promotion_id):
        promotion = Promotion.find(promotion_id)
        if not promotion:
            return "", status.HTTP_204_NO_CONTENT

        if promotion.status == StatusEnum.active:
            api.abort(409, "Cannot delete active promotion")

        promotion.delete()
        return "", status.HTTP_204_NO_CONTENT


######################################################################
# DUPLICATE ACTION
######################################################################


@api.route("/<int:promotion_id>/duplicate")
class DuplicatePromotion(Resource):

    @api.doc("duplicate_promotion")
    @api.marshal_with(promotion_model, code=201)
    def post(self, promotion_id):

        role = request.headers.get("X-Role")
        if not role:
            api.abort(401, "Authentication required")

        if role.lower() != "administrator":
            api.abort(403, "Administrator privileges required")

        if not request.is_json:
            api.abort(415, "Content-Type must be application/json")

        new_promo, err_code, err_type, err_msg = \
            Promotion.duplicate_promotion_with_error_handling(promotion_id)

        if err_code:
            api.abort(err_code, err_msg)

        return new_promo, status.HTTP_201_CREATED


######################################################################
# HEALTH — Keep this as app.route (not part of API)
######################################################################


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK"}), status.HTTP_200_OK
