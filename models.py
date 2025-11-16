from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, Literal


class POSLine(BaseModel):
    timestamp: datetime
    item_type: Literal["FOOD", "BEV", "OTHER"]
    item_name: str
    quantity: int = Field(ge=1)
    price_per_item: float = Field(ge=0)
    total_price: float = Field(ge=0)
    payment_method: Literal["CARD", "CASH"]
    area: Literal["Restaurant", "Bar", "Events", "Catering", "Other"]
    receipt_id: str


class SalesInvoice(BaseModel):
    date: date
    amount: float = Field(ge=0)
    area: Literal["Restaurant", "Bar", "Events", "Catering", "Other"]


class PurchaseInvoice(BaseModel):
    date: date
    amount: float = Field(ge=0)
    category: Literal["FOOD", "BEV", "OTHER"]
    area: Optional[Literal["Restaurant", "Bar", "Events", "Catering", "Other"]] = None


class LaborCost(BaseModel):
    date: date
    amount: float = Field(ge=0)
    area: Optional[Literal["Restaurant", "Bar", "Events", "Catering", "Other"]] = None


class FixedCost(BaseModel):
    date: date
    amount: float = Field(ge=0)
    cost_type: Literal["rent", "leasing", "utilities", "other"]


class InventorySnapshot(BaseModel):
    date: date
    stock_value: float = Field(ge=0)


class CapitalSnapshot(BaseModel):
    date: date
    capital_value: float = Field(ge=0)


class PriceListItem(BaseModel):
    item_name: str
    theoretical_price: float = Field(ge=0)


class ReorderLevel(BaseModel):
    item_name: str
    reorder_level: int = Field(ge=0)
