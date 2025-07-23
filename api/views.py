from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.db.models import Sum
from django.urls import reverse
# Restframework
from rest_framework import status
from rest_framework.decorators import api_view, APIView, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.views import APIView
# Others
import json
import logging
import random
import base64
import re
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from datetime import datetime
# Custom Imports
from api import models as gomini
from api import serializer as serializers
from api.utils.draftjs_to_html import draftjs_to_html

class DashboardSendEmailAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'message', 'signature'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'signature': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )
    def post(self, request):
        email = request.data.get('email')
        message = request.data.get('message')
        signature = request.data.get('signature')

        if not email or not message or not signature:
            return Response({"error": "email, message, and signature are required"}, status=status.HTTP_400_BAD_REQUEST)

        subject = "پاسخ به پیام شما"
        full_message = f"{message}\n\n{signature}"

        text_body = full_message
        html_body = f"<p>{message}</p><p>{signature}</p>"

        msg = EmailMultiAlternatives(
            subject=subject,
            from_email=f'"ShahreZananeKarafarin" <{settings.EMAIL_HOST_USER}>',
            to=[email],
            body=text_body
        )
        msg.attach_alternative(html_body, "text/html")
        try:
            msg.send()
            return Response({"message": "Email sent successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logging.error(f"Failed to send email to {email}: {e}")
            return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UnsubscribeView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, uidb64):
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = gomini.User.objects.get(id=user_id)
            user.receive_updates = False
            user.save()
            # Redirect to frontend unsubscribe success page
            frontend_base_url = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173")
            frontend_url = f"{frontend_base_url}/unsubscribe-success/"
            return redirect(frontend_url)
        except (TypeError, ValueError, OverflowError, gomini.User.DoesNotExist):
            return HttpResponse("<h2>لینک لغو اشتراک نامعتبر است.</h2>", status=400)

class MyTokenObtainPairView(TokenObtainPairView):
    # Here, it specifies the serializer class to be used with this view.
    serializer_class = serializers.MyTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    # It sets the queryset for this view to retrieve all User objects.
    queryset = gomini.User.objects.all()
    # It specifies that the view allows any user (no authentication required).
    permission_classes = (AllowAny,)
    # It sets the serializer class to be used with this view.
    serializer_class = serializers.RegisterSerializer

class UserCountAPIView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        user_count = gomini.User.objects.count()
        return Response({"user_count": user_count}, status=status.HTTP_200_OK)

class TotalLikesCountAPIView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        total_likes = gomini.Post.objects.aggregate(total_likes=Sum("likes"))['total_likes'] or 0
        return Response({"total_likes": total_likes}, status=status.HTTP_200_OK)

def generate_numeric_otp(length=7):
    # Generate a random 7-digit OTP
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp

class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = serializers.UserProfileSerializer

    def get_object(self):
        user_id = self.kwargs.get('user_id')

        # Validate user_id is a valid integer
        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            raise ValidationError({"user_id": "Invalid user_id parameter"})

        try:
            user = gomini.User.objects.get(id=user_id_int)
        except gomini.User.DoesNotExist:
            
            raise NotFound(detail="User not found")

        return user

class UserListAPIView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = serializers.UserSerializer

    def get_queryset(self):
        return gomini.User.objects.all()

class PasswordEmailVerify(generics.RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = serializers.UserSerializer
    
    def get_object(self):
        email = self.kwargs['email']
        user = gomini.User.objects.get(email=email)
        
        if user:
            user.otp = generate_numeric_otp()
            uidb64 = base64.urlsafe_b64encode(str(user.pk).encode()).decode()
            
             # Generate a token and include it in the reset link sent via email
            refresh = RefreshToken.for_user(user)
            reset_token = str(refresh.access_token)

            # Store the reset_token in the user model for later verification
            user.reset_token = reset_token
            user.save()

            link = f"{settings.FRONTEND_BASE_URL}/create-new-password?otp={user.otp}&uidb64={uidb64}&reset_token={reset_token}"
            
            merge_data = {
                'link': link, 
                'full_name': user.full_name,
            }
            subject = f"درخواست بازنشانی رمز عبور"
            text_body = render_to_string("email/password_reset.txt", merge_data)
            html_body = render_to_string("email/password_reset.html", merge_data)
            
            msg = EmailMultiAlternatives(
                subject=subject, from_email='"ShahreZananeKarafarin" <' + settings.EMAIL_HOST_USER + '>',
                to=[user.email], body=text_body
            )
            msg.attach_alternative(html_body, "text/html")
            try:
                msg.send()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send password reset email to {user.email}: {e}")
                raise e
        return user
    
class PasswordChangeView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = serializers.UserSerializer
    
    def create(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        payload = request.data   
        logger.debug(f"PasswordChangeView payload: {payload}")
        otp = payload.get('otp')
        uidb64 = payload.get('uidb64')
        reset_token = payload.get('reset_token')
        password = payload.get('password') 

        if not otp or not uidb64 or not reset_token or not password:
            logger.error("Missing required fields in password change request")
            raise ValidationError("Missing required fields")

        try:
            user_id = int(base64.urlsafe_b64decode(uidb64).decode())
        except Exception:
            logger.error("Invalid uidb64 in password change request")
            raise ValidationError("Invalid uidb64")

        try:
            user = gomini.User.objects.get(id=user_id, otp=otp, reset_token=reset_token)
        except gomini.User.DoesNotExist:
            logger.error("Invalid token or OTP in password change request")
            return Response({"message": "Invalid token or OTP"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.otp = ""
        user.reset_token = ""
        user.save()
        
        return Response({"message": "Password Changed Successfully"}, status=status.HTTP_201_CREATED)

######################## Post APIs ########################

class CategoryListAPIView(generics.ListAPIView):
    serializer_class = serializers.CategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return gomini.Category.objects.all()

class PostCategoryListAPIView(generics.ListAPIView):
    serializer_class = serializers.PostSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        category_slug = self.kwargs['category_slug'] 
        category = gomini.Category.objects.get(slug=category_slug)
        return gomini.Post.objects.filter(category=category, status="Active")

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class PostListAPIView(generics.ListAPIView):
    serializer_class = serializers.PostSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return gomini.Post.objects.all().order_by('-date')

class MostViewedPostListAPIView(generics.ListAPIView):
    serializer_class = serializers.PostSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return gomini.Post.objects.all().order_by('-view', '-date')

class PostDetailAPIView(generics.RetrieveAPIView):
    serializer_class = serializers.PostSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        slug = self.kwargs['slug']
        try:
            post = gomini.Post.objects.get(slug=slug, status="Active")
        except gomini.Post.DoesNotExist:
            raise NotFound(detail="Post not found")
        post.view += 1
        post.save()
        return post

class LikePostAPiView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'post_id': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )
    def post(self, request):
        user_id = request.data['user_id']
        post_id = request.data['post_id']

        user = gomini.User.objects.get(id=user_id)
        post = gomini.Post.objects.get(id=post_id)

        # Check if post has already been liked by this user
        if user in post.likes.all():
            # If liked, unlike post
            post.likes.remove(user)
            return Response({"message": "Post Disliked"}, status=status.HTTP_200_OK)
        else:
            # If post hasn't been liked, like the post by adding user to set of poeple who have liked the post
            post.likes.add(user)
            
            # Create Notification for Author
            gomini.Notification.objects.create(
                user=post.user,
                post=post,
                type="Like",
            )
            return Response({"message": "Post Liked"}, status=status.HTTP_201_CREATED)
        
class PostCommentAPIView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'post_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'comment': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )
    def post(self, request):
        # Get data from request.data (frontend)
        post_id = request.data['post_id']
        name = request.data['name']
        email = request.data['email']
        comment = request.data['comment']

        post = gomini.Post.objects.get(id=post_id)

        # Create Comment
        gomini.Comment.objects.create(
            post=post,
            name=name,
            email=email,
            comment=comment,
        )

        # Notification
        gomini.Notification.objects.create(
            user=post.user,
            post=post,
            type="Comment",
        )

        # Return response back to the frontend
        return Response({"message": "Commented Sent"}, status=status.HTTP_201_CREATED)

class BookmarkPostAPIView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'post_id': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )
    def post(self, request):
        user_id = request.data['user_id']
        post_id = request.data['post_id']

        user = gomini.User.objects.get(id=user_id)
        post = gomini.Post.objects.get(id=post_id)

        bookmark = gomini.Bookmark.objects.filter(post=post, user=user).first()
        if bookmark:
            # Remove post from bookmark
            bookmark.delete()
            return Response({"message": "Post Un-Bookmarked"}, status=status.HTTP_200_OK)
        else:
            gomini.Bookmark.objects.create(
                user=user,
                post=post
            )

            # Notification
            gomini.Notification.objects.create(
                user=post.user,
                post=post,
                type="Bookmark",
            )
            return Response({"message": "Post Bookmarked"}, status=status.HTTP_201_CREATED)

######################## Author Dashboard APIs ########################

class DashboardStats(generics.ListAPIView):
    serializer_class = serializers.AuthorStats
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = gomini.User.objects.get(id=user_id)

        views = gomini.Post.objects.filter(user=user).aggregate(view=Sum("view"))['view']
        posts = gomini.Post.objects.filter(user=user).count()
        likes = gomini.Post.objects.filter(user=user).aggregate(total_likes=Sum("likes"))['total_likes']
        bookmarks = gomini.Bookmark.objects.all().count()

        return [{
            "views": views,
            "posts": posts,
            "likes": likes,
            "bookmarks": bookmarks,
        }]
    
    def list(self, request, *args, **kwargs):
        querset = self.get_queryset()
        serializer = self.get_serializer(querset, many=True)
        return Response(serializer.data)

class DashboardPostLists(generics.ListAPIView):
    serializer_class = serializers.PostSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = gomini.User.objects.get(id=user_id)
        return gomini.Post.objects.filter(user=user).order_by("-id")

class DashboardCommentLists(generics.ListAPIView):
    serializer_class = serializers.CommentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return gomini.Comment.objects.all()

class DashboardNotificationLists(generics.ListAPIView):
    serializer_class = serializers.NotificationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = gomini.User.objects.get(id=user_id)
        return gomini.Notification.objects.filter(seen=False, user=user)

class DashboardMarkNotificationAsSeen(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'noti_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        ),
    )
    def post(self, request):
        noti_id = request.data['noti_id']
        noti = gomini.Notification.objects.get(id=noti_id)

        noti.seen = True
        noti.save()

        return Response({"message": "Noti Marked As Seen"}, status=status.HTTP_200_OK)

class DashboardReplyCommentAPIView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'comment_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'reply': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )
    def post(self, request):
        comment_id = request.data['comment_id']
        reply = request.data['reply']

        print("comment_id =======", comment_id)
        print("reply ===========", reply)

        comment = gomini.Comment.objects.get(id=comment_id)
        comment.reply = reply
        comment.save()

        return Response({"message": "Comment Response Sent"}, status=status.HTTP_201_CREATED)    

class ContactMessageCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.ContactMessageSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'email', 'subject', 'message'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'subject': openapi.Schema(type=openapi.TYPE_STRING),
                'message': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact_message = serializer.save()

        # Create notifications for all authors
        authors = gomini.User.objects.filter(author=True)
        for author in authors:
            gomini.Notification.objects.create(
                user=author,
                post=None,
                type="ContactMessage",
            )

        return Response({"message": "Contact message sent successfully"}, status=status.HTTP_201_CREATED)

class ContactMessageListAPIView(generics.ListAPIView):
    serializer_class = serializers.ContactMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only authors can see contact messages
        user = self.request.user
        if not user.author:
            return gomini.ContactMessage.objects.none()
        return gomini.ContactMessage.objects.all().order_by('-date')

class ContactMessageReplyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['contact_message_id', 'response'],
            properties={
                'contact_message_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'response': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )
    def post(self, request):
        contact_message_id = request.data.get('contact_message_id')
        response_text = request.data.get('response')

        if not contact_message_id or not response_text:
            return Response({"error": "contact_message_id and response are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            contact_message = gomini.ContactMessage.objects.get(id=contact_message_id)
        except gomini.ContactMessage.DoesNotExist:
            return Response({"error": "Contact message not found"}, status=status.HTTP_404_NOT_FOUND)

        contact_message.response = response_text
        contact_message.responded = True
        contact_message.save()

        # Send email to user using the content of the email template file directly
        subject = f"پاسخ به پیام شما: {contact_message.subject}"
        # Render the email template with the context
        context = {
            'full_name': contact_message.name,
            'response_text': response_text,
            'subject': contact_message.subject,
        }
        text_body = render_to_string("email/contact_message.txt", context)
        html_body = render_to_string("email/contact_message.html", context)
        msg = EmailMultiAlternatives(
            subject=subject,
            from_email=f'"ShahreZananeKarafarin" <{settings.EMAIL_HOST_USER}>',
            to=[contact_message.email],
            body=text_body
        )
        msg.attach_alternative(html_body, "text/html")

        try:
            msg.send()
            return Response({"message": "Response sent and email delivered"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DashboardDeleteCommentAPIView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'comment_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=['comment_id']
        ),
    )
    def post(self, request):
        comment_id = request.data.get('comment_id')
        if not comment_id:
            return Response({"error": "comment_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            comment = gomini.Comment.objects.get(id=comment_id)
            # Permission check: only allow if user is author of comment or admin
            user = request.user
            if not user.is_authenticated:
                return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            if comment.name != user.username and not user.is_staff:
                return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
            comment.delete()
            return Response({"message": "Comment deleted successfully"}, status=status.HTTP_200_OK)
        except gomini.Comment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

class DashboardDeleteContactMessageAPIView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'contact_message_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=['contact_message_id']
        ),
    )
    def post(self, request):
        contact_message_id = request.data.get('contact_message_id')
        if not contact_message_id:
            return Response({"error": "contact_message_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            contact_message = gomini.ContactMessage.objects.get(id=contact_message_id)
            # Permission check: only allow if user is staff (authors)
            user = request.user
            if not user.is_authenticated:
                return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            if not user.is_staff:
                return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
            contact_message.delete()
            return Response({"message": "Contact message deleted successfully"}, status=status.HTTP_200_OK)
        except gomini.ContactMessage.DoesNotExist:
            return Response({"error": "Contact message not found"}, status=status.HTTP_404_NOT_FOUND)

class DashboardPostCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.PostSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info(f"Post creation request data: {request.data}")
        user_id = request.data.get('user_id')
        title = request.data.get('title')
        image = request.data.get('image')
        description = request.data.get('description')
        tags = request.data.get('tags')
        category_id = request.data.get('category')
        post_status = request.data.get('post_status')

        logger.info(f"user_id: {user_id}, title: {title}, image: {image}, description: {description}, tags: {tags}, category_id: {category_id}, post_status: {post_status}")

        user = gomini.User.objects.get(id=user_id)
        category = gomini.Category.objects.get(id=category_id)

        post = gomini.Post.objects.create(
            user=user,
            title=title,
            image=image,
            description=description,
            tags=tags,
            category=category,
            status=post_status
        )
        logger.info(f"Post created with slug: {post.slug} and status: {post.status}")

        if post.status == "Active":
            # Send email to all users who opted in to receive updates
            users_to_notify = gomini.User.objects.filter(receive_updates=True).values_list('email', flat=True)
            for email in users_to_notify:
                unsubscribe_url = f"{request.scheme}://{request.get_host()}/api/v1/user/unsubscribe/{urlsafe_base64_encode(force_bytes(gomini.User.objects.get(email=email).pk))}"
                send_post_update_email(post, email, unsubscribe_url=unsubscribe_url)

        return Response({"message": "Post Created Successfully"}, status=status.HTTP_201_CREATED)

class DashboardPostEditAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.PostSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs['user_id']
        post_id = self.kwargs['post_id']
        user = gomini.User.objects.get(id=user_id)
        return gomini.Post.objects.get(user=user, id=post_id)

    def update(self, request, *args, **kwargs):
        post_instance = self.get_object()

        title = request.data.get('title')
        image = request.data.get('image')
        description = request.data.get('description')
        tags = request.data.get('tags')
        category_id = request.data.get('category')
        post_status = request.data.get('post_status')

        if category_id:
            try:
                category = gomini.Category.objects.get(id=category_id)
            except gomini.Category.DoesNotExist:
                return Response({"error": "Invalid category ID"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            category = None

        post_instance.title = title
        if image and image != "undefined":
            post_instance.image = image
        post_instance.description = description
        post_instance.tags = tags
        if category:
            post_instance.category = category
        post_instance.status = post_status
        post_instance.save()

        return Response({"message": "Post Updated Successfully"}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def send_signup_email(request):
    email = request.data.get('email')
    logger = logging.getLogger(__name__)
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = gomini.User.objects.filter(email=email).first()
        if user:
            return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        signup_link = f"{settings.FRONTEND_BASE_URL}/signup?email={email}"
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk)) if user else ''
        merge_data = {
            'signup_link': signup_link,
            'email': email,
            'uidb64': uidb64,
        }
        subject = "تکمیل ثبت نام در سایت"
        text_body = render_to_string("email/signup_email.txt", merge_data)
        html_body = render_to_string("email/signup_email.html", merge_data)
        msg = EmailMultiAlternatives(
            subject=subject,
            from_email=f'"ShahreZananeKarafarin" <{settings.EMAIL_HOST_USER}>',
            to=[email],
            body=text_body
        )
        msg.attach_alternative(html_body, "text/html")

        try:
            msg.send()
            return Response({"message": "Signup email sent successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to send signup email to {email}: {e}")
            return Response({"error": "Failed to send signup email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error in send_signup_email: {e}")
        return Response({"error": "An error occurred while processing signup email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def send_post_update_email(post, email, unsubscribe_url=None):
    logger = logging.getLogger(__name__)
    if not email:
        logger.error("Email is required to send post update email")
        return False

    def extract_first_paragraph(html_content):
        # Use regex to find the first <p>...</p> or first block of text before a <p> or <br> tag
        match = re.search(r'<p.*?>(.*?)</p>', html_content, re.DOTALL)
        if match:
            return match.group(0)  # return the full first paragraph including <p> tags
        else:
            # If no <p> tags, try to split by <br> or newline and return first part
            parts = re.split(r'<br\s*/?>|\n', html_content)
            if parts:
                return parts[0]
            else:
                return html_content

    try:
        post_link = f"{settings.FRONTEND_BASE_URL}/post/{post.slug}"
        uidb64 = urlsafe_base64_encode(force_bytes(gomini.User.objects.get(email=email).pk))
        # Convert Draft.js JSON description to HTML
        if isinstance(post.description, str):
            try:
                post_description_html = draftjs_to_html(post.description)
                # Extract only the first paragraph
                post_description_html = extract_first_paragraph(post_description_html)
            except Exception as e:
                logger.error(f"Failed to convert post description to HTML: {e}")
                post_description_html = ""
        else:
            post_description_html = ""

        merge_data = {
            'post_title': post.title,
            'post_description': post_description_html,
            'post_link': post_link,
            'email': email,
            'uidb64': uidb64,
            'unsubscribe_url': unsubscribe_url,
        }
        subject = f"جدیدترین پست: {post.title}"
        text_body = render_to_string("email/new_post_update_email.txt", merge_data)
        html_body = render_to_string("email/new_post_update_email.html", merge_data)
        
        import os

        msg = EmailMultiAlternatives(
            subject=subject,
            from_email=f'"ShahreZananeKarafarin" <{settings.EMAIL_HOST_USER}>',
            to=[email],
            body=text_body
        )
        msg.attach_alternative(html_body, "text/html")

        try:
            msg.send()
            return True
        except Exception as e:
            logger.error(f"Failed to send post update email to {email}: {e}")
            return False

    except Exception as e:
        logger.error(f"Unexpected error in send_post_update_email: {e}")
        return False

def send_new_post_update_email(request):
    email = request.data.get('email')
    logger = logging.getLogger(__name__)
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        newest_post = gomini.Post.objects.filter(status="Active").order_by('-date').first()
        if not newest_post:
            return Response({"error": "No active posts found"}, status=status.HTTP_404_NOT_FOUND)
        success = send_post_update_email(newest_post, email)
        if success:
            return Response({"message": "New post update email sent successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to send new post update email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Failed to send new post update email to {email}: {e}")
        return Response({"error": "Failed to send new post update email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

{
    "title": "New post",
    "image": "",
    "description": "lorem",
    "tags": "tags, here",
    "category_id": 1,
    "post_status": "Active"
}