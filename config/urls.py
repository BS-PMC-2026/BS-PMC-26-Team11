from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from users.views import (
    login_view,
    logout_view,
    home_page,
    package_list,
    package_detail,
    add_to_cart,
    cart_view,
    promotion_management,
    cancel_user_package,
    package_reservation_admin,
    admin_dashboard,
    admin_packages,
    delete_package,
    edit_package,
    paid_orders_view,
    payment_page,
    complete_payment,
    delete_package,
    admin_users_list,
    admin_delete_user,
    admin_feedbacks,
    admin_feedbacks_page,
    submit_feedback,
    feedbacks_page,
    get_user_feedbacks,
    view_all_feedbacks,
    all_feedbacks_page,
)

def signup_success(request):
    return render(request, 'signup_success.html')

urlpatterns = [
    path('', home_page, name='home'),
    path('home/', home_page, name='home_page'),
    path('packages/', package_list, name='packages'),
    path('packages/<int:package_id>/', package_detail, name='package_detail'),
    path('packages/<int:package_id>/add/', add_to_cart, name='add_to_cart'),
    path('my-orders/', cart_view, name='my_orders'),
    path('cart/', cart_view, name='cart'),
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/packages/', admin_packages, name='admin_packages_view'),
    path('admin/packages/<int:package_id>/edit/', edit_package, name='edit_package'),
    path('admin/packages/<int:package_id>/delete/', delete_package, name='delete_package'),
    path('admin/package-reservations/', package_reservation_admin, name='package_reservation_admin'),
    path('admin/promotions/', promotion_management, name='promotions'),
    path('admin/feedbacks/', admin_feedbacks_page, name='admin_feedbacks_page'),
    path('api/admin/feedbacks/', admin_feedbacks, name='admin_feedbacks_api'),
    path('admin-panel/users/', admin_users_list, name='admin_users_list'),
    path('admin-panel/users/<int:user_id>/delete/', admin_delete_user, name='admin_delete_user'),
    path('feedbacks/', feedbacks_page, name='feedbacks_page'),
    path('all-feedbacks/', all_feedbacks_page, name='all_feedbacks_page'),
    path('api/feedbacks/', submit_feedback, name='submit_feedback'),
    path('api/feedbacks/all/', view_all_feedbacks, name='view_all_feedbacks'),
    path('api/user/feedbacks/', get_user_feedbacks, name='get_user_feedbacks'),
    path('admin/', admin.site.urls),
    path('api/user/packages/<int:order_id>/', cancel_user_package, name='cancel_user_package'),
    path('users/', include('users.urls')),
    path('logout/', logout_view, name='logout'),
    path('admin/packages/<int:package_id>/delete/', delete_package, name='delete_package'),
    path('payment/', payment_page, name='payment_page'),
    path('payment/complete/', complete_payment, name='complete_payment'),
    path('paid-orders/', paid_orders_view, name='paid_orders'),
    path('signup-success/', signup_success, name='signup_success'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
