from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import User, Expense, Balance


class UserExpenseAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Create users
        self.user1 = User.objects.create(name="Alice", email="alice@example.com", mobile="1234567890")
        self.user2 = User.objects.create(name="Bob", email="bob@example.com", mobile="0987654321")
        self.user3 = User.objects.create(name="Charlie", email="charlie@example.com", mobile="1122334455")

        # Create expenses
        self.expense1 = Expense.objects.create(
            payer=self.user1,
            amount=100,
            split_method='equal'
        )
        self.expense1.participants.add(self.user2, self.user3)

        self.expense2 = Expense.objects.create(
            payer=self.user2,
            amount=200,
            split_method='exact',
            exact_splits={"1": 50, "3": 150}
        )
        self.expense2.participants.add(self.user1, self.user3)

    # Test user creation
    def test_user_create(self):
        data = {
            "name": "Dave",
            "email": "dave@example.com",
            "mobile": "9988776655"
        }
        response = self.client.post(reverse('user-create'), data, format='json')
        print(response)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 4)  # 3 users from setUp + 1 new user
        self.assertEqual(User.objects.get(email="dave@example.com").name, "Dave")

    def test_user_detail(self):
        response = self.client.get(reverse('user-detail', kwargs={'pk': self.user1.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.user1.name)

    # Test expense creation
    def test_expense_create(self):
        data = {
            "payer": self.user1.id,
            "participants": [self.user2.id, self.user3.id],
            "amount": 150,
            "split_method": "equal"
        }
        response = self.client.post(reverse('expense-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 3) 

    # Test fetching an expense's details
    def test_expense_detail(self):
        response = self.client.get(reverse('expense-detail'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  

    def test_get_balance(self):
        self.expense1.split_expense()
        response = self.client.get(reverse('get-balance', kwargs={'user_id': self.user2.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['amount'], 50.0)  
    def test_overall_expenses(self):
        response = self.client.get(reverse('overall-expenses'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['expense_count'], 2)

    def test_download_balance_sheet(self):
        response = self.client.get(reverse('download-balance-sheet'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response['Content-Disposition'].startswith('attachment;'))

    def test_expense_split_exact(self):
        response = self.client.get(reverse('expense-split', kwargs={'expense_id': self.expense2.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.expense2.split_expense()  
        balance = Balance.objects.get(from_user=self.user1, to_user=self.user2)
        print(balance)
        self.assertEqual(balance.amount, 100.0) 


if __name__ == '__main__':
    import unittest
    unittest.main()
