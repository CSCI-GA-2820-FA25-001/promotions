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
YourResourceModel Service

This service implements a REST API that allows you to Create, Read, Update
and Delete YourResourceModel
"""

import logging
from flask import jsonify, request, url_for
from flask import current_app as app
from service.models import Promotion, StatusEnum, DataValidationError
from service.common import status
from datetime import datetime


logger = logging.getLogger("flask.app")


######################################################################
# GET INDEX
######################################################################
@app.route("/", methods=["GET"])
def index():
    """Root URL for the Promotions microservice"""
    logger.info("Root URL accessed.")
    response = {
        "service": "Promotions REST API Service",
        "version": "1.0",
        "description": "This service allows CRUD operations on promotions",
        "list_url": url_for("list_promotions", _external=True),
    }
    return jsonify(response), status.HTTP_200_OK

######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
# CREATE
######################################################################


@app.route("/promotions", methods=["POST"])
def create_promotion():
    """Create a new promotion"""
    if not request.is_json:
        return jsonify(error="Unsupported Media Type",
                       message="Content-Type must be application/json"), status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        data = request.get_json()
        promotion = Promotion()
        promotion.deserialize(data)
        promotion.create()
        location_url = url_for("get_promotion", promotion_id=promotion.id, _external=True)
        return jsonify(promotion.serialize()), status.HTTP_201_CREATED, {"Location": location_url}
    except DataValidationError as err:
        return jsonify(error="Bad Request", message=str(err)), status.HTTP_400_BAD_REQUEST


######################################################################
# READ
######################################################################
@app.route("/promotions/<int:promotion_id>", methods=["GET"])
def get_promotion(promotion_id):
    """Read a promotion"""
    promotion = Promotion.find(promotion_id)
    if not promotion:
        return jsonify(error="Not Found",
                       message=f"Promotion with id '{promotion_id}' was not found."), status.HTTP_404_NOT_FOUND
    return jsonify(promotion.serialize()), status.HTTP_200_OK


######################################################################
# UPDATE
######################################################################
@app.route("/promotions/<int:promotion_id>", methods=["PUT"])
def update_promotion(promotion_id):
    """Update a promotion"""
    promotion = Promotion.find(promotion_id)
    if not promotion:
        return jsonify(error="Not Found",
                       message=f"Promotion with id '{promotion_id}' was not found."), status.HTTP_404_NOT_FOUND
    if not request.is_json:
        return jsonify(error="Unsupported Media Type",
                       message="Content-Type must be application/json"), status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        promotion.deserialize(request.get_json())
        promotion.update()
        return jsonify(promotion.serialize()), status.HTTP_200_OK
    except DataValidationError as err:
        return jsonify(error="Bad Request", message=str(err)), status.HTTP_400_BAD_REQUEST


######################################################################
# DELETE
######################################################################
@app.route("/promotions/<int:promotion_id>", methods=["DELETE"])
def delete_promotion(promotion_id):
    """Delete a promotion"""
    promotion = Promotion.find(promotion_id)
    if not promotion:
        # Idempotent delete — return 204 even if not found
        return "", status.HTTP_204_NO_CONTENT

    # Check for active promotions before deleting
    if promotion.status == StatusEnum.active:
        return (
            jsonify(error="Conflict", message="Cannot delete active promotion"),
            status.HTTP_409_CONFLICT,
        )

    # Proceed with deletion
    promotion.delete()
    return "", status.HTTP_204_NO_CONTENT


######################################################################
# LIST
######################################################################
@app.route("/promotions", methods=["GET"])
def list_promotions():
    """List promotions filtered by role and optionally by date range"""
    role = request.args.get("role", "customer").lower()
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    # Step 1: Filter by role
    if role == "customer":
        promotions = Promotion.query.filter_by(status=StatusEnum.active)
    elif role == "supplier":
        promotions = Promotion.query.filter(
            Promotion.status.in_([StatusEnum.active, StatusEnum.expired])
        )
    elif role == "manager":
        promotions = Promotion.query
    else:
        return jsonify(error="Bad Request", message="Invalid role value"), status.HTTP_400_BAD_REQUEST

    # Step 2: Optional date filtering
    try:
        if start_date_str and end_date_str:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
            promotions = promotions.filter(
                Promotion.start_date >= start_date,
                Promotion.expiration_date <= end_date
            )
    except ValueError:
        # if date parsing fails
        return jsonify(error="Bad Request", message="Invalid date format"), status.HTTP_400_BAD_REQUEST

    # Step 3: Return results
    result = [p.serialize() for p in promotions.all()]
    return jsonify(result), status.HTTP_200_OK

######################################################################
# METHOD NOT ALLOWED
######################################################################


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle method not allowed"""
    return jsonify(error="Method Not Allowed", message=str(error)), status.HTTP_405_METHOD_NOT_ALLOWED
