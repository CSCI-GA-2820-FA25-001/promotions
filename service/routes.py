######################################################################
# Copyright 2016, 2024 John J. Rofrano
######################################################################

"""
Promotions Service with Swagger

Paths:
------
GET / - Displays a UI
GET /promotions - Returns a list all of the Promotions
GET /promotions/{id} - Returns the Promotions with a given id number
POST /promotions - creates a new Promotions record in the database
PUT /promotions/{id} - updates a Promotions record in the database
DELETE /promotions/{id} - deletes a Promotions record in the database
POST /promotions/{id} - duplicates a Promotions record in the database
"""

import logging
from datetime import datetime
from flask import request
from flask import current_app as app
from flask_restx import Resource, Api, fields
from werkzeug.exceptions import NotFound, BadRequest, MethodNotAllowed, UnsupportedMediaType, InternalServerError
from service.models import Promotion, StatusEnum, db, DiscountTypeEnum, PromotionTypeEnum
from service.common import status


logger = logging.getLogger("flask.app")


######################################################################
# Helper Functions
######################################################################
def error_response(error: str, message: str, code: int):
    """Return a standardized error response dictionary."""
    return {"error": error, "message": message}, code


######################################################################
# Swagger & RESTX API Initialization
######################################################################

authorizations = {
    "apikey": {"type": "apiKey", "in": "header", "name": "X-Role"}
}

api = Api(
    app,
    version="1.0.0",
    title="Promotions API",
    description="RESTX API for Promotions Service",
    doc="/apidocs",
    authorizations=authorizations,
    prefix="/api",
    default="Promotions",
    default_label="Promotions API operations"
)

promotion_create_model = api.model(
    "Promotion",
    {
        "id": fields.Integer(required=True, description="ID for the promotion"),
        "product_name": fields.String(required=True, description="The name of the promotion's product"),
        "description": fields.String(
            required=False, description="Description of the Promotion"
        ),
        "original_price": fields.Float(required=True, description="Original price of the product"),
        "discount_value": fields.Float(required=False, description="Value of the discount"),
        "discount_type": fields.String(
            required=False, enum=DiscountTypeEnum._member_names_, description="Type of the discount"
        ),
        "promotion_type": fields.String(
            required=True, enum=PromotionTypeEnum._member_names_, description="Type of the promotion"
        ),
        "start_date": fields.Date(required=False, description="Start date"),
        "expiration_date": fields.Date(required=True, description="Expiration date"),
        "status": fields.String(
            required=True, enum=StatusEnum._member_names_, description="Status of the promotion"
        ),
    },
)


######################################################################
# RESTX JSON Error Handlers (replaces HTML error handlers)
######################################################################
@api.errorhandler(NotFound)
def handle_not_found(error):
    """Handle 404 errors with JSON response"""
    return {"error": "Not Found", "message": str(error)}, 404


@api.errorhandler(BadRequest)
def handle_bad_request(error):
    """Handle 400 errors with JSON response"""
    return {"error": "Bad Request", "message": str(error)}, 400


@api.errorhandler(MethodNotAllowed)
def handle_method_not_allowed(error):
    """Handle 405 errors with JSON response"""
    return {"error": "Method not Allowed", "message": str(error)}, 405


@api.errorhandler(UnsupportedMediaType)
def handle_unsupported_media_type(error):
    """Handle 415 errors with JSON response"""
    return {"error": "Unsupported Media Type", "message": str(error)}, 415


@api.errorhandler(InternalServerError)
def handle_internal_server_error(error):
    """Handle 500 errors with JSON response"""
    logger.error("Internal Server Error: %s", error)
    return {"error": "Internal Server Error", "message": str(error)}, 500


######################################################################
# Index Route
######################################################################
@app.route("/", methods=["GET"])
def index():
    """Root URL for the Promotions microservice"""
    return app.send_static_file("index.html")


