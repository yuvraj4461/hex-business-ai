from app.ingestion.normalizers.base import (
    Normalizer,
    to_date,
    to_float,
    to_str,
)
from app.models.expense import Expense
from app.models.transaction import Transaction
from app.sources.base import EntityType, RawRecord


class TransactionNormalizer(Normalizer):
    entity_type = EntityType.TRANSACTION
    model = Transaction

    def map(self, db, raw: RawRecord, organization_id: int, connection_id: int):
        p = raw.payload
        amount = to_float(self.source_field(p, "amount"))
        if amount is None:
            return None

        ttype = (
            to_str(self.source_field(p, "transaction_type"))
            or ("REVENUE" if amount >= 0 else "EXPENSE")
        ).upper()

        return {
            "transaction_type": ttype,
            "amount": abs(amount),
            "description": to_str(self.source_field(p, "description")),
            "transaction_date": to_date(
                self.source_field(p, "transaction_date")
            )
            or to_date(self.source_field(p, "date")),
        }


class ExpenseNormalizer(Normalizer):
    entity_type = EntityType.EXPENSE
    model = Expense

    def map(self, db, raw: RawRecord, organization_id: int, connection_id: int):
        p = raw.payload
        amount = to_float(self.source_field(p, "amount"))
        if amount is None:
            return None

        return {
            "category": to_str(self.source_field(p, "category")) or "General",
            "amount": abs(amount),
            "description": to_str(self.source_field(p, "description")),
            "expense_date": to_date(self.source_field(p, "expense_date"))
            or to_date(self.source_field(p, "date")),
        }
