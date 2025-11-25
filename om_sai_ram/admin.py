from django.contrib import admin
from .models import User, Snack, Cart, CartItem, Order, OrderItem, Payment, Feedback


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'user_name', 'email', 'mobile')
    search_fields = ('user_name', 'email', 'mobile')


@admin.register(Snack)
class SnackAdmin(admin.ModelAdmin):
    list_display = ('snack_id', 'snack_name', 'price', 'available_quantity')
    search_fields = ('snack_name',)
    list_editable = ('price', 'available_quantity')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'user')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart_item_id', 'cart', 'snack', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'order_time', 'status', 'price')
    list_filter = ('status', 'order_time')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_item_id', 'order', 'snack', 'quantity')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'order', 'mode', 'status', 'payment_time')
    list_filter = ('mode', 'status')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('feedback_id', 'user', 'rating', 'feedback_time')
    list_filter = ('rating',)
