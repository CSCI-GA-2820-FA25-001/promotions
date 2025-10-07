"""
Models for YourResourceModel

All of the models are stored in this module
"""

import logging
from datetime import datetime
from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Index, Enum as SQLEnum, func

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class DiscountTypeEnum(str, Enum):
    amount = "amount"
    percent = "percent"

class PromotionTypeEnum(str, Enum):
    discount = "discount"
    other = "other"

class StatusEnum(str, Enum):
    draft = "draft"
    active = "active"
    expired = "expired"
    deactivated = "deactivated"
    deleted = "deleted"

class Promotion(db.Model):
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
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_promotions_status", "status"), #accelerate status search（like WHERE status = 'active'）
        Index("ix_promotions_expiration_date", "expiration_date"), #accelerate expiration_date search
        Index("ix_promotions_name", "product_name"), #accelerate product_name search
        Index("ix_promotions_type", "promotion_type"), #accelerate promotion_type search
        Index("ix_promotions_discount_type", "discount_type"), #accelerate discount_type search
        CheckConstraint("original_price > 0", name="chk_original_price_positive"),
        CheckConstraint(
            "(discount_type IS NULL AND discount_value IS NULL) OR "
            "(discount_type='amount' AND discount_value <= original_price) OR "
            "(discount_type='percent' AND discount_value >= 0 AND discount_value <= 100)",
            name="chk_discount_value_valid"
        ),
        CheckConstraint(
            "expiration_date > start_date",
            name="chk_expiration_after_start"
        ),
        CheckConstraint(
            "(promotion_type='other' AND discount_value IS NULL AND discount_type IS NULL)"
            "OR (promotion_type = 'discount')",
            name="chk_promotion_type_after_start"
        ),
    )

    @property
    def discounted_price(self):
        if self.promotion_type != PromotionTypeEnum.discount or not self.discount_value:
            return self.original_price
        if self.discount_type == DiscountTypeEnum.amount:
            return max(self.original_price - self.discount_value, 0)
        elif self.discount_type == DiscountTypeEnum.percent:
            return max(self.original_price * (1 - self.discount_value / 100), 0)
        return self.original_price
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


class YourResourceModel(db.Model):
    """
    Class that represents a YourResourceModel
    """

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63))

    # Todo: Place the rest of your schema here...

    def __repr__(self):
        return f"<YourResourceModel {self.name} id=[{self.id}]>"

    def create(self):
        """
        Creates a YourResourceModel to the database
        """
        logger.info("Creating %s", self.name)
        self.id = None  # pylint: disable=invalid-name
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating record: %s", self)
            raise DataValidationError(e) from e

    def update(self):
        """
        Updates a YourResourceModel to the database
        """
        logger.info("Saving %s", self.name)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self)
            raise DataValidationError(e) from e

    def delete(self):
        """Removes a YourResourceModel from the data store"""
        logger.info("Deleting %s", self.name)
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error deleting record: %s", self)
            raise DataValidationError(e) from e

    def serialize(self):
        """Serializes a YourResourceModel into a dictionary"""
        return {"id": self.id, "name": self.name}

    def deserialize(self, data):
        """
        Deserializes a YourResourceModel from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.name = data["name"]
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid YourResourceModel: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid YourResourceModel: body of request contained bad or no data "
                + str(error)
            ) from error
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def all(cls):
        """Returns all of the YourResourceModels in the database"""
        logger.info("Processing all YourResourceModels")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a YourResourceModel by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.session.get(cls, by_id)

    @classmethod
    def find_by_name(cls, name):
        """Returns all YourResourceModels with the given name

        Args:
            name (string): the name of the YourResourceModels you want to match
        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)
