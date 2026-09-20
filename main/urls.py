from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Wallets
    path('wallets/', views.wallet_list, name='wallet_list'),
    path('wallets/<int:pk>/edit/', views.wallet_edit, name='wallet_edit'),
    path('wallets/<int:pk>/delete/', views.wallet_delete, name='wallet_delete'),

    # Income
    path('income/', views.income_list, name='income_list'),
    path('income/add/', views.income_create, name='income_create'),
    path('income/<int:pk>/delete/', views.income_delete, name='income_delete'),

    # Expense
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),

    # Lending
    path('lending/', views.lending_list, name='lending_list'),
    path('lending/add/', views.lending_create, name='lending_create'),
    path('lending/<int:pk>/toggle/', views.lending_toggle_return, name='lending_toggle'),
    path('lending/<int:pk>/delete/', views.lending_delete, name='lending_delete'),

    # Borrowing
    path('borrowing/', views.borrowing_list, name='borrowing_list'),
    path('borrowing/add/', views.borrowing_create, name='borrowing_create'),
    path('borrowing/<int:pk>/toggle/', views.borrowing_toggle_return, name='borrowing_toggle'),
    path('borrowing/<int:pk>/delete/', views.borrowing_delete, name='borrowing_delete'),

    # Transfers
    path('transfers/', views.transfer_list, name='transfer_list'),
    path('transfers/add/', views.transfer_create, name='transfer_create'),
    path('transfers/<int:pk>/delete/', views.transfer_delete, name='transfer_delete'),
]

