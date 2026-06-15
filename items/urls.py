from django.urls import path
from . import views

app_name = "items"

urlpatterns = [
    path('', views.home, name='home'),            
    path('welcome/', views.welcome, name='welcome'),
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    
    # Database-backed views (new system)
    path('dashboard/', views.dashboard_db, name='dashboard'),
    path('profile/', views.profile_db, name='profile'),
    path('lost-items/', views.lost_items_db, name='lost_items'),
    path('found-items/', views.found_items_db, name='found_items'),
    path('item/<int:item_id>/', views.item_detail_db, name='detail'),
    path('item/<int:item_id>/edit/', views.edit_item_db, name='edit_item'),
    path('item/<int:item_id>/delete/', views.delete_item_db, name='delete_item'),
    path('post/', views.post_item_db, name='post'),
    
    # Chat routes
    path('chats/', views.chats_home, name='chats'),
    path('item/<int:item_id>/chat/', views.start_chat, name='start_chat'),
    path('chat/<int:conversation_id>/', views.chat_detail, name='chat_detail'),
    path('chat/<int:conversation_id>/end/', views.end_chat, name='end_chat'),
    path('claim/<int:claim_id>/chat/', views.start_claim_chat, name='start_claim_chat'),

    # Verification system
    path('item/<int:item_id>/claim/', views.claim_item, name='claim_item'),
    path('claim/<int:claim_id>/verify/', views.verify_claim, name='verify_claim'),
]
