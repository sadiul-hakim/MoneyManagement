from django.contrib import admin
from .models import Wallet, Income, Expense, Lending, Borrowing


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['name', 'balance', 'icon', 'created_at']


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['amount', 'source', 'wallet', 'date', 'description']
    list_filter = ['source', 'date']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['amount', 'category', 'wallet', 'date', 'description']
    list_filter = ['category', 'date']


@admin.register(Lending)
class LendingAdmin(admin.ModelAdmin):
    list_display = ['person_name', 'amount', 'date_lent', 'return_date', 'is_returned']
    list_filter = ['is_returned']


@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ['person_name', 'amount', 'date_borrowed', 'return_date', 'is_returned']
    list_filter = ['is_returned']
