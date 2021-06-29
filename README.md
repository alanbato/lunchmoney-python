# lunchmoney

This library is a Python client for the [Lunch Money](https://lunchmoney.app) API.

This software is considered to be in Alpha state, as all endpoints of the API have not yet been implemented.

# Installation

You can install this library by running

`$ pip install lunchmoney`

# Usage

In order to use the client, you need to set the `LUNCHMONEY_API_KEY` enviroment variable with your API Token, which you can get by going to `Settings > Developers > Request new Access Token`.

# Examples

## Create a client

```python
from lunchmoney import LunchMoneyClient

client = LunchMoneyClient()
```

## Get the list of categories

```python
categories = client.categories()
print(categories)
# [Category(id=214038, name='Alcohol, Bars', description=None, is_income=False, exclude_from_budget=False, exclude_from_totals=False, updated_at=datetime.datetime(2021, 6, 7, 22, 14, 6, 379000, tzinfo=datetime.timezone.utc), created_at=datetime.datetime(2021, 6, 7, 22, 14, 6, 379000, tzinfo=datetime.timezone.utc), is_group=False, group_id=None), Category(...), ...]
```

## Insert a Transaction

```python
trx_data = {
  "date": "2021-06-06",
  "payee": "Sushi House",
  "amount": 50.99,
  "currency": "usd",
}
trx_ids = client.insert_transaction(trx_data)
print(trx_ids)
# [3322341]
```

You can also instert multiple transactions by passing a list of transactions to `client.insert_transactions()`

## Query Transactions

```python
trxs = client.transactions(category_id=323401)
print(trxs)
# [Transaction(id=41078765, date='2021-06-06', amount=70.0, payee='Sushi House', currency='usd', status=<TransactionStatus.uncleared: 'uncleared'>, category_id=214038, asset_id=None, parent_id=None, plaid_account_id=None, is_group=False, group_id=None, external_id=None, tags=None, notes=None), ...]
```

# Contributing

This library is still in development, and pull requests are welcome.
For ideas on what to contribute, take a look at Lunch Money's [API Reference](https://lunchmoney.dev/), and try to implement a missing endpoint or parameter.

# Developing

1. Fork this repository, clone your fork, and add this repository remote as upstream.
2. Run `make setup` in the project directory.
3. Make your changes, write your tests.
4. Try out your changes in the repl with `make repl`.
5. Run `make test` for tests, and `make lint` for linting.
6. Once you're happy with your changes, submit a PR!
