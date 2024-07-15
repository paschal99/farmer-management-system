from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Profile(models.Model):
    role_choices = (
        ('farmer', 'farmer'),
        ('buyer', 'buyer'),
    )
    gender = (('male', 'male'), ('female', 'female'))
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10, null=False, blank=False)
    location = models.CharField(max_length=100, blank=True)
    sex = models.CharField(choices=gender, max_length=6)
    role = models.CharField(choices=role_choices, max_length=6, default='farmer')

    def __str__(self):
        return self.user.username


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username}'s Account"


class LoanRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    account = models.OneToOneField(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_requested = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return str(self.user)



class LoanFeedback(models.Model):
    loan_request = models.OneToOneField(LoanRequest, on_delete=models.CASCADE)
    from_account = models.ForeignKey(Account, related_name='transferred_from', on_delete=models.CASCADE)
    to_account = models.ForeignKey(Account, related_name='transferred_to', on_delete=models.CASCADE)
    amount_transferred = models.DecimalField(max_digits=10, decimal_places=2)
    date_transferred = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.loan_request.user.username}'s Loan Request"


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    date_sent = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"


class Feedback(models.Model):
    sender = models.ForeignKey(User, related_name='sent_feedback', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_feedback', on_delete=models.CASCADE)
    content = models.TextField()
    date_sent = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"


class Notification(models.Model):
    sender = models.ForeignKey(User, related_name='sent_notifications', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Product(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('sold_out', 'sold_out'),
    ]
    seller = models.ForeignKey(User, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    delivered = models.BooleanField(max_length=5,default=False,null=True)
    location = models.CharField(max_length=50, null=True, blank=True)
    quantity_available = models.IntegerField(default=0)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='images', null=True, blank=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='Pending')

    def __str__(self):
        return self.name

    def total_price(self):
        return self.quantity_available * self.price_per_unit

class Order(models.Model):
    buyer = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_ordered = models.IntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    order_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity_ordered * self.product.price_per_unit
        self.product.quantity_available -= self.quantity_ordered
        if self.product.quantity_available <= 0:
            self.product.payment_status = 'Sold Out'
        self.product.save()
        super().save(*args, **kwargs)