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

from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from service.models import Promotion, db, StatusEnum, DataValidationError #YourResourceModel
from service.common import status  # HTTP Status Codes
import logging


logger = logging.getLogger("flask.app")


######################################################################
# GET INDEX (#10 Root URL)
######################################################################
@app.route("/", methods=["GET"])
def index():
    """Root URL for the Promotions microservice"""
    logger.info("Root URL accessed.")
    response = {
        "service": "Promotions REST API Service",
        "version": "1.0",
        "description": "This service manages promotions for an eCommerce platform.",
        # ✅ use host_url instead of _external for test consistency
        "list_url": request.host_url.rstrip("/") + url_for("list_promotions"),
    }
    return jsonify(response), status.HTTP_200_OK



######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################

# Todo: Place your REST API code here ...


######################################################################
# LIST PROMOTIONS (#8)
######################################################################
@app.route("/promotions", methods=["GET"])
def list_promotions():
    """List promotions filtered by role"""
    role = request.args.get("role", None)
    logger.debug(f"Role parameter received: {role}")

    if role is None:
        promotions = Promotion.query.all()
    elif role == "customer":
        promotions = Promotion.query.filter_by(status=StatusEnum.active).all()
    elif role == "supplier":
        promotions = Promotion.query.filter(
            Promotion.status.in_([StatusEnum.active, StatusEnum.expired])
        ).all()
    elif role == "manager":
        promotions = Promotion.query.all()
    else:
        # ✅ return JSON instead of abort, to match test expectations
        return jsonify({"message": "Invalid role value"}), status.HTTP_400_BAD_REQUEST

    results = [promo.serialize() for promo in promotions]
    return jsonify(results), status.HTTP_200_OK
