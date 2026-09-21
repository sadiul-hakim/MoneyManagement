from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django_select2.forms import Select2Widget
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportMixin
from rangefilter.filters import DateRangeFilterBuilder, NumericRangeFilterBuilder
from admin_action_buttons.admin import ActionButtonsMixin

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

admin.site.site_header = "MoneyManagement"
admin.site.site_title = "MoneyManagement"
admin.site.index_title = "Welcome to MoneyManagement"


# ---------------------------------------------------------
# Forms with Select2 Searchable Dropdowns
# ---------------------------------------------------------

class IncomeAdminForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = '__all__'
        widgets = {
            'source': Select2Widget,
            'wallet': Select2Widget,
        }


class ExpenseAdminForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = '__all__'
        widgets = {
            'category': Select2Widget,
            'wallet': Select2Widget,
        }


class LendingAdminForm(forms.ModelForm):
    class Meta:
        model = Lending
        fields = '__all__'
        widgets = {
            'wallet': Select2Widget,
        }


class BorrowingAdminForm(forms.ModelForm):
    class Meta:
        model = Borrowing
        fields = '__all__'
        widgets = {
            'wallet': Select2Widget,
        }


class TransferAdminForm(forms.ModelForm):
    class Meta:
        model = Transfer
        fields = '__all__'
        widgets = {
            'user': Select2Widget,
            'from_wallet': Select2Widget,
            'to_wallet': Select2Widget,
        }


# ---------------------------------------------------------
# Import-Export Resources
# ---------------------------------------------------------

class IncomeResource(resources.ModelResource):
    source = fields.Field(
        column_name='source',
        attribute='source',
        widget=ForeignKeyWidget(IncomeSource, field='name')
    )
    wallet = fields.Field(
        column_name='wallet',
        attribute='wallet',
        widget=ForeignKeyWidget(Wallet, field='name')
    )

    class Meta:
        model = Income
        fields = ('id', 'amount', 'source', 'wallet', 'date', 'description', 'created_at')
        export_order = ('id', 'amount', 'source', 'wallet', 'date', 'description', 'created_at')


class ExpenseResource(resources.ModelResource):
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(ExpenseCategory, field='name')
    )
    wallet = fields.Field(
        column_name='wallet',
        attribute='wallet',
        widget=ForeignKeyWidget(Wallet, field='name')
    )

    class Meta:
        model = Expense
        fields = ('id', 'amount', 'category', 'wallet', 'date', 'description', 'created_at')
        export_order = ('id', 'amount', 'category', 'wallet', 'date', 'description', 'created_at')


class WalletResource(resources.ModelResource):
    class Meta:
        model = Wallet
        fields = ('id', 'user__username', 'name', 'balance', 'icon', 'created_at')
        export_order = ('id', 'user__username', 'name', 'balance', 'icon', 'created_at')


class IncomeSourceResource(resources.ModelResource):
    class Meta:
        model = IncomeSource
        fields = ('id', 'name', 'icon', 'created_at')


class ExpenseCategoryResource(resources.ModelResource):
    class Meta:
        model = ExpenseCategory
        fields = ('id', 'name', 'icon', 'created_at')


class LendingResource(resources.ModelResource):
    wallet = fields.Field(
        column_name='wallet',
        attribute='wallet',
        widget=ForeignKeyWidget(Wallet, field='name')
    )

    class Meta:
        model = Lending
        fields = ('id', 'person_name', 'amount', 'wallet', 'date_lent', 'return_date', 'notes', 'is_returned', 'created_at')


class BorrowingResource(resources.ModelResource):
    wallet = fields.Field(
        column_name='wallet',
        attribute='wallet',
        widget=ForeignKeyWidget(Wallet, field='name')
    )

    class Meta:
        model = Borrowing
        fields = ('id', 'person_name', 'amount', 'wallet', 'date_borrowed', 'return_date', 'notes', 'is_returned', 'created_at')


class TransferResource(resources.ModelResource):
    from_wallet = fields.Field(
        column_name='from_wallet',
        attribute='from_wallet',
        widget=ForeignKeyWidget(Wallet, field='name')
    )
    to_wallet = fields.Field(
        column_name='to_wallet',
        attribute='to_wallet',
        widget=ForeignKeyWidget(Wallet, field='name')
    )

    class Meta:
        model = Transfer
        fields = ('id', 'user__username', 'from_wallet', 'to_wallet', 'amount', 'date', 'description', 'created_at')


# ---------------------------------------------------------
# Admin Models
# ---------------------------------------------------------

