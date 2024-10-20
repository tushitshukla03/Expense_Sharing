# Expense Sharing Application

A Django REST API for managing shared expenses between users. This application helps track expenses, split bills, and manage balances between users with different splitting methods.

## Features

- User Management
- Expense Creation and Tracking
- Multiple Expense Splitting Methods
  - Equal Split
  - Exact Amount Split
  - Percentage Split
- Balance Tracking
- Expense Reports
- Balance Sheet Export

## API Endpoints

### User Endpoints

- `POST /users/create/` - Create a new user
- `GET /users/<id>/` - Get user details
- `GET /users/<id>/expenses/` - Get user's expenses summary

### Expense Endpoints

- `POST /expenses/create/` - Create a new expense
- `GET /expenses/` - List all expenses
- `GET /expenses/split/<expense_id>/` - Get expense split details
- `GET /expenses/overall/` - Get overall expense statistics

### Balance Endpoints

- `GET /balances/<user_id>/` - Get user's balance details
- `GET /balances/download/` - Download balance sheet as CSV

## Models

### User
```python
fields = {
    'name': CharField,
    'email': EmailField(unique),
    'mobile': CharField(unique)
}
```

### Expense
```python
fields = {
    'payer': ForeignKey(User),
    'participants': ManyToManyField(User),
    'amount': FloatField,
    'split_method': CharField(choices=['equal', 'exact', 'percentage']),
    'exact_splits': JSONField,
    'percentage_splits': JSONField,
    'created_at': DateTimeField
}
```

### Balance
```python
fields = {
    'from_user': ForeignKey(User),
    'to_user': ForeignKey(User),
    'amount': FloatField
}
```

## Setup

1. Clone the repository
```bash
git clone https://github.com/tushitshukla03/Expense_Sharing
```

2. running script 
```bash
./run.sh
```



## API Usage Examples

### Creating a User
```bash
curl -X POST http://localhost:8000/users/create/ \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com", "mobile": "1234567890"}'
```

### Creating an Expense (Equal Split)
```bash
curl -X POST http://localhost:8000/expenses/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "payer": 1,
    "participants": [1, 2, 3],
    "amount": 300.00,
    "split_method": "equal"
  }'
```

### Creating an Expense (Exact Split)
```bash
curl -X POST http://localhost:8000/expenses/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "payer": 1,
    "participants": [1, 2, 3],
    "amount": 300.00,
    "split_method": "exact",
    "exact_splits": {
      "1": 100.00,
      "2": 150.00,
      "3": 50.00
    }
  }'
```

## Error Handling

The API uses standard HTTP response codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error

## Logging

The application includes comprehensive logging for:
- Expense creation and splitting
- Balance updates
- Error tracking

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

