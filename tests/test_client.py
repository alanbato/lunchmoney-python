import os
from typing import List

from vcr import VCR
from ward import Scope, each, fixture, raises, test, xfail

from lunchmoney import Category, LunchMoneyClient, LunchMoneyError, Tag
from lunchmoney.transactions import Transaction, TransactionStatus

my_vcr = VCR(
    serializer="json",
    path_transformer=VCR.ensure_suffix(".json"),
    cassette_library_dir="tests/cassettes",
    record_mode="once",
    match_on=["uri", "method", "query"],
    filter_headers=[("authorization", "XXXXXXX")],
)


@fixture(scope=Scope.Global)
def client() -> LunchMoneyClient:
    client = LunchMoneyClient()
    yield client
    client.close()


@fixture()
def disable_api_key() -> None:
    prev = os.environ.get("LUNCHMONEY_API_KEY", "")
    os.environ["LUNCHMONEY_API_KEY"] = ""
    yield
    os.environ["LUNCHMONEY_API_KEY"] = prev


@test("Test that we can create a client", tags=["client"])
def _(client: LunchMoneyClient = client):
    assert isinstance(client, LunchMoneyClient)


@test("Test that a client with no API Key Fails", tags=["client"])
def _(disable_api_key=disable_api_key):
    with raises(LunchMoneyError) as exc:
        LunchMoneyClient()
    assert (
        str(exc.raised)
        == "The environment variable LUNCHMONEY_API_KEY must be provided."
    )


@test("Test listing of categories", tags=["/categories"])
def _(client: LunchMoneyClient = client):
    with my_vcr.use_cassette("categories_get"):
        categories = client.categories()
    assert len(categories) == 11
    assert isinstance(categories[0], Category)


@test("Test creation of categories", tags=["/categories"])
def _(client: LunchMoneyClient = client):
    with my_vcr.use_cassette("categories_post"):
        category_id = client.create_category(
            name="Junk Food",
        )
    with my_vcr.use_cassette("categories_post_validation"):
        categories: List[Category] = client.categories()
    for category in categories:
        if category.id == category_id:
            break
    else:
        raise
    assert category.name == "Junk Food"
    assert not category.is_income
    assert not category.exclude_from_budget
    assert not category.exclude_from_totals


@test("Test creation of categories with all params", tags=["/categories"])
def _(client: LunchMoneyClient = client):
    with my_vcr.use_cassette("categories_post_full"):
        category_id = client.create_category(
            name="Side Business",
            description="Extra money on the side, shh",
            is_income=True,
            exclude_from_budget=True,
            exclude_from_totals=True,
        )
    with my_vcr.use_cassette("categories_post_full_validation"):
        categories: List[Category] = client.categories()
    for category in categories:
        if category.id == category_id:
            break
    else:
        raise
    assert category.name == "Side Business"
    assert category.is_income
    assert category.exclude_from_budget
    assert category.exclude_from_totals


@test("Test creation of category fails", tags=["/categories"])
def _(client: LunchMoneyClient = client):
    long_name = "Really long name" + "e" * 100
    with my_vcr.use_cassette("categories_post_fails"):
        with raises(LunchMoneyError):
            client.create_category(name=long_name)


@test("Test listing of tags", tags=["/tags"])
def _(client: LunchMoneyClient = client):
    with my_vcr.use_cassette("tags_get"):
        tags = client.tags()
    assert len(tags) == 4
    assert isinstance(tags[0], Tag)


@test("Test listing of transactions", tags=["/transactions"])
def _(client: LunchMoneyClient = client):
    with my_vcr.use_cassette("trx_get"):
        trxs = client.transactions()
    assert len(trxs) == 23
    assert isinstance(trxs[0], Transaction)


@test(
    "Test querying that there are {count} transactions with {param}={value}",
    tags=["/transactions"],
)
def _(
    client: LunchMoneyClient = client,
    param=each("tag_id", "recurring_id", "category_id", "asset_id"),
    value=each(14405, 111413, 214042, 17663),
    count=each(6, 1, 1, 7),
):
    with my_vcr.use_cassette(f"trx_get_param_{param}"):
        trxs = client.transactions(**{param: value})
    assert len(trxs) == count


@test(
    "Test get {count} transactions from {start_date} to {end_date}",
    tags=["/transactions"],
)
def _(
    client: LunchMoneyClient = client,
    start_date=each("2021-05-01", "2021-06-01"),
    end_date=each("2021-05-30", "2021-06-06"),
    count=each(18, 9),
):
    with my_vcr.use_cassette(f"trx_get_from_{start_date}_to_{end_date}"):
        trxs = client.transactions(start_date=start_date, end_date=end_date)
    assert len(trxs) == count


@test(
    "Test get only {limit} transactions",
    tags=["/transactions"],
)
def _(client: LunchMoneyClient = client, limit=each(10, 15, 20)):
    with my_vcr.use_cassette(f"trx_get_limit_{limit}"):
        trxs = client.transactions(limit=limit)
    assert len(trxs) == limit


