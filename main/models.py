from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Wallet(models.Model):
    """Represents a balance location — cash in hand, bank, bKash, etc."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    icon = models.CharField(max_length=10, default='💰', help_text='Emoji icon for the wallet')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.icon} {self.name}"


class Income(models.Model):
    """Records incoming money."""
    SOURCE_CHOICES = [
        ('salary', 'Salary'),
        ('freelance', 'Freelance'),
        ('business', 'Business'),
        ('gift', 'Gift'),
        ('investment', 'Investment'),
        ('refund', 'Refund'),
        ('other', 'Other'),
    ]

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='salary')
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='incomes')
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"+{self.amount} ({self.get_source_display()}) on {self.date}"


class Expense(models.Model):
    """Records outgoing money."""
    CATEGORY_CHOICES = [
        ('food', 'Food & Groceries'),
        ('transport', 'Transport'),
        ('wifi', 'WiFi Bill'),
        ('internet', 'Internet'),
        ('mobile', 'Mobile Recharge'),
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('dress', 'Dress & Clothing'),
        ('health', 'Health & Medicine'),
        ('education', 'Education'),
        ('entertainment', 'Entertainment'),
        ('shopping', 'Shopping'),
        ('donation', 'Donation'),
        ('other', 'Other'),
    ]

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='food')
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='expenses')
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"-{self.amount} ({self.get_category_display()}) on {self.date}"


class Lending(models.Model):
    """Money you lent to someone."""
    person_name = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='lendings')
    date_lent = models.DateField(default=timezone.now)
    return_date = models.DateField(null=True, blank=True, help_text='Expected return date')
    notes = models.CharField(max_length=255, blank=True)
    is_returned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_returned', '-date_lent']

    def __str__(self):
        status = '✅' if self.is_returned else '⏳'
        return f"{status} Lent {self.amount} to {self.person_name}"


class Borrowing(models.Model):
    """Money you borrowed from someone."""
    person_name = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='borrowings')
    date_borrowed = models.DateField(default=timezone.now)
    return_date = models.DateField(null=True, blank=True, help_text='Expected return date')
    notes = models.CharField(max_length=255, blank=True)
    is_returned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_returned', '-date_borrowed']

    def __str__(self):
        status = '✅' if self.is_returned else '⏳'
        return f"{status} Borrowed {self.amount} from {self.person_name}"
