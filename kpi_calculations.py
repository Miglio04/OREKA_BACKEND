from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict
try:
    from .models import POSLine, SalesInvoice, PurchaseInvoice
except ImportError:
    # Fallback for direct execution
    from models import POSLine, SalesInvoice, PurchaseInvoice

Q2 = Decimal("0.01")
Q4 = Decimal("0.0001")


def _q2(x: Decimal) -> Decimal:
    return x.quantize(Q2, rounding=ROUND_HALF_UP)


def _q4(x: Decimal) -> Decimal:
    return x.quantize(Q4, rounding=ROUND_HALF_UP)


def kpi_pos_only(
    pos: list[POSLine], price_list: Optional[Dict[str, Decimal]] = None
) -> Dict[str, object]:
    rev_total = Decimal("0")
    by_area: Dict[str, Decimal] = defaultdict(Decimal)
    by_payment: Dict[str, Decimal] = defaultdict(Decimal)
    receipts: set[str] = set()
    discount_numer = Decimal("0")
    discount_denom = Decimal("0")

    has_prices = bool(price_list)

    for l in pos:
        tp: Decimal = Decimal(str(l.total_price))
        rev_total += tp
        by_area[l.area] += tp
        by_payment[l.payment_method] += tp
        receipts.add(l.receipt_id)

        if has_prices:
            theo = price_list.get(l.item_name)  # Decimal or None
            if theo is not None:
                actual = tp / Decimal(l.quantity)  # quantity >= 1
                if theo > actual:
                    discount_numer += (theo - actual) * Decimal(l.quantity)
                discount_denom += theo * Decimal(l.quantity)

    avg_receipt = rev_total / Decimal(max(len(receipts), 1))
    discount_rate = discount_numer / discount_denom if discount_denom > 0 else None

    return {
        "revenue_total": _q2(rev_total),
        "revenue_by_area": {k: _q2(v) for k, v in by_area.items()},
        "revenue_by_payment": {k: _q2(v) for k, v in by_payment.items()},
        "receipt_count": len(receipts),
        "average_receipt": _q2(avg_receipt),
        "discount_rate": _q4(discount_rate) if discount_rate is not None else None,
    }


def add_sales_invoices(
    revenue_by_area: Dict[str, Decimal],
    sales_inv: list[SalesInvoice],
) -> Dict[str, Decimal]:
    out = revenue_by_area.copy()
    for si in sales_inv:
        out[si.area] = out.get(si.area, Decimal("0")) + Decimal(str(si.amount))
    return out


def _normalized_weights(alloc_basis: Dict[str, Decimal]) -> Dict[str, Decimal]:
    # nonnegative finite weights for Decimal
    clean: Dict[str, Decimal] = {
        k: Decimal(v)
        for k, v in alloc_basis.items()
        if v is not None and Decimal(v) > 0
    }
    total = sum(clean.values(), Decimal("0"))
    if total <= 0:
        raise ValueError("alloc_basis must contain at least one positive weight")
    return {k: (w / total) for k, w in clean.items()}


def compute_cogs(
    purch: list[PurchaseInvoice],
    alloc_basis: Optional[Dict[str, Decimal]] = None,
) -> Dict[str, Decimal]:
    cogs_area: Dict[str, Decimal] = defaultdict(Decimal)
    undirected = Decimal("0")
    for p in purch:
        amount = Decimal(str(p.amount))
        if p.area:
            cogs_area[p.area] += amount
        else:
            undirected += amount

    if undirected > 0 and alloc_basis:
        weights = _normalized_weights(alloc_basis)
        for area, w in weights.items():
            cogs_area[area] += undirected * w

    return dict(cogs_area)


def gross_margin_by_area(
    rev_by_area: Dict[str, Decimal], cogs_by_area: Dict[str, Decimal]
) -> Dict[str, Decimal]:
    areas = set(rev_by_area) | set(cogs_by_area)
    return {
        a: _q2(rev_by_area.get(a, Decimal("0")) - cogs_by_area.get(a, Decimal("0")))
        for a in areas
    }


def operating_margin_total(
    gross_total: Decimal, labor: Decimal, fixed: Decimal, other: Decimal = Decimal("0")
) -> Decimal:
    return _q2(gross_total - labor - fixed - other)


def roi_monthly(operating_profit: Decimal, capital_value: Decimal) -> Optional[Decimal]:
    return _q4(operating_profit / capital_value) if capital_value > 0 else None


def inventory_turnover(cogs_total: Decimal, avg_stock: Decimal) -> Optional[Decimal]:
    return _q4(cogs_total / avg_stock) if avg_stock > 0 else None


def inventory_coverage_days(
    stock_value: Decimal, avg_daily_consumption: Decimal
) -> Optional[Decimal]:
    return (
        (stock_value / avg_daily_consumption).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
        if avg_daily_consumption > 0
        else None
    )
