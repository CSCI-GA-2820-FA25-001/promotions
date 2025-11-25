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
from datetime import datetime
from flask import jsonify, request, url_for
from flask import current_app as app
from service.models import (
    Promotion,
    StatusEnum,
)
from service.common import status


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
        "ui_url": url_for("ui", _external=True),
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
        return (
            jsonify(
                error="Unsupported Media Type",
                message="Content-Type must be application/json",
            ),
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    # Use the model method to handle creation with error handling
    promotion, error_code, error_type, error_message = Promotion.create_promotion_with_error_handling(request.get_json())

    if error_code:
        return (
            jsonify(error=error_type, message=error_message),
            error_code,
        )

    location_url = url_for("get_promotion", promotion_id=promotion.id, _external=True)
    return (
        jsonify(promotion.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


######################################################################
# READ
######################################################################


@app.route("/promotions/<int:promotion_id>", methods=["GET"])
def get_promotion(promotion_id):
    """Read a promotion"""
    promotion = Promotion.find(promotion_id)
    if not promotion:
        return (
            jsonify(
                error="Not Found",
                message=f"Promotion with id '{promotion_id}' was not found.",
            ),
            status.HTTP_404_NOT_FOUND,
        )
    return jsonify(promotion.serialize()), status.HTTP_200_OK


######################################################################
# UPDATE
######################################################################


@app.route("/promotions/<int:promotion_id>", methods=["PUT"])
def update_promotion(promotion_id):
    """Update a promotion"""
    if not request.is_json:
        return (
            jsonify(
                error="Unsupported Media Type",
                message="Content-Type must be application/json",
            ),
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    # Use the model method to handle update with error handling
    promotion, error_code, error_type, error_message = (
        Promotion.update_promotion_with_error_handling(
            promotion_id, request.get_json()
        )
    )

    if error_code:
        return (
            jsonify(error=error_type, message=error_message),
            error_code,
        )

    return jsonify(promotion.serialize()), status.HTTP_200_OK


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
    """List promotions filtered by role and optionally by date range and keyword"""
    role = (
        request.headers.get("X-Role") or request.args.get("role", "customer")
    ).lower()
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    keyword = request.args.get("q") or request.args.get("keyword")

    # the system will automatically check the status of promotion
    expired = Promotion.query.filter(
        Promotion.expiration_date < datetime.now(),
        Promotion.status == StatusEnum.active,
    ).all()
    for pro in expired:
        pro.status = StatusEnum.expired
        pro.update()

    # 1) Base query by role
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
            jsonify(error="Bad Request", message="Invalid role value"),
            status.HTTP_400_BAD_REQUEST,
        )

    # 2) Keyword search (product_name or description)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (Promotion.product_name.ilike(like)) | (Promotion.description.ilike(like))
        )

    # 3) Optional date range filter
    try:
        if start_date_str and end_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            query = query.filter(
                Promotion.start_date >= start_date,
                Promotion.expiration_date <= end_date,
            )
    except ValueError:
        return (
            jsonify(error="Bad Request", message="Invalid date format"),
            status.HTTP_400_BAD_REQUEST,
        )

    # 4) Return results
    result = [p.serialize() for p in query.all()]
    return jsonify(result), status.HTTP_200_OK


######################################################################
# DUPLICATE
######################################################################


@app.route("/promotions/<int:promotion_id>/duplicate", methods=["POST"])
def duplicate_promotion(promotion_id):
    """Duplicate an existing promotion"""
    # Check authentication
    role = request.headers.get("X-Role")
    if not role:
        return (
            jsonify(error="Unauthorized", message="Authentication required"),
            status.HTTP_401_UNAUTHORIZED,
        )

    # Check authorization (only administrators can duplicate)
    if role.lower() != "administrator":
        return (
            jsonify(
                error="Forbidden",
                message="Administrator privileges required to duplicate promotions",
            ),
            status.HTTP_403_FORBIDDEN,
        )

    # Check content type
    if not request.is_json:
        return (
            jsonify(
                error="Unsupported Media Type",
                message="Content-Type must be application/json",
            ),
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    # Use the model method to handle duplication with error handling
    new_promotion, error_code, error_type, error_message = Promotion.duplicate_promotion_with_error_handling(promotion_id)

    if error_code:
        return (
            jsonify(error=error_type, message=error_message),
            error_code,
        )

    # Return the created promotion
    location_url = url_for(
        "get_promotion", promotion_id=new_promotion.id, _external=True
    )
    return (
        jsonify(new_promotion.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )

######################################################################
# health end point
######################################################################


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Kubernetes"""
    return jsonify({"status": "OK"}), status.HTTP_200_OK