@admin.register(IncomeSource)
class IncomeSourceAdmin(ActionButtonsMixin, ImportExportMixin, admin.ModelAdmin):
    resource_classes = [IncomeSourceResource]
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name']


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(ActionButtonsMixin, ImportExportMixin, admin.ModelAdmin):
    resource_classes = [ExpenseCategoryResource]
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name']


@admin.register(Wallet)
class WalletAdmin(ActionButtonsMixin, ImportExportMixin, admin.ModelAdmin):
    resource_classes = [WalletResource]
    list_display = ['name', 'balance', 'icon', 'user', 'created_at']
    search_fields = ['name', 'user__username']
    list_filter = [('balance', NumericRangeFilterBuilder()), 'user']


@admin.register(Income)
class IncomeAdmin(ActionButtonsMixin, ImportExportMixin, admin.ModelAdmin):
    form = IncomeAdminForm
    resource_classes = [IncomeResource]
    list_display = ['amount', 'source', 'wallet', 'date', 'description']
    list_filter = [
        ('date', DateRangeFilterBuilder(title='Date Range')),
        ('amount', NumericRangeFilterBuilder(title='Amount Range')),
        'source',
        'wallet',
    ]
    search_fields = ['description', 'source__name', 'wallet__name']
    date_hierarchy = 'date'


@admin.register(Expense)
class ExpenseAdmin(ActionButtonsMixin, ImportExportMixin, admin.ModelAdmin):
    form = ExpenseAdminForm
    resource_classes = [ExpenseResource]
    list_display = ['amount', 'category', 'wallet', 'date', 'description']
    list_filter = [
        ('date', DateRangeFilterBuilder(title='Date Range')),
        ('amount', NumericRangeFilterBuilder(title='Amount Range')),
        'category',
        'wallet',
    ]
    search_fields = ['description', 'category__name', 'wallet__name']
    date_hierarchy = 'date'


@admin.register(Lending)
class LendingAdmin(ActionButtonsMixin, ImportExportMixin, admin.ModelAdmin):
    form = LendingAdminForm
    resource_classes = [LendingResource]
    list_display = ['person_name', 'amount', 'wallet',
                    'date_lent', 'return_date', 'status_badge']
    list_filter = [
        'is_returned',
        ('date_lent', DateRangeFilterBuilder(title='Lent Date Range')),
        ('amount', NumericRangeFilterBuilder(title='Amount Range')),
        'wallet',
    ]
    search_fields = ['person_name', 'notes', 'wallet__name']
    actions = ['mark_as_returned', 'mark_as_pending']

    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.is_returned:
            return format_html('<span style="color: #10B981; font-weight: bold;">✅ Returned</span>')
        return format_html('<span style="color: #F59E0B; font-weight: bold;">⏳ Pending</span>')

    @admin.action(description="Mark selected as Returned")
    def mark_as_returned(self, request, queryset):
        queryset.update(is_returned=True)

    @admin.action(description="Mark selected as Pending")
    def mark_as_pending(self, request, queryset):
        queryset.update(is_returned=False)


@admin.register(Borrowing)
class BorrowingAdmin(ActionButtonsMixin, ImportExportMixin, admin.ModelAdmin):
    form = BorrowingAdminForm
    resource_classes = [BorrowingResource]
    list_display = ['person_name', 'amount', 'wallet',
                    'date_borrowed', 'return_date', 'status_badge']
    list_filter = [
        'is_returned',
        ('date_borrowed', DateRangeFilterBuilder(title='Borrowed Date Range')),
        ('amount', NumericRangeFilterBuilder(title='Amount Range')),
        'wallet',
    ]
    search_fields = ['person_name', 'notes', 'wallet__name']
    actions = ['mark_as_returned', 'mark_as_pending']

    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.is_returned:
            return format_html('<span style="color: #10B981; font-weight: bold;">✅ Returned</span>')
        return format_html('<span style="color: #EF4444; font-weight: bold;">⏳ Pending</span>')

    @admin.action(description="Mark selected as Returned")
    def mark_as_returned(self, request, queryset):
        queryset.update(is_returned=True)

    @admin.action(description="Mark selected as Pending")
    def mark_as_pending(self, request, queryset):
        queryset.update(is_returned=False)


@admin.register(Transfer)
class TransferAdmin(ActionButtonsMixin, ImportExportMixin, admin.ModelAdmin):
    form = TransferAdminForm
    resource_classes = [TransferResource]
    list_display = ['from_wallet', 'to_wallet',
                    'amount', 'date', 'description', 'created_at']
    list_filter = [
        ('date', DateRangeFilterBuilder(title='Transfer Date Range')),
        ('amount', NumericRangeFilterBuilder(title='Amount Range')),
        'from_wallet',
        'to_wallet',
    ]
    search_fields = ['description', 'from_wallet__name', 'to_wallet__name']
    date_hierarchy = 'date'