######################################################################
# Promotions Collection
######################################################################
@api.route("/promotions")
class PromotionCollection(Resource):
    """Handles operations on the promotions collection."""

    @api.doc("list_promotions")
    def get(self):
        """List promotions with filtering by role, keyword, and date."""
        # -------- Auto-expire promotions --------
        expired = Promotion.query.filter(
            Promotion.expiration_date < datetime.now(),
            Promotion.status == StatusEnum.active,
        ).all()

        for pro in expired:
            pro.status = StatusEnum.expired
            pro.update()

        # -------- Role filter --------
        role = request.args.get("role", "customer").lower()
        if role == "customer":
            query = Promotion.query.filter(
                Promotion.status == StatusEnum.active
            )
        elif role == "supplier":
            query = Promotion.query.filter(
                Promotion.status.in_([StatusEnum.active, StatusEnum.expired])
            )
        elif role == "manager":
            query = Promotion.query
        else:
            return error_response(
                "Bad Request",
                "Invalid role value",
                status.HTTP_400_BAD_REQUEST,
            )

        # -------- Keyword filter --------
        keyword = request.args.get("q") or request.args.get("keyword")
        if keyword:
            like_expr = f"%{keyword}%"
            query = query.filter(
                Promotion.product_name.ilike(like_expr)
                | Promotion.description.ilike(like_expr)
            )

        # -------- Date filter --------
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(
                    start_date_str.replace("Z", "+00:00")
                )
                end_date = datetime.fromisoformat(
                    end_date_str.replace("Z", "+00:00")
                )
                query = query.filter(
                    Promotion.start_date >= start_date,
                    Promotion.expiration_date <= end_date,
                )
            except ValueError:
                return error_response(
                    "Bad Request",
                    "Invalid date format",
                    status.HTTP_400_BAD_REQUEST,
                )

        results = [p.serialize() for p in query.all()]
        return results, status.HTTP_200_OK

    @api.doc("create_promotion")
    @api.expect(promotion_create_model)
    def post(self):
        """Create a new promotion."""
        if not request.is_json:
            return error_response(
                "Unsupported Media Type",
                "Content-Type must be application/json",
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        promotion, error_code, error_type, error_message = (
            Promotion.create_promotion_with_error_handling(
                request.get_json()
            )
        )

        if error_code:
            return error_response(error_type, error_message, error_code)

        location_url = api.url_for(
            PromotionResource, promotion_id=promotion.id, _external=True
        )

        return (
            promotion.serialize(),
            status.HTTP_201_CREATED,
            {"Location": location_url},
        )


######################################################################
# Promotion Resource
######################################################################
@api.route("/promotions/<int:promotion_id>")
@api.response(404, "Promotion not found")
class PromotionResource(Resource):
    """Handles CRUD operations on a specific promotion."""

    @api.doc("get_promotion")
    def get(self, promotion_id):
        """Retrieve a promotion by ID."""
        promotion = Promotion.find(promotion_id)
        if not promotion:
            return error_response(
                "Not Found",
                f"Promotion with id '{promotion_id}' was not found.",
                status.HTTP_404_NOT_FOUND,
            )
        return promotion.serialize(), status.HTTP_200_OK

    @api.doc("update_promotion")
    @api.expect(promotion_create_model)
    def put(self, promotion_id):
        """Update an existing promotion."""
        if not request.is_json:
            return error_response(
                "Unsupported Media Type",
                "Content-Type must be application/json",
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        promotion, error_code, error_type, error_message = (
            Promotion.update_promotion_with_error_handling(
                promotion_id, request.get_json()
            )
        )

        if error_code:
            return error_response(error_type, error_message, error_code)

        return promotion.serialize(), status.HTTP_200_OK

    @api.doc("delete_promotion")
    def delete(self, promotion_id):
        """Delete a promotion if it is not active."""
        promotion = Promotion.find(promotion_id)

        if not promotion:
            return "", status.HTTP_204_NO_CONTENT

        if promotion.status == StatusEnum.active:
            return error_response(
                "Conflict",
                "Cannot delete active promotion",
                status.HTTP_409_CONFLICT,
            )

        promotion.delete()
        return "", status.HTTP_204_NO_CONTENT


######################################################################
# Duplicate Promotion
######################################################################
@api.route("/promotions/<int:promotion_id>/duplicate")
class PromotionDuplicate(Resource):
    """Duplicate an existing promotion with optional overrides."""

    @api.doc("duplicate_promotion")
    def post(self, promotion_id):
        """Duplicate a promotion after data validation."""
        # -------- Authentication --------
        role = request.headers.get("X-Role")
        if not role:
            return error_response(
                "Unauthorized",
                "Authentication required",
                status.HTTP_401_UNAUTHORIZED,
            )

        if role.lower() != "administrator":
            return error_response(
                "Forbidden",
                "Administrator privileges required to duplicate promotions",
                status.HTTP_403_FORBIDDEN,
            )

        # -------- Content-Type --------
        if not request.is_json:
            return error_response(
                "Unsupported Media Type",
                "Content-Type must be application/json",
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        # -------- Duplicate --------
        new_promotion, error_code, error_type, error_message = (
            Promotion.duplicate_promotion_with_error_handling(
                promotion_id)
        )

        if error_code:
            return error_response(error_type, error_message, error_code)

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
# Reset Database (BDD Test Helper)
######################################################################
@api.route("/promotions/reset")
class PromotionReset(Resource):
    """Reset all promotions (used for BDD tests)."""

    @api.doc("reset_promotions")
    def delete(self):
        """Delete all promotions in the database."""
        Promotion.query.delete()
        db.session.commit()
        return "", status.HTTP_204_NO_CONTENT


######################################################################
# Health Endpoint
######################################################################
@api.route("/health")
class Health(Resource):
    """Health check endpoint."""

    def get(self):
        """Return service health status."""
        return {"status": "OK"}, status.HTTP_200_OK

@app.route("/health")
def health():
    """Plain health check used by Kubernetes probes."""
    return jsonify(status="OK"), status.HTTP_200_OK
