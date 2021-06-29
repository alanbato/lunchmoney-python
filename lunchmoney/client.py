import os
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union, cast

from httpx import Client, Response
from pydantic import parse_obj_as

from lunchmoney.transactions import SplitData

from . import Category, Tag, Transaction, TransactionData

LUNCHMONEY_API_URL = "https://dev.lunchmoney.app/v1/"


class LunchMoneyError(Exception):
    def __init__(self, message: Union[str, List[str]] = None):
        if isinstance(message, str):
            self.message = message
        if isinstance(message, list):
            self.message = "\n".join(message)

    def __str__(self) -> str:  # pragma: no cover
        return self.message


def single_to_list_decorator(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def wrapper(
        self: Any, element: Any, *args: List[Any], **kwargs: Dict[str, Any]
    ) -> Any:
        return f(self, [element], *args, **kwargs)

    return wrapper


class LunchMoneyClient(Client):
    def __init__(self, api_key: str = None) -> None:
        api_key = api_key or os.environ.get("LUNCHMONEY_API_KEY", None)
        if not api_key:
            raise LunchMoneyError(
                "The environment variable LUNCHMONEY_API_KEY must be provided."
            )
        super().__init__(
            base_url=LUNCHMONEY_API_URL, headers={"Authorization": f"Bearer {api_key}"}
        )

    def _get_data_or_raise(self, response: Response, key: str = None) -> Any:
        data = response.json()
        if "error" in data:
            raise LunchMoneyError(data["error"])
        elif key is not None:
            return data[key]
        else:
            return data

    # Category Endpoints
    def categories(self) -> List[Category]:
        r = self.get("categories")
        r.raise_for_status()
        categories_data = self._get_data_or_raise(r, "categories")
        categories = parse_obj_as(List[Category], categories_data)
        return categories

    def create_category(
        self,
        name: str,
        description: str = None,
        is_income: bool = False,
        exclude_from_budget: bool = False,
        exclude_from_totals: bool = False,
    ) -> int:
        category_data = {
            "name": name,
            "description": description,
            "is_income": is_income,
            "exclude_from_budget": exclude_from_budget,
            "exclude_from_totals": exclude_from_totals,
        }
        r = self.post("categories", json=category_data)
        r.raise_for_status()
        return self._get_data_or_raise(r, "category_id")

    # Tag Endpoints
    def tags(self) -> List[Tag]:
        r = self.get("tags")
        r.raise_for_status()
        tags_data = self._get_data_or_raise(r)
        tags = parse_obj_as(List[Tag], tags_data)
        return tags

    # Transaction Endpoints
    def transactions(
        self,
        tag_id: int = None,
        recurring_id: int = None,
        plaid_account_id: int = None,
        category_id: int = None,
        asset_id: int = None,
        start_date: str = None,
        end_date: str = None,
        debit_as_negative: bool = False,
        offset: int = None,
        limit: int = None,
    ) -> List[Transaction]:
        """Gets the list of transactions that match the query"""
        params = {
            "tag_id": tag_id,
            "recurring_id": recurring_id,
            "plaid_account_id": plaid_account_id,
            "category_id": category_id,
            "asset_id": asset_id,
            "start_date": start_date,
            "end_date": end_date,
            "debit_as_negative": debit_as_negative,
            "offset": offset,
            "limit": limit,
        }
        # Remove unused params
        query_params: Dict[str, Any] = {
            k: v for k, v in params.items() if v is not None
        }
        r = self.get("transactions", params=query_params)
        r.raise_for_status()
        transactions_data = self._get_data_or_raise(r, "transactions")
        transactions = parse_obj_as(List[Transaction], transactions_data)
        return transactions

    def transaction(
        self, transaction_id: int, debit_as_negative: bool = False
    ) -> Transaction:
        """Get a transaction by its ID"""
        params = {
            "debit_as_negative": debit_as_negative,
        }
        r = self.get(f"transactions/{transaction_id}", params=params)
        r.raise_for_status()
        transaction_data = self._get_data_or_raise(r)
        transaction = Transaction.parse_obj(transaction_data)
        return transaction

    def insert_transactions(
        self,
        transactions: List[Union[Transaction, TransactionData]],
        apply_rules: bool = False,
        skip_duplicates: bool = False,
        check_for_recurring: bool = False,
        debit_as_negative: bool = False,
    ) -> List[int]:
        transactions_data = [
            t.dict(
                exclude={
                    "id",
                    "plaid_account_id",
                    "parent_id",
                    "group_id",
                    "is_group",
                }
            )
            if isinstance(t, Transaction)
            else t
            for t in transactions
        ]
        payload = {
            "transactions": transactions_data,
            "apply_rules": apply_rules,
            "skip_duplicates": skip_duplicates,
            "check_for_recurring": check_for_recurring,
            "debit_as_negative": debit_as_negative,
        }
        r = self.post("transactions", json=payload)
        r.raise_for_status()
        return self._get_data_or_raise(r, "ids")

    insert_transaction = single_to_list_decorator(insert_transactions)

    def update_transaction(
        self,
        transaction_id: int,
        transaction: Union[Transaction, TransactionData],
        split: Optional[SplitData] = None,
        debit_as_negative: bool = False,
    ) -> Dict[str, Any]:
        transaction_data: TransactionData
        if isinstance(transaction, Transaction):
            transaction_dict = transaction.dict(
                exclude={
                    "id",
                    "plaid_account_id",
                    "parent_id",
                    "group_id",
                    "is_group",
                },
                exclude_none=True,
            )
            transaction_data = cast(TransactionData, transaction_dict)
        else:
            transaction_data = transaction
        payload = {
            "transaction": transaction_data,
            "debit_as_negative": debit_as_negative,
        }
        if split is not None:
            payload["split"] = split
        r = self.put(f"transactions/{transaction_id}", json=payload)
        r.raise_for_status()
        return self._get_data_or_raise(r)
