from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    mobile = models.CharField(max_length=10, unique=True)
    password = models.CharField(max_length=128)  # plain-text like Flask (simple)

    def __str__(self):
        return f"{self.user_name} ({self.user_id})"


class Snack(models.Model):
    snack_id = models.AutoField(primary_key=True)
    snack_name = models.CharField(max_length=150)
    price = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Price in rupees (positive integer)."
    )
    available_quantity = models.IntegerField(
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Quantity in stock (0 means out of stock)."
    )
    image = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Snack image file name in static/images/, e.g. 'vada-pav.jpg'."
    )

    def __str__(self):
        return f"{self.snack_name} ({self.snack_id})"


class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')

    def __str__(self):
        return f"Cart {self.cart_id} user={self.user_id}"


class CartItem(models.Model):
    cart_item_id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    snack = models.ForeignKey(Snack, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Quantity must be at least 1."
    )

    def __str__(self):
        return f"CartItem {self.cart_item_id} cart={self.cart_id} snack={self.snack_id} qty={self.quantity}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Preparing', 'Preparing'),
        ('Ready', 'Ready'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    order_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    price = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Order {self.order_id} user={self.user_id} status={self.status}"


class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    snack = models.ForeignKey(Snack, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    def __str__(self):
        return f"OrderItem {self.order_item_id} order={self.order_id} snack={self.snack_id} qty={self.quantity}"


class Payment(models.Model):
    MODE_CHOICES = [
        ('Cash', 'Cash'),
        ('Cashless', 'Cashless'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]

    payment_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    mode = models.CharField(max_length=50, choices=MODE_CHOICES, blank=True, null=True)
    payment_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Payment {self.payment_id} order={self.order_id} mode={self.mode} status={self.status}"


class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        null=True,
        blank=True
    )
    feedback_time = models.DateTimeField(default=timezone.now)
    feedback_content = models.CharField(
        max_length=getattr(settings, 'FEEDBACK_MAX_LENGTH', 350),
        blank=True,
        help_text="Max 350 characters."
    )

    def __str__(self):
        return f"Feedback {self.feedback_id} user={self.user_id} rating={self.rating}"
