from django import forms
from .models import (
    Wallet,
    IncomeSource,
    ExpenseCategory,
    Income,
    Expense,
    Lending,
    Borrowing,
    Transfer,
)


class WalletForm(forms.ModelForm):
    class Meta:
        model = Wallet
        fields = ['name', 'balance', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g. Cash in Hand, Bank, bKash',
                'class': 'form-input',
            }),
            'balance': forms.NumberInput(attrs={
                'placeholder': '0.00',
                'class': 'form-input',
                'step': '0.01',
            }),
            'icon': forms.TextInput(attrs={
                'placeholder': '💰',
                'class': 'form-input',
                'maxlength': '10',
            }),
        }


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['amount', 'source', 'wallet', 'date', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'placeholder': 'Amount',
                'class': 'form-input',
                'step': '0.01',
                'inputmode': 'decimal',
            }),
            'source': forms.Select(attrs={
                'class': 'form-input',
            }),
            'wallet': forms.Select(attrs={
                'class': 'form-input',
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
            }),
            'description': forms.TextInput(attrs={
                'placeholder': 'Short note (optional)',
                'class': 'form-input',
            }),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['amount', 'category', 'wallet', 'date', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'placeholder': 'Amount',
                'class': 'form-input',
                'step': '0.01',
                'inputmode': 'decimal',
            }),
            'category': forms.Select(attrs={
                'class': 'form-input',
            }),
            'wallet': forms.Select(attrs={
                'class': 'form-input',
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
            }),
            'description': forms.TextInput(attrs={
                'placeholder': 'Short note (optional)',
                'class': 'form-input',
            }),
        }


class LendingForm(forms.ModelForm):
    class Meta:
        model = Lending
        fields = ['person_name', 'amount', 'wallet', 'date_lent', 'return_date', 'notes']
        widgets = {
            'person_name': forms.TextInput(attrs={
                'placeholder': 'Who did you lend to?',
                'class': 'form-input',
            }),
            'amount': forms.NumberInput(attrs={
                'placeholder': 'Amount',
                'class': 'form-input',
                'step': '0.01',
                'inputmode': 'decimal',
            }),
            'wallet': forms.Select(attrs={
                'class': 'form-input',
            }),
            'date_lent': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
            }),
            'return_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
            }),
            'notes': forms.TextInput(attrs={
                'placeholder': 'Notes (optional)',
                'class': 'form-input',
            }),
        }


class BorrowingForm(forms.ModelForm):
    class Meta:
        model = Borrowing
        fields = ['person_name', 'amount', 'wallet', 'date_borrowed', 'return_date', 'notes']
        widgets = {
            'person_name': forms.TextInput(attrs={
                'placeholder': 'Who did you borrow from?',
                'class': 'form-input',
            }),
            'amount': forms.NumberInput(attrs={
                'placeholder': 'Amount',
                'class': 'form-input',
                'step': '0.01',
                'inputmode': 'decimal',
            }),
            'wallet': forms.Select(attrs={
                'class': 'form-input',
            }),
            'date_borrowed': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
            }),
            'return_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
            }),
            'notes': forms.TextInput(attrs={
                'placeholder': 'Notes (optional)',
                'class': 'form-input',
            }),
        }


class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        fields = ['from_wallet', 'to_wallet', 'amount', 'date', 'description']
        widgets = {
            'from_wallet': forms.Select(attrs={
                'class': 'form-input',
            }),
            'to_wallet': forms.Select(attrs={
                'class': 'form-input',
            }),
            'amount': forms.NumberInput(attrs={
                'placeholder': 'Amount to transfer',
                'class': 'form-input',
                'step': '0.01',
                'inputmode': 'decimal',
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
            }),
            'description': forms.TextInput(attrs={
                'placeholder': 'Note (optional)',
                'class': 'form-input',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        from_wallet = cleaned_data.get('from_wallet')
        to_wallet = cleaned_data.get('to_wallet')
        amount = cleaned_data.get('amount')

        if from_wallet and to_wallet and from_wallet == to_wallet:
            self.add_error('to_wallet', 'Destination wallet cannot be the same as source wallet.')

        if amount is not None and amount <= 0:
            self.add_error('amount', 'Transfer amount must be greater than 0.')

        if from_wallet and amount and from_wallet.balance < amount:
            self.add_error('amount', f'Insufficient balance in {from_wallet.name} (Available: ৳{from_wallet.balance}).')

        return cleaned_data

