from django.urls import path
from . import views

urlpatterns = [
    path('', views.register, name='register'),         
    path('home/', views.home, name='home'),            
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/delete/', views.delete_profile, name='delete_profile'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/update_item/', views.update_cart_item, name='update_cart_item'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/<str:method>/', views.payment, name='payment'),
    path('feedback/', views.feedback, name='feedback'),
    path('confirm_payment/<str:method>/', views.confirm_payment, name='confirm_payment'),
    path('orders/', views.orders, name='orders'),
    path('orders/view/<int:order_id>/', views.view_order, name='view_order'),
    path('live-orders/', views.live_orders, name='live_orders'),

    # AJAX APIs (for JS auto-refresh, no page reload)
    path('api/cart-count/', views.api_cart_count, name='api_cart_count'),
    path('api/order-status/<int:order_id>/', views.api_order_status, name='api_order_status'),
    path('api/user-latest-orders/', views.api_user_latest_orders, name='api_user_latest_orders'),

    # owner side
    path('owner/dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/customers/', views.owner_customers, name='owner_customers'),

    path('owner/feedbacks/', views.owner_feedbacks_list, name='owner_feedbacks_list'),
    path('owner/feedbacks/delete/<int:feedback_id>/', views.owner_delete_feedback, name='owner_delete_feedback'),

    path('owner/orders/', views.owner_orders_list, name='owner_orders_list'),
    path('owner/orders/change_status/<int:order_id>/', views.owner_change_order_status, name='owner_change_order_status'),
    path('owner/orders/view/<int:order_id>/', views.owner_view_order, name='owner_view_order'),

    path('owner/payments/', views.owner_payments_list, name='owner_payments_list'),
    path('owner/payments/change_status/<int:payment_id>/', views.owner_change_payment_status, name='owner_change_payment_status'),

    path('owner/inventory/', views.owner_inventory, name='owner_inventory'),
    path('owner/inventory/update/<int:snack_id>/', views.owner_update_inventory, name='owner_update_inventory'),
    path('owner/snacks/add/', views.owner_add_snack, name='owner_add_snack'),
    path('owner/snacks/delete/<int:snack_id>/', views.owner_delete_snack, name='owner_delete_snack'),

    path('owner/reports/', views.owner_reports, name='owner_reports'),
    path('owner/reports/orders/', views.owner_reports_orders, name='owner_reports_orders'),
    path('owner/reports/payments/', views.owner_reports_payments, name='owner_reports_payments'),

]