@test(
    "Test get a specific transaction: {trx_id}",
    tags=["/transactions"],
)
def _(
    client: LunchMoneyClient = client,
    trx_id=each(37555760, 37555796, 37555795),
    amount=each(850.0, 33.31, 18.99),
):
    with my_vcr.use_cassette(f"trx_get_{trx_id}"):
        trx = client.transaction(trx_id)
    assert trx.amount == amount


@test("Test insert transaction", tags=["/transactions"])
def _(client: LunchMoneyClient = client):
    trx_data = {
        "date": "2021-06-06",
        "payee": "Sushi House",
        "amount": 50.99,
        "currency": "usd",
    }
    with my_vcr.use_cassette("trx_post"):
        trx_ids = client.insert_transaction(trx_data)
    trx_id = trx_ids[0]
    with my_vcr.use_cassette("trx_post_lookup"):
        trx = client.transaction(trx_id)
    assert trx_data["payee"] == trx.payee
    assert trx_data["amount"] == trx.amount


@test("Test insert transaction fails", tags=["/transactions"])
def _(client: LunchMoneyClient = client):
    trx_data = {
        "date": "2021-06-06",
        "payee": "Sushi House",
        "amount": 50.99,
        "currency": "megabucks",
    }
    with my_vcr.use_cassette("trx_post_fails"):
        with raises(LunchMoneyError):
            client.insert_transaction(trx_data)


@test("Test insert multiple transactions", tags=["/transactions"])
def _(client: LunchMoneyClient = client):
    trx_data = [
        {
            "date": "2021-06-06",
            "payee": "Family Laundry",
            "amount": 15.10,
            "currency": "usd",
        },
        {
            "date": "2021-06-06",
            "payee": "Cine Theater",
            "amount": 16.50,
            "currency": "usd",
        },
    ]
    with my_vcr.use_cassette("trx_post_multiple"):
        trx_ids = client.insert_transactions(trx_data)
    for idx, trx_id in enumerate(trx_ids):
        with my_vcr.use_cassette(f"trx_post_multiple_lookup_{trx_id}"):
            trx = client.transaction(trx_id)
        assert trx_data[idx]["payee"] == trx.payee
        assert trx_data[idx]["amount"] == trx.amount


@test("Test insert multiple transactions fails", tags=["/transactions"])
def _(client: LunchMoneyClient = client):
    trx_data = [
        {
            "date": "2100-06-06",
            "payee": "Future Shop",
            "amount": 150000,
            "currency": "quarzon",
        },
        {
            "date": "2021-06-06",
            "payee": "Cine Theater",
            "amount": 16.50,
            "currency": "megabucks",
        },
    ]
    with my_vcr.use_cassette("trx_post_multiple_fails"):
        with raises(LunchMoneyError):
            client.insert_transactions(trx_data)


@test("Test update transaction {trx_id}", tags=["/transactions"])
def _(client: LunchMoneyClient = client, trx_id=37555760):
    with my_vcr.use_cassette(f"trx_get_{trx_id}"):
        trx = client.transaction(trx_id)
    trx.payee = "New Payee"
    trx.amount += 1
    trx.status = None
    with my_vcr.use_cassette(f"trx_update_{trx_id}"):
        response = client.update_transaction(trx_id, trx)
    assert response["updated"]


@test("Test update transaction with {trx_id} with dict", tags=["/transactions"])
def _(client: LunchMoneyClient = client, trx_id=37555760):
    with my_vcr.use_cassette(f"trx_get_{trx_id}"):
        trx = client.transaction(trx_id)
    updated_transaction = {
        "payee": "New Payee (New)",
        "amount": trx.amount + 1,
        "status": TransactionStatus.cleared,
    }
    with my_vcr.use_cassette(f"trx_update_{trx_id}_dict"):
        response = client.update_transaction(trx_id, updated_transaction)
    assert response["updated"]


@xfail("API returns 'splits.map is not a function'")
@test("Test split transaction", tags=["/transactions"])
def _(client: LunchMoneyClient = client):
    with my_vcr.use_cassette("categories_get.json"):
        categories = client.categories()
    trx_data = {
        "date": "2021-06-06",
        "payee": "Sushi House",
        "amount": 100,
        "currency": "usd",
        "category_id": categories[0].id,
        "tags": [],
    }
    with my_vcr.use_cassette("trx_post_to_split"):
        trx_ids = client.insert_transaction(trx_data)
    trx_id = trx_ids[0]
    with my_vcr.use_cassette("trx_get_to_split"):
        trx = client.transaction(trx_id)
    trx.amount = 70
    with my_vcr.use_cassette("trx_post_split"):
        data = client.update_transaction(
            transaction_id=trx_id,
            transaction=trx,
            split={
                "date": trx_data["date"],
                "category_id": trx.category_id,
                "amount": 30,
            },
        )
        assert "split" in data
