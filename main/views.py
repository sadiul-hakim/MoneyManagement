from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .models import Wallet, Income, Expense, Lending, Borrowing
from .forms import WalletForm, IncomeForm, ExpenseForm, LendingForm, BorrowingForm


# ── Dashboard ──────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    wallets = Wallet.objects.filter(user=request.user)
    total_balance = wallets.aggregate(total=Sum('balance'))['total'] or Decimal('0')

    now = timezone.now()
    current_month_start = now.replace(day=1).date()

    # All-time totals
    total_income = Income.objects.filter(
        wallet__user=request.user
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    total_expense = Expense.objects.filter(
        wallet__user=request.user
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    total_lent = Lending.objects.filter(
        wallet__user=request.user
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    total_borrowed = Borrowing.objects.filter(
        wallet__user=request.user
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Current month totals for chart
    month_income = Income.objects.filter(
        wallet__user=request.user,
        date__gte=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    month_expense = Expense.objects.filter(
        wallet__user=request.user,
        date__gte=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Pending lending & borrowing
    pending_lent = Lending.objects.filter(
        wallet__user=request.user,
        is_returned=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    pending_borrowed = Borrowing.objects.filter(
        wallet__user=request.user,
        is_returned=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Recent transactions — last 10 combined
    recent_incomes = list(Income.objects.filter(wallet__user=request.user).select_related('wallet')[:5])
    recent_expenses = list(Expense.objects.filter(wallet__user=request.user).select_related('wallet')[:5])

    recent_items = []
    for inc in recent_incomes:
        recent_items.append({
            'type': 'income',
            'icon': '📥',
            'label': inc.get_source_display(),
            'amount': inc.amount,
            'date': inc.date,
            'wallet': str(inc.wallet),
            'description': inc.description,
        })
    for exp in recent_expenses:
        recent_items.append({
            'type': 'expense',
            'icon': '📤',
            'label': exp.get_category_display(),
            'amount': exp.amount,
            'date': exp.date,
            'wallet': str(exp.wallet),
            'description': exp.description,
        })
    recent_items.sort(key=lambda x: x['date'], reverse=True)
    recent_items = recent_items[:8]

    # Bar chart data (income vs expense as percentage)
    max_val = max(month_income, month_expense, Decimal('1'))
    income_pct = int((month_income / max_val) * 100)
    expense_pct = int((month_expense / max_val) * 100)

    context = {
        'wallets': wallets,
        'total_balance': total_balance,
        'total_income': total_income,
        'total_expense': total_expense,
        'total_lent': total_lent,
        'total_borrowed': total_borrowed,
        'month_income': month_income,
        'month_expense': month_expense,
        'pending_lent': pending_lent,
        'pending_borrowed': pending_borrowed,
        'recent_items': recent_items,
        'income_pct': income_pct,
        'expense_pct': expense_pct,
        'current_month': now.strftime('%B %Y'),
    }
    return render(request, 'dashboard.html', context)


# ── Wallets ────────────────────────────────────────────────────────────

@login_required
def wallet_list(request):
    wallets = Wallet.objects.filter(user=request.user)
    total = wallets.aggregate(total=Sum('balance'))['total'] or Decimal('0')
    form = WalletForm()

    if request.method == 'POST':
        form = WalletForm(request.POST)
        if form.is_valid():
            wallet = form.save(commit=False)
            wallet.user = request.user
            wallet.save()
            messages.success(request, 'Wallet created!')
            return redirect('wallet_list')

    return render(request, 'wallets.html', {
        'wallets': wallets,
        'total': total,
        'form': form,
    })


@login_required
def wallet_edit(request, pk):
    wallet = get_object_or_404(Wallet, pk=pk, user=request.user)
    form = WalletForm(instance=wallet)

    if request.method == 'POST':
        form = WalletForm(request.POST, instance=wallet)
        if form.is_valid():
            form.save()
            messages.success(request, 'Wallet updated!')
            return redirect('wallet_list')

    return render(request, 'wallet_form.html', {
        'form': form,
        'wallet': wallet,
        'title': f'Edit {wallet.name}',
    })


@login_required
def wallet_delete(request, pk):
    wallet = get_object_or_404(Wallet, pk=pk, user=request.user)
    if request.method == 'POST':
        wallet.delete()
        messages.success(request, 'Wallet deleted!')
        return redirect('wallet_list')
    return render(request, 'confirm_delete.html', {
        'object': wallet,
        'cancel_url': 'wallet_list',
        'title': 'Delete Wallet',
    })


# ── Income ─────────────────────────────────────────────────────────────

@login_required
def income_list(request):
    incomes = Income.objects.filter(wallet__user=request.user).select_related('wallet')

    # Month filter
    month = request.GET.get('month')
    year = request.GET.get('year')
    if month and year:
        incomes = incomes.filter(date__month=int(month), date__year=int(year))

    total = incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    return render(request, 'income_list.html', {
        'incomes': incomes,
        'total': total,
    })


@login_required
def income_create(request):
    form = IncomeForm()
    form.fields['wallet'].queryset = Wallet.objects.filter(user=request.user)

    if request.method == 'POST':
        form = IncomeForm(request.POST)
        form.fields['wallet'].queryset = Wallet.objects.filter(user=request.user)
        if form.is_valid():
            income = form.save()
            # Add to wallet balance
            income.wallet.balance += income.amount
            income.wallet.save()
            messages.success(request, f'+৳{income.amount} added!')
            return redirect('income_list')

    return render(request, 'income_form.html', {
        'form': form,
        'title': 'Add Income',
    })


@login_required
def income_delete(request, pk):
    income = get_object_or_404(Income, pk=pk, wallet__user=request.user)
    if request.method == 'POST':
        # Reverse the wallet balance
        income.wallet.balance -= income.amount
        income.wallet.save()
        income.delete()
        messages.success(request, 'Income record deleted!')
        return redirect('income_list')
    return render(request, 'confirm_delete.html', {
        'object': income,
        'cancel_url': 'income_list',
        'title': 'Delete Income',
    })


# ── Expense ────────────────────────────────────────────────────────────

@login_required
def expense_list(request):
    expenses = Expense.objects.filter(wallet__user=request.user).select_related('wallet')

    month = request.GET.get('month')
    year = request.GET.get('year')
    if month and year:
        expenses = expenses.filter(date__month=int(month), date__year=int(year))

    total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    return render(request, 'expense_list.html', {
        'expenses': expenses,
        'total': total,
    })


@login_required
def expense_create(request):
    form = ExpenseForm()
    form.fields['wallet'].queryset = Wallet.objects.filter(user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        form.fields['wallet'].queryset = Wallet.objects.filter(user=request.user)
        if form.is_valid():
            expense = form.save()
            # Deduct from wallet balance
            expense.wallet.balance -= expense.amount
            expense.wallet.save()
            messages.success(request, f'-৳{expense.amount} recorded!')
            return redirect('expense_list')

    return render(request, 'expense_form.html', {
        'form': form,
        'title': 'Add Expense',
    })


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, wallet__user=request.user)
    if request.method == 'POST':
        # Reverse the wallet balance
        expense.wallet.balance += expense.amount
        expense.wallet.save()
        expense.delete()
        messages.success(request, 'Expense record deleted!')
        return redirect('expense_list')
    return render(request, 'confirm_delete.html', {
        'object': expense,
        'cancel_url': 'expense_list',
        'title': 'Delete Expense',
    })


# ── Lending ────────────────────────────────────────────────────────────

@login_required
def lending_list(request):
    lendings = Lending.objects.filter(wallet__user=request.user).select_related('wallet')
    pending = lendings.filter(is_returned=False)
    returned = lendings.filter(is_returned=True)

    total_pending = pending.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    return render(request, 'lending_list.html', {
        'pending': pending,
        'returned': returned,
        'total_pending': total_pending,
    })


@login_required
def lending_create(request):
    form = LendingForm()
    form.fields['wallet'].queryset = Wallet.objects.filter(user=request.user)

    if request.method == 'POST':
        form = LendingForm(request.POST)
        form.fields['wallet'].queryset = Wallet.objects.filter(user=request.user)
        if form.is_valid():
            lending = form.save()
            messages.success(request, f'Lent ৳{lending.amount} to {lending.person_name}')
            return redirect('lending_list')

    return render(request, 'lending_form.html', {
        'form': form,
        'title': 'Lend Money',
    })


@login_required
def lending_toggle_return(request, pk):
    lending = get_object_or_404(Lending, pk=pk, wallet__user=request.user)
    if request.method == 'POST':
        lending.is_returned = not lending.is_returned
        if lending.is_returned:
            messages.success(request, f'৳{lending.amount} returned by {lending.person_name}!')
        else:
            messages.info(request, f'Marked as not returned.')
        lending.save()
    return redirect('lending_list')


@login_required
def lending_delete(request, pk):
    lending = get_object_or_404(Lending, pk=pk, wallet__user=request.user)
    if request.method == 'POST':
        lending.delete()
        messages.success(request, 'Lending record deleted!')
        return redirect('lending_list')
    return render(request, 'confirm_delete.html', {
        'object': lending,
        'cancel_url': 'lending_list',
        'title': 'Delete Lending',
    })


# ── Borrowing ──────────────────────────────────────────────────────────

@login_required
def borrowing_list(request):
    borrowings = Borrowing.objects.filter(wallet__user=request.user).select_related('wallet')
    pending = borrowings.filter(is_returned=False)
    returned = borrowings.filter(is_returned=True)

    total_pending = pending.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    return render(request, 'borrowing_list.html', {
        'pending': pending,
        'returned': returned,
        'total_pending': total_pending,
    })


@login_required
def borrowing_create(request):
    form = BorrowingForm()
    form.fields['wallet'].queryset = Wallet.objects.filter(user=request.user)

    if request.method == 'POST':
        form = BorrowingForm(request.POST)
        form.fields['wallet'].queryset = Wallet.objects.filter(user=request.user)
        if form.is_valid():
            borrowing = form.save()
            messages.success(request, f'Borrowed ৳{borrowing.amount} from {borrowing.person_name}')
            return redirect('borrowing_list')

    return render(request, 'borrowing_form.html', {
        'form': form,
        'title': 'Borrow Money',
    })


@login_required
def borrowing_toggle_return(request, pk):
    borrowing = get_object_or_404(Borrowing, pk=pk, wallet__user=request.user)
    if request.method == 'POST':
        borrowing.is_returned = not borrowing.is_returned
        if borrowing.is_returned:
            messages.success(request, f'৳{borrowing.amount} returned to {borrowing.person_name}!')
        else:
            messages.info(request, f'Marked as not returned.')
        borrowing.save()
    return redirect('borrowing_list')


@login_required
def borrowing_delete(request, pk):
    borrowing = get_object_or_404(Borrowing, pk=pk, wallet__user=request.user)
    if request.method == 'POST':
        borrowing.delete()
        messages.success(request, 'Borrowing record deleted!')
        return redirect('borrowing_list')
    return render(request, 'confirm_delete.html', {
        'object': borrowing,
        'cancel_url': 'borrowing_list',
        'title': 'Delete Borrowing',
    })
