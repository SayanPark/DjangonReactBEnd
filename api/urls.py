from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from api import views as api_views
from django.http import JsonResponse
from django.core.management import call_command

def run_migrations(request):
    try:
        call_command('migrate')
        return JsonResponse({'message': 'Migrations completed successfully.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

urlpatterns = [
    # Userauths API Endpoints
    path('user/token/', api_views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('user/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/register/', api_views.RegisterView.as_view(), name='auth_register'),
    path('user/profile/<user_id>/', api_views.ProfileView.as_view(), name='user_profile'),
    path('user/all/', api_views.UserListAPIView.as_view(), name='user_list'),
    path('user/password-reset/<email>/', api_views.PasswordEmailVerify.as_view(), name='password_reset'),
    path('user/password-change/', api_views.PasswordChangeView.as_view(), name='password_change'),
    path('user/count/', api_views.UserCountAPIView.as_view(), name='user_count'),
    path('likes/total/', api_views.TotalLikesCountAPIView.as_view(), name='total_likes_count'),
    path('user/send-signup-email/', api_views.send_signup_email, name='send_signup_email'),
    path('user/send-new-post-update-email/', api_views.send_new_post_update_email, name='send_new_post_update_email'),
    path('user/unsubscribe/<uidb64>/', api_views.UnsubscribeView.as_view(), name='user_unsubscribe'),
    path('user/change-superuser-status/', api_views.ChangeSuperuserStatusAPIView.as_view(), name='change_superuser_status'),
    # Post Endpoints
    path('post/category/list/', api_views.CategoryListAPIView.as_view()),
    path('post/category/posts/<category_slug>/', api_views.PostCategoryListAPIView.as_view()),
    path('post/lists/', api_views.PostListAPIView.as_view()),
    path('post/most-viewed/', api_views.MostViewedPostListAPIView.as_view()),
    path('post/detail/<slug>/', api_views.PostDetailAPIView.as_view()),
    path('post/like-post/', api_views.LikePostAPiView.as_view()),
    path('post/comment-post/', api_views.PostCommentAPIView.as_view()),
    path('post/bookmark-post/', api_views.BookmarkPostAPIView.as_view()),
    # Dashboard APIS
    path('author/dashboard/stats/<user_id>/', api_views.DashboardStats.as_view()),
    path('author/dashboard/post-list/<user_id>/', api_views.DashboardPostLists.as_view()),
    path('author/dashboard/comment-list/<user_id>/', api_views.DashboardCommentLists.as_view()),
    path('author/dashboard/noti-list/<user_id>/', api_views.DashboardNotificationLists.as_view()),
    path('author/dashboard/noti-mark-seen/', api_views.DashboardMarkNotificationAsSeen.as_view()),
    path('author/dashboard/reply-comment/', api_views.DashboardReplyCommentAPIView.as_view()),
    path('author/dashboard/delete-comment/', api_views.DashboardDeleteCommentAPIView.as_view()),
    path('author/dashboard/delete-contact-message/', api_views.DashboardDeleteContactMessageAPIView.as_view()),
    path('author/dashboard/post-create/', api_views.DashboardPostCreateAPIView.as_view()),
    path('author/dashboard/post-detail/<user_id>/<post_id>/', api_views.DashboardPostEditAPIView.as_view()),
    path('author/dashboard/send-email/', api_views.DashboardSendEmailAPIView.as_view()),
    # Contact Message Endpoints
    path('contact-message/create/', api_views.ContactMessageCreateAPIView.as_view()),
    path('contact-message/list/', api_views.ContactMessageListAPIView.as_view()),
    path('contact-message/reply/', api_views.ContactMessageReplyAPIView.as_view()),
    # Migration trigger endpoint
    path('run-migrations/', run_migrations),
]
