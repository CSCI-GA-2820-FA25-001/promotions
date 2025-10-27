"""
Models for YourResourceModel

All of the models are stored in this module
"""

import logging
from datetime import datetime
from decimal import Decimal
from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Index, Enum as SQLEnum, func
logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""

    def __init__(self, message):
        """Create an instance with a meaningful error message"""
        super().__init__(message)


class DiscountTypeEnum(str, Enum):
    """Enumeration for discount types"""
    amount = "amount"  # pylint: disable=invalid-name
    percent = "percent"  # pylint: disable=invalid-name


class PromotionTypeEnum(str, Enum):
    """Enumeration for promotion types"""
    discount = "discount"  # pylint: disable=invalid-name
    other = "other"  # pylint: disable=invalid-name


class StatusEnum(str, Enum):
    """Enumeration for promotion statuses"""
    draft = "draft"  # pylint: disable=invalid-name
    active = "active"  # pylint: disable=invalid-name
    expired = "expired"  # pylint: disable=invalid-name
    deactivated = "deactivated"  # pylint: disable=invalid-name
    deleted = "deleted"  # pylint: disable=invalid-name


class Promotion(db.Model):  # pylint: disable=too-many-instance-attributes
    """Promotion model for managing promotional offers"""
    __tablename__ = "promotions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(1024), nullable=True)
    original_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_value = db.Column(db.Numeric(10, 2), nullable=True)
    discount_type = db.Column(SQLEnum(DiscountTypeEnum), nullable=True)
    promotion_type = db.Column(SQLEnum(PromotionTypeEnum), nullable=False)
    start_date = db.Column(db.DateTime, nullable=True, default=datetime.now)
    expiration_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(SQLEnum(StatusEnum), nullable=False, default=StatusEnum.draft)
    # pylint: disable=not-callable
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    # pylint: disable=not-callable
    updated_at = db.Column(
        db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    @property
    def discounted_price(self):
        """Calculate the discounted price based on discount type and value"""
        if self.promotion_type != PromotionTypeEnum.discount or not self.discount_value:
            return self.original_price
        if self.discount_type == DiscountTypeEnum.amount:
            return max(self.original_price - self.discount_value, 0)
        if self.discount_type == DiscountTypeEnum.percent:
            return max(Decimal(self.original_price) * Decimal(1 - self.discount_value / 100), 0)
        return self.original_price

    def create(self):
        """Create a new promotion in the database"""
        logger.info("Creating %s", self.product_name)
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self)
            raise DataValidationError(e) from e

    def update(self):
        """Update an existing promotion in the database"""
        logger.info("update %s", self.product_name)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self)
            raise DataValidationError(e) from e

    def delete(self):
        """Delete a promotion from the database"""
        logger.info("delete %s", self.product_name)
        db.session.delete(self)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self)
            raise DataValidationError(e) from e

    def serialize(self):
        """Serializes a Promotion into a JSON-friendly dictionary"""
        return {
            "id": self.id,
            "product_name": self.product_name,
            "description": self.description,
            "original_price": float(self.original_price),
            "discount_value": float(self.discount_value) if self.discount_value is not None else None,
            "discount_type": self.discount_type.value if self.discount_type else None,
            "promotion_type": self.promotion_type.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "expiration_date": self.expiration_date.isoformat(),
            "status": self.status.value,
            "discounted_price": float(self.discounted_price),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def deserialize(self, data):  # noqa: C901
        """
        Deserializes a Promotion from a dictionary

        Args:
            data (dict): A dictionary containing the promotion data
        """
        try:
            required_fields = ["product_name", "original_price", "promotion_type", "expiration_date"]
            for field in required_fields:
                if field not in data:
                    raise DataValidationError(f"Missing required field: {field}")
            if not isinstance(data["product_name"], str):
                raise DataValidationError("Invalid data type for 'product_name'; expected string")
            if not isinstance(data["original_price"], (int, float, Decimal)):
                raise DataValidationError("Invalid data type for 'original_price'; expected numeric")
            if data.get("discount_value") is not None and not isinstance(data["discount_value"], (int, float, Decimal)):
                raise DataValidationError("Invalid data type for 'discount_value'; expected numeric")
            if data.get("description") and not isinstance(data["description"], str):
                raise DataValidationError("Invalid data type for 'description'; expected string")
            if data.get("promotion_type") == PromotionTypeEnum.other and data.get("discount_value") is not None:
                raise DataValidationError("the discount_value should be None")
            if data.get("promotion_type") == PromotionTypeEnum.other and data.get("discount_type") is not None:
                raise DataValidationError("the discount_type should be None")
            self.product_name = data["product_name"]
            self.description = data.get("description")
            self.original_price = data["original_price"]
            self.discount_value = data.get("discount_value")
            self.discount_type = DiscountTypeEnum(data["discount_type"]) if data.get("discount_type") else None
            self.promotion_type = PromotionTypeEnum(data["promotion_type"]) if data.get("promotion_type") else None
            self.start_date = datetime.fromisoformat(data["start_date"]) if data.get("start_date") else datetime.now()
            self.expiration_date = datetime.fromisoformat(data["expiration_date"])
            self.status = StatusEnum(data["status"]) if data.get("status") else StatusEnum.draft

        except KeyError as error:
            raise DataValidationError(f"Missing required field: {error.args[0]}") from error
        except ValueError as error:
            raise DataValidationError(f"Invalid field value: {error}") from error
        except TypeError as error:
            raise DataValidationError(f"Invalid input data type: {error}") from error
        return self

    __table_args__ = (
        Index("ix_promotions_status", "status"),
        Index("ix_promotions_expiration_date", "expiration_date"),
        Index("ix_promotions_name", "product_name"),
        Index("ix_promotions_type", "promotion_type"),
        Index("ix_promotions_discount_type", "discount_type"),
        CheckConstraint("original_price > 0", name="chk_original_price_positive"),
        CheckConstraint(
            "(discount_type IS NULL AND discount_value IS NULL) OR "
            "(discount_type='amount' AND discount_value <= original_price) OR "
            "(discount_type='percent' AND discount_value >= 0 AND discount_value <= 100)",
            name="chk_discount_value_valid"
        ),
        CheckConstraint(
            "expiration_date >= start_date",
            name="chk_expiration_after_start"
        ),
        CheckConstraint(
            "(promotion_type='other' AND discount_value IS NULL AND discount_type IS NULL)"
            "OR (promotion_type = 'discount')",
            name="chk_promotion_type_after_start"
        ),
    )

    @classmethod
    def all(cls):
        """return all the Promotion fields"""
        logger.info("Processing all YourResourceModels")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a YourResourceModel by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.session.get(cls, by_id)

    @classmethod
    def find_by_name(cls, name):
        """Find Promotions by product_name."""
        return cls.query.filter_by(product_name=name).all()

    @classmethod
    def find_by_status(cls, status):
        """Find Promotions by product_name."""
        return cls.query.filter_by(status=status).all()

    @classmethod
    def find_by_discount_type(cls, discount_type):
        """Find Promotions by product_name."""
        return cls.query.filter_by(discount_type=discount_type).all()

    @classmethod
    def find_by_expiration_date(cls, expiration_date):
        """Find Promotions by product_name."""
        return cls.query.filter_by(expiration_date=expiration_date).all()

    @classmethod
    def find_by_promotion_type(cls, promotion_type):
        """Find Promotions by product_name."""
        return cls.query.filter_by(promotion_type=promotion_type).all()

    @classmethod
    def duplicate_promotion(cls, original_id, override_data=None):
        """Duplicate a promotion with optional overrides and proper error handling"""
        from flask import request  # pylint: disable=import-outside-toplevel

        # Find the original promotion
        original_promotion = cls.find(original_id)
        if not original_promotion:
            raise DataValidationError(f"Promotion with ID {original_id} not found")

        # Get override data from request if not provided
        if override_data is None:
            override_data = request.get_json() or {}
        # Create new promotion data by copying from original and applying overrides
        # Handle product_name - if not overridden, make it unique by appending timestamp
        product_name_override = override_data.get("product_name")
        if product_name_override:
            new_product_name = product_name_override
        else:
            # Make the product name unique by appending timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_product_name = f"{original_promotion.product_name}_copy_{timestamp}"

        new_promotion_data = {
            "product_name": new_product_name,
            "description": override_data.get("description", original_promotion.description),
            "original_price": override_data.get("original_price", float(original_promotion.original_price)),
            "discount_value": override_data.get(
                "discount_value",
                (float(original_promotion.discount_value) if original_promotion.discount_value else None),
            ),
            "discount_type": override_data.get(
                "discount_type",
                (original_promotion.discount_type.value if original_promotion.discount_type else None),
            ),
            "promotion_type": override_data.get("promotion_type", original_promotion.promotion_type.value),
            "expiration_date": override_data.get("expiration_date", original_promotion.expiration_date.isoformat()),
        }

        # Only add start_date if it exists in original or override
        start_date_override = override_data.get("start_date")
        if start_date_override:
            new_promotion_data["start_date"] = start_date_override
        elif original_promotion.start_date:
            new_promotion_data["start_date"] = original_promotion.start_date.isoformat()

        # Create the new promotion using deserialize
        logger.info("Creating promotion with data: %s", new_promotion_data)
        new_promotion = cls()
        new_promotion.deserialize(new_promotion_data)
        new_promotion.create()

        return new_promotion

    @classmethod
    def create_promotion_with_error_handling(cls, data):
        """Create a promotion with comprehensive error handling and HTTP status classification"""
        try:
            promotion = cls()
            promotion.deserialize(data)
            promotion.create()
            return promotion, None, None, None  # success, no error
        except DataValidationError as err:
            # Classify the error and return error info instead of raising
            status_code, error_type = cls.classify_validation_error(err)
            return None, status_code, error_type, str(err)

    @classmethod
    def update_promotion_with_error_handling(cls, promotion_id, data):
        """Update a promotion with comprehensive error handling and HTTP status classification"""
        try:
            promotion = cls.find(promotion_id)
            if not promotion:
                return None, 404, "Not Found", f"Promotion with ID {promotion_id} not found"

            promotion.deserialize(data)
            promotion.update()
            return promotion, None, None, None  # success, no error
        except DataValidationError as err:
            # Classify the error and return error info instead of raising
            status_code, error_type = cls.classify_validation_error(err)
            return None, status_code, error_type, str(err)

    @classmethod
    def duplicate_promotion_with_error_handling(cls, original_id, override_data=None):
        """Duplicate a promotion with comprehensive error handling and HTTP status classification"""
        try:
            promotion = cls.duplicate_promotion(original_id, override_data)
            return promotion, None, None, None  # success, no error
        except DataValidationError as err:
            # Classify the error and return error info instead of raising
            status_code, error_type = cls.classify_duplicate_error(err)
            return None, status_code, error_type, str(err)

    @staticmethod
    def classify_validation_error(error):
        """Classify DataValidationError from create/update operations into appropriate HTTP status codes"""
        error_message = str(error).lower()

        # Handle not found errors (404)
        if "not found" in error_message:
            return 404, "Not Found"

        # Handle duplicate name conflicts (409)
        if "duplicate" in error_message or "unique" in error_message or "1062" in error_message:
            return 409, "Conflict"

        # Handle business logic validation errors (422)
        if any(keyword in error_message for keyword in [
            "should be", "cannot", "discount_value should be", "discount_type should be",
            "chk_discount_value_valid", "chk_original_price_positive",
            "chk_expiration_after_start", "chk_promotion_type_after_start"
        ]):
            return 422, "Unprocessable Entity"

        # Handle other validation errors (400)
        return 400, "Bad Request"

    @staticmethod
    def classify_duplicate_error(error):
        """Classify DataValidationError from duplicate operation into appropriate HTTP status codes"""
        error_message = str(error).lower()

        # Handle not found errors (404)
        if "not found" in error_message:
            return 404, "Not Found"

        # Handle duplicate name conflicts (409)
        if "duplicate" in error_message or "unique" in error_message or "1062" in error_message:
            return 409, "Conflict"

        # Handle business logic validation errors (422)
        if any(keyword in error_message for keyword in [
            "should be", "cannot", "discount_value should be", "discount_type should be",
            "chk_discount_value_valid", "chk_original_price_positive",
            "chk_expiration_after_start", "chk_promotion_type_after_start"
        ]):
            return 422, "Unprocessable Entity"

        # Handle other validation errors (400)
        return 400, "Bad Request"
