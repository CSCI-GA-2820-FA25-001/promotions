"""
Models for YourResourceModel

All of the models are stored in this module
"""

import logging
from datetime import datetime
from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Index, Enum as SQLEnum, func
from decimal import Decimal
logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""
    def __init__(self, message):
        """Create an instance with a meaningful error message"""
        super().__init__(message)

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

    @property
    def discounted_price(self):
        if self.promotion_type != PromotionTypeEnum.discount or not self.discount_value:
            return self.original_price
        if self.discount_type == DiscountTypeEnum.amount:
            return max(self.original_price - self.discount_value, 0)
        elif self.discount_type == DiscountTypeEnum.percent:
            return max(Decimal(self.original_price) * Decimal(1 - self.discount_value / 100), 0)
        return self.original_price

    def create(self):
        logger.info("Creating %s", self.product_name)
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self)
            raise DataValidationError(e) from e

    def update(self):
        logger.info("update %s", self.product_name)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self)
            raise DataValidationError(e) from e

    def delete(self):
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
    def deserialize(self, data):
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
            # -------- 数据类型验证 --------
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
        Index("ix_promotions_status", "status"), #加速基于 status 列的查询（例如 WHERE status = 'active'）
        Index("ix_promotions_expiration_date", "expiration_date"), #加速基于 expiration_date 列的查询
        Index("ix_promotions_name", "product_name"), #加速基于product_name列的查询
        Index("ix_promotions_type", "promotion_type"), #加速基于promotion_type列的查询
        Index("ix_promotions_discount_type", "discount_type"), #加速基于discount_type列的查询
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
        """返回数据库中所有 Promotion 对象"""
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

