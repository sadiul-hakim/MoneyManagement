from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Wallet, Transfer, IncomeSource, ExpenseCategory, Income, Expense
from .forms import TransferForm, IncomeForm, ExpenseForm


class TransferTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.wallet_bank = Wallet.objects.create(
            user=self.user, name='Bank', balance=Decimal('1000.00'), icon='🏦'
        )
        self.wallet_bkash = Wallet.objects.create(
            user=self.user, name='bKash', balance=Decimal('200.00'), icon='📱'
        )
        self.source = IncomeSource.objects.create(name='Salary', icon='💼')
        self.category = ExpenseCategory.objects.create(name='Food & Groceries', icon='🍔')
        self.client = Client()
        self.client.login(username='testuser', password='password123')

    def test_transfer_form_validation(self):
        # Same wallet validation
        form = TransferForm(data={
            'from_wallet': self.wallet_bank.pk,
            'to_wallet': self.wallet_bank.pk,
            'amount': '100.00',
            'date': '2026-09-20',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('to_wallet', form.errors)

        # Insufficient balance validation
        form2 = TransferForm(data={
            'from_wallet': self.wallet_bkash.pk,
            'to_wallet': self.wallet_bank.pk,
            'amount': '500.00',
            'date': '2026-09-20',
        })
        self.assertFalse(form2.is_valid())
        self.assertIn('amount', form2.errors)

    def test_transfer_create_view(self):
        response = self.client.post(reverse('transfer_create'), {
            'from_wallet': self.wallet_bank.pk,
            'to_wallet': self.wallet_bkash.pk,
            'amount': '300.00',
            'date': '2026-09-20',
            'description': 'Add funds to bKash',
        })
        self.assertRedirects(response, reverse('transfer_list'))

        self.wallet_bank.refresh_from_db()
        self.wallet_bkash.refresh_from_db()

        self.assertEqual(self.wallet_bank.balance, Decimal('700.00'))
        self.assertEqual(self.wallet_bkash.balance, Decimal('500.00'))
        self.assertEqual(Transfer.objects.count(), 1)

    def test_transfer_delete_reverts_balances(self):
        # Create transfer
        self.client.post(reverse('transfer_create'), {
            'from_wallet': self.wallet_bank.pk,
            'to_wallet': self.wallet_bkash.pk,
            'amount': '400.00',
            'date': '2026-09-20',
        })
        transfer = Transfer.objects.first()

        # Delete transfer
        response = self.client.post(reverse('transfer_delete', kwargs={'pk': transfer.pk}))
        self.assertRedirects(response, reverse('transfer_list'))

        self.wallet_bank.refresh_from_db()
        self.wallet_bkash.refresh_from_db()

        self.assertEqual(self.wallet_bank.balance, Decimal('1000.00'))
        self.assertEqual(self.wallet_bkash.balance, Decimal('200.00'))
        self.assertEqual(Transfer.objects.count(), 0)

    def test_income_create_with_dynamic_source(self):
        response = self.client.post(reverse('income_create'), {
            'amount': '500.00',
            'source': self.source.pk,
            'wallet': self.wallet_bank.pk,
            'date': '2026-09-20',
        })
        self.assertRedirects(response, reverse('income_list'))
        self.wallet_bank.refresh_from_db()
        self.assertEqual(self.wallet_bank.balance, Decimal('1500.00'))
        self.assertEqual(Income.objects.first().source, self.source)

    def test_expense_create_with_dynamic_category(self):
        response = self.client.post(reverse('expense_create'), {
            'amount': '250.00',
            'category': self.category.pk,
            'wallet': self.wallet_bank.pk,
            'date': '2026-09-20',
        })
        self.assertRedirects(response, reverse('expense_list'))
        self.wallet_bank.refresh_from_db()
        self.assertEqual(self.wallet_bank.balance, Decimal('750.00'))
        self.assertEqual(Expense.objects.first().category, self.category)

