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

    def test_income_edit_same_and_different_wallet(self):
        # Create initial income
        income = Income.objects.create(
            amount=Decimal('500.00'), source=self.source, wallet=self.wallet_bank, date='2026-09-20'
        )
        self.wallet_bank.balance += Decimal('500.00')
        self.wallet_bank.save()

        # Edit amount on same wallet: 500 -> 700 (net +200)
        response = self.client.post(reverse('income_edit', kwargs={'pk': income.pk}), {
            'amount': '700.00',
            'source': self.source.pk,
            'wallet': self.wallet_bank.pk,
            'date': '2026-09-20',
        })
        self.assertRedirects(response, reverse('income_list'))
        self.wallet_bank.refresh_from_db()
        self.assertEqual(self.wallet_bank.balance, Decimal('1700.00'))

        # Switch to bkash wallet: bank should revert by -700 (back to 1000), bkash should get +700 (200 -> 900)
        response = self.client.post(reverse('income_edit', kwargs={'pk': income.pk}), {
            'amount': '700.00',
            'source': self.source.pk,
            'wallet': self.wallet_bkash.pk,
            'date': '2026-09-20',
        })
        self.assertRedirects(response, reverse('income_list'))
        self.wallet_bank.refresh_from_db()
        self.wallet_bkash.refresh_from_db()
        self.assertEqual(self.wallet_bank.balance, Decimal('1000.00'))
        self.assertEqual(self.wallet_bkash.balance, Decimal('900.00'))

    def test_expense_edit_same_and_different_wallet(self):
        # Create initial expense
        expense = Expense.objects.create(
            amount=Decimal('300.00'), category=self.category, wallet=self.wallet_bank, date='2026-09-20'
        )
        self.wallet_bank.balance -= Decimal('300.00')
        self.wallet_bank.save()
        self.assertEqual(self.wallet_bank.balance, Decimal('700.00'))

        # Edit amount on same wallet: 300 -> 400 (extra 100 spent, bank should become 600)
        response = self.client.post(reverse('expense_edit', kwargs={'pk': expense.pk}), {
            'amount': '400.00',
            'category': self.category.pk,
            'wallet': self.wallet_bank.pk,
            'date': '2026-09-20',
        })
        self.assertRedirects(response, reverse('expense_list'))
        self.wallet_bank.refresh_from_db()
        self.assertEqual(self.wallet_bank.balance, Decimal('600.00'))

        # Switch to bkash wallet: bank reverts (+400 -> 1000), bkash is deducted (-400 -> 200 - 400 = -200)
        response = self.client.post(reverse('expense_edit', kwargs={'pk': expense.pk}), {
            'amount': '400.00',
            'category': self.category.pk,
            'wallet': self.wallet_bkash.pk,
            'date': '2026-09-20',
        })
        self.assertRedirects(response, reverse('expense_list'))
        self.wallet_bank.refresh_from_db()
        self.wallet_bkash.refresh_from_db()
        self.assertEqual(self.wallet_bank.balance, Decimal('1000.00'))
        self.assertEqual(self.wallet_bkash.balance, Decimal('-200.00'))


class ReportTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reportuser', password='password123')
        self.other_user = User.objects.create_user(username='otheruser', password='password123')

        self.wallet = Wallet.objects.create(
            user=self.user, name='Main Wallet', balance=Decimal('5000.00'), icon='💰'
        )
        self.other_wallet = Wallet.objects.create(
            user=self.other_user, name='Other Wallet', balance=Decimal('1000.00'), icon='🏦'
        )

        self.source_salary = IncomeSource.objects.create(name='Salary', icon='💼')
        self.source_freelance = IncomeSource.objects.create(name='Freelance', icon='💻')
        self.cat_food = ExpenseCategory.objects.create(name='Food & Groceries', icon='🍔')
        self.cat_bills = ExpenseCategory.objects.create(name='Bills & Utilities', icon='⚡')

        # Incomes in 2026-09 and 2026-08
        Income.objects.create(
            wallet=self.wallet, source=self.source_salary, amount=Decimal('3000.00'), date='2026-09-01'
        )
        Income.objects.create(
            wallet=self.wallet, source=self.source_freelance, amount=Decimal('1000.00'), date='2026-09-15'
        )
        Income.objects.create(
            wallet=self.wallet, source=self.source_salary, amount=Decimal('3000.00'), date='2026-08-01'
        )

        # Incomes in 2025
        Income.objects.create(
            wallet=self.wallet, source=self.source_salary, amount=Decimal('2000.00'), date='2025-12-01'
        )

        # Other user's income (should not leak)
        Income.objects.create(
            wallet=self.other_wallet, source=self.source_salary, amount=Decimal('9999.00'), date='2026-09-01'
        )

        # Expenses in 2026-09 and 2026-08
        Expense.objects.create(
            wallet=self.wallet, category=self.cat_food, amount=Decimal('1200.00'), date='2026-09-05'
        )
        Expense.objects.create(
            wallet=self.wallet, category=self.cat_bills, amount=Decimal('800.00'), date='2026-09-10'
        )
        Expense.objects.create(
            wallet=self.wallet, category=self.cat_food, amount=Decimal('1500.00'), date='2026-08-05'
        )

        self.client = Client()

    def test_reports_unauthenticated_redirect(self):
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 302)

    def test_reports_page_all_time(self):
        self.client.login(username='reportuser', password='password123')
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)

        # Overall sums
        # Total Income = 3000 + 1000 + 3000 + 2000 = 9000
        self.assertEqual(response.context['total_income'], Decimal('9000.00'))
        # Total Expense = 1200 + 800 + 1500 = 3500
        self.assertEqual(response.context['total_expense'], Decimal('3500.00'))
        # Net savings = 9000 - 3500 = 5500
        self.assertEqual(response.context['net_savings'], Decimal('5500.00'))

        # Monthly aggregation should have 3 distinct months (2026-09, 2026-08, 2025-12)
        monthly_list = response.context['monthly_list']
        self.assertEqual(len(monthly_list), 3)
        self.assertEqual(monthly_list[0]['key'], '2026-09')
        self.assertEqual(monthly_list[0]['income'], Decimal('4000.00'))
        self.assertEqual(monthly_list[0]['expense'], Decimal('2000.00'))
        self.assertEqual(monthly_list[0]['net'], Decimal('2000.00'))

        # Source breakdown
        sources = response.context['source_breakdown']
        self.assertEqual(len(sources), 2)
        # Salary is 3000 + 3000 + 2000 = 8000 (88.9%)
        self.assertEqual(sources[0]['name'], 'Salary')
        self.assertEqual(sources[0]['total'], Decimal('8000.00'))

        # Category breakdown
        categories = response.context['category_breakdown']
        self.assertEqual(len(categories), 2)
        # Food is 1200 + 1500 = 2700
        self.assertEqual(categories[0]['name'], 'Food & Groceries')
        self.assertEqual(categories[0]['total'], Decimal('2700.00'))

    def test_reports_year_filter(self):
        self.client.login(username='reportuser', password='password123')
        response = self.client.get(reverse('reports') + '?year=2026')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_year'], 2026)

        # 2026 Income: 3000 + 1000 + 3000 = 7000
        self.assertEqual(response.context['total_income'], Decimal('7000.00'))
        # 2026 Expense: 1200 + 800 + 1500 = 3500
        self.assertEqual(response.context['total_expense'], Decimal('3500.00'))
        # Monthly list only has 2 months in 2026
        self.assertEqual(len(response.context['monthly_list']), 2)


