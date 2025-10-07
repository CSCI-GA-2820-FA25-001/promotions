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
from service.models import Promotion, db #YourResourceModel
from service.common import status  # HTTP Status Codes
import logging


logger = logging.getLogger("flask.app")


######################################################################
# GET INDEX (#10 Root URL)
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    logger.info("Root URL accessed.")
    return (
        jsonify(
            name="Promotions REST API Service",
            version="1.0",
            endpoints={
                "list_promotions": url_for("list_promotions", _external=True),
            },
        ),
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################

# Todo: Place your REST API code here ...

######################################################################
# LIST PROMOTIONS (#8)
######################################################################
@app.route("/promotions", methods=["GET"])
def list_promotions():
    """
    Returns a list of all promotions in JSON format
    GET /promotions
    """
    logger.info("Request for promotion list received.")
    promotions = Promotion.query.all()
    results = [promo.serialize() for promo in promotions]
    return jsonify(results), status.HTTP_200_OK
