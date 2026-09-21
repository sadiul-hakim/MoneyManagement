import calendar
from collections import defaultdict
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .models import Wallet, Income, Expense, Lending, Borrowing, Transfer
from .forms import WalletForm, IncomeForm, ExpenseForm, LendingForm, BorrowingForm, TransferForm


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
    recent_incomes = list(Income.objects.filter(wallet__user=request.user).select_related('wallet', 'source')[:5])
    recent_expenses = list(Expense.objects.filter(wallet__user=request.user).select_related('wallet', 'category')[:5])

    recent_items = []
    for inc in recent_incomes:
        recent_items.append({
            'type': 'income',
            'icon': inc.source.icon if inc.source and inc.source.icon else '📥',
            'label': inc.source.name if inc.source else 'Income',
            'amount': inc.amount,
            'date': inc.date,
            'wallet': str(inc.wallet),
            'description': inc.description,
        })
    for exp in recent_expenses:
        recent_items.append({
            'type': 'expense',
            'icon': exp.category.icon if exp.category and exp.category.icon else '📤',
            'label': exp.category.name if exp.category else 'Expense',
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
    incomes = Income.objects.filter(wallet__user=request.user).select_related('wallet', 'source')

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
def income_edit(request, pk):
    income = get_object_or_404(Income, pk=pk, wallet__user=request.user)
    form = IncomeForm(instance=income)
    form.fields['wallet'].queryset = Wallet.objects.filter(user=request.user)

    if request.method == 'POST':
        old_wallet = income.wallet
        old_amount = income.amount
        form = IncomeForm(request.POST, instance=income)
        form.fields['wallet'].queryset = Wallet.objects.filter(user=request.user)
        if form.is_valid():
            with transaction.atomic():
                updated_income = form.save(commit=False)
                new_wallet = updated_income.wallet
                new_amount = updated_income.amount

                if old_wallet.pk == new_wallet.pk:
                    w = Wallet.objects.select_for_update().get(pk=old_wallet.pk)
                    w.balance = w.balance - old_amount + new_amount
                    w.save()
                else:
                    w_old = Wallet.objects.select_for_update().get(pk=old_wallet.pk)
                    w_new = Wallet.objects.select_for_update().get(pk=new_wallet.pk)
                    w_old.balance -= old_amount
                    w_new.balance += new_amount
                    w_old.save()
                    w_new.save()

                updated_income.save()

            messages.success(request, 'Income updated successfully!')
            return redirect('income_list')

    return render(request, 'income_form.html', {
        'form': form,
        'title': 'Edit Income',
        'is_edit': True,
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
    expenses = Expense.objects.filter(wallet__user=request.user).select_related('wallet', 'category')

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
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk, wallet__user=request.user)
    form = ExpenseForm(instance=expense)
    form.fields['wallet'].queryset = Wallet.objects.filter(user=request.user)

    if request.method == 'POST':
        old_wallet = expense.wallet
        old_amount = expense.amount
        form = ExpenseForm(request.POST, instance=expense)
        form.fields['wallet'].queryset = Wallet.objects.filter(user=request.user)
        if form.is_valid():
            with transaction.atomic():
                updated_expense = form.save(commit=False)
                new_wallet = updated_expense.wallet
                new_amount = updated_expense.amount

                if old_wallet.pk == new_wallet.pk:
                    w = Wallet.objects.select_for_update().get(pk=old_wallet.pk)
                    w.balance = w.balance + old_amount - new_amount
                    w.save()
                else:
                    w_old = Wallet.objects.select_for_update().get(pk=old_wallet.pk)
                    w_new = Wallet.objects.select_for_update().get(pk=new_wallet.pk)
                    w_old.balance += old_amount
                    w_new.balance -= new_amount
                    w_old.save()
                    w_new.save()

                updated_expense.save()

            messages.success(request, 'Expense updated successfully!')
            return redirect('expense_list')

    return render(request, 'expense_form.html', {
        'form': form,
        'title': 'Edit Expense',
        'is_edit': True,
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


# ── Transfers ──────────────────────────────────────────────────────────

@login_required
def transfer_list(request):
    transfers = Transfer.objects.filter(user=request.user).select_related('from_wallet', 'to_wallet')

    # Month filter
    month = request.GET.get('month')
    year = request.GET.get('year')
    if month and year:
        transfers = transfers.filter(date__month=int(month), date__year=int(year))

    total = transfers.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    return render(request, 'transfer_list.html', {
        'transfers': transfers,
        'total': total,
    })


@login_required
def transfer_create(request):
    user_wallets = Wallet.objects.filter(user=request.user)
    form = TransferForm()
    form.fields['from_wallet'].queryset = user_wallets
    form.fields['to_wallet'].queryset = user_wallets

    if request.method == 'POST':
        form = TransferForm(request.POST)
        form.fields['from_wallet'].queryset = user_wallets
        form.fields['to_wallet'].queryset = user_wallets
        if form.is_valid():
            with transaction.atomic():
                transfer = form.save(commit=False)
                transfer.user = request.user

                from_w = Wallet.objects.select_for_update().get(pk=transfer.from_wallet.pk)
                to_w = Wallet.objects.select_for_update().get(pk=transfer.to_wallet.pk)

                if from_w.balance < transfer.amount:
                    messages.error(request, f"Insufficient balance in {from_w.name}.")
                    return render(request, 'transfer_form.html', {'form': form, 'title': 'Transfer Money'})

                from_w.balance -= transfer.amount
                to_w.balance += transfer.amount
                from_w.save()
                to_w.save()
                transfer.save()

            messages.success(request, f'Transferred ৳{transfer.amount} from {from_w.name} to {to_w.name}!')
            return redirect('transfer_list')

    return render(request, 'transfer_form.html', {
        'form': form,
        'title': 'Transfer Money',
    })


@login_required
def transfer_delete(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk, user=request.user)
    if request.method == 'POST':
        with transaction.atomic():
            from_w = Wallet.objects.select_for_update().get(pk=transfer.from_wallet.pk)
            to_w = Wallet.objects.select_for_update().get(pk=transfer.to_wallet.pk)
            from_w.balance += transfer.amount
            to_w.balance -= transfer.amount
            from_w.save()
            to_w.save()
            transfer.delete()
        messages.success(request, 'Transfer record deleted and balances reverted!')
        return redirect('transfer_list')
    return render(request, 'confirm_delete.html', {
        'object': transfer,
        'cancel_url': 'transfer_list',
        'title': 'Delete Transfer',
    })


# ── Reports & Analytics ────────────────────────────────────────────────

@login_required
def reports_view(request):
    user = request.user
    incomes_qs = Income.objects.filter(wallet__user=user).select_related('source')
    expenses_qs = Expense.objects.filter(wallet__user=user).select_related('category')

    # Get distinct years for filter
    income_years = incomes_qs.dates('date', 'year', order='DESC')
    expense_years = expenses_qs.dates('date', 'year', order='DESC')
    available_years = sorted(list(set(
        [d.year for d in income_years] + [d.year for d in expense_years]
    )), reverse=True)

    selected_year = request.GET.get('year', '').strip()
    if selected_year and selected_year.isdigit():
        selected_year = int(selected_year)
        incomes_qs = incomes_qs.filter(date__year=selected_year)
        expenses_qs = expenses_qs.filter(date__year=selected_year)
    else:
        selected_year = None

    # Overall totals
    total_income = incomes_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_expense = expenses_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    net_savings = total_income - total_expense
    savings_rate = 0
    if total_income > 0:
        savings_rate = round(float((net_savings / total_income) * 100), 1)

    # Monthly breakdown (YYYY-MM)
    monthly_data = defaultdict(lambda: {'income': Decimal('0'), 'expense': Decimal('0')})
    for inc in incomes_qs:
        key = inc.date.strftime('%Y-%m')
        monthly_data[key]['income'] += inc.amount

    for exp in expenses_qs:
        key = exp.date.strftime('%Y-%m')
        monthly_data[key]['expense'] += exp.amount

    monthly_list = []
    for month_key in sorted(monthly_data.keys(), reverse=True):
        m_inc = monthly_data[month_key]['income']
        m_exp = monthly_data[month_key]['expense']
        m_net = m_inc - m_exp
        y, m = month_key.split('-')
        month_name = calendar.month_name[int(m)]
        month_label = f"{month_name} {y}"

        max_val = max(m_inc, m_exp, Decimal('1'))
        inc_pct = int((m_inc / max_val) * 100) if max_val > 0 else 0
        exp_pct = int((m_exp / max_val) * 100) if max_val > 0 else 0

        monthly_list.append({
            'key': month_key,
            'label': month_label,
            'year': int(y),
            'month': int(m),
            'income': m_inc,
            'expense': m_exp,
            'net': m_net,
            'income_pct': inc_pct,
            'expense_pct': exp_pct,
        })

    # Total Income by Source
    sources_summary = (
        incomes_qs.values('source__name', 'source__icon')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )
    source_breakdown = []
    for s in sources_summary:
        s_total = s['total'] or Decimal('0')
        pct = round(float((s_total / total_income) * 100), 1) if total_income > 0 else 0
        source_breakdown.append({
            'name': s['source__name'] or 'General',
            'icon': s['source__icon'] or '📥',
            'total': s_total,
            'count': s['count'],
            'percentage': pct,
        })

    # Total Cost by Category
    categories_summary = (
        expenses_qs.values('category__name', 'category__icon')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )
    category_breakdown = []
    for c in categories_summary:
        c_total = c['total'] or Decimal('0')
        pct = round(float((c_total / total_expense) * 100), 1) if total_expense > 0 else 0
        category_breakdown.append({
            'name': c['category__name'] or 'General',
            'icon': c['category__icon'] or '📤',
            'total': c_total,
            'count': c['count'],
            'percentage': pct,
        })

    context = {
        'available_years': available_years,
        'selected_year': selected_year,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_savings': net_savings,
        'savings_rate': savings_rate,
        'monthly_list': monthly_list,
        'source_breakdown': source_breakdown,
        'category_breakdown': category_breakdown,
    }
    return render(request, 'reports.html', context)


