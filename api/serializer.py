from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from rest_framework import serializers
from api import models as gomini

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username
        try:
            token['vendor_id'] = user.vendor.id
        except:
            token['vendor_id'] = 0
        token['is_staff'] = user.is_staff
        token['can_delete_comment'] = getattr(user, 'can_delete_comment', False)
        return token

    def validate(self, attrs):
        username_or_email = attrs.get("username") or attrs.get("email")
        password = attrs.get("password")

        if not username_or_email:
            raise serializers.ValidationError("Please provide username or email.")

        user_obj = None

        # Try to find user by username
        try:
            user_obj = gomini.User.objects.get(username=username_or_email)
        except gomini.User.DoesNotExist:
            # Try to find user by email
            try:
                user_obj = gomini.User.objects.get(email=username_or_email)
            except gomini.User.DoesNotExist:
                pass

        if user_obj:
            attrs["username"] = user_obj.username
        else:
            raise serializers.ValidationError("No active account found with the given credentials")

        return super().validate(attrs)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = gomini.User
        fields = ('username', 'password', 'password2', 'email', 'full_name', 'first_name', 'last_name', 'bio', 'about', 'image', 'receive_updates')
        extra_kwargs = {
            'email': {'required': True},
            'full_name': {'required': True}
        }
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "پسووردها باهم تطابق ندارند."})

        password = attrs['password']
        if len(password) < 8:
            raise serializers.ValidationError({"password": "پسوورد باید حداقل 8 حرف داشته باشد."})
        if not any(char.isdigit() for char in password):
            raise serializers.ValidationError({"password": "پسوورد باید حداقل شامل یک عدد باشد."})
        if not any(char.isupper() for char in password):
            raise serializers.ValidationError({"password": "پسوورد باید شامل یک حرف بزرگ باشد."})
        if not any(char in '@#$%^&+=!' for char in password):
            raise serializers.ValidationError({"password": "پسوورد باید شامل یک حروف پیچیده باشد"})
        
        return attrs
       
    def create(self, validated_data):
        image = validated_data.pop('image', None)
        receive_updates = validated_data.pop('receive_updates', False)
        user = gomini.User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            bio=validated_data.get('bio', ''),
            about=validated_data.get('about', ''),
            receive_updates=receive_updates,
        )
        if image:
            user.image = image
        email_username, mobile = user.email.split("@")
        user.username = email_username
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = gomini.User
        fields = '__all__'
        extra_kwargs = {
            'otp': {'write_only': True, 'required': False},
            'reset_token': {'write_only': True, 'required': False},
        }

class UserProfileSerializer(serializers.ModelSerializer):
    bio = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    about = serializers.CharField(allow_blank=True, allow_null=True, required=False)

    class Meta:
        model = gomini.User
        fields = '__all__'
        extra_kwargs = {
            'otp': {'write_only': True, 'required': False},
            'reset_token': {'write_only': True, 'required': False},
        }

    def update(self, instance, validated_data):
        bio = validated_data.get('bio')
        about = validated_data.get('about')

        instance = super().update(instance, validated_data)

        if bio is not None:
            instance.bio = bio
        if about is not None:
            instance.about = about
        instance.save()

        return instance

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class CategorySerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    def get_post_count(self, category):
        return category.posts.count()

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            url = obj.image.url
            if request is not None:
                return request.build_absolute_uri(url)
            else:
                return url
        return None
    
    class Meta:
        model = gomini.Category
        fields = [
            "id",
            "title",
            "image",
            "image_url",
            "slug",
            "post_count",
        ]

    def __init__(self, *args, **kwargs):
        super(CategorySerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'POST':
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3

class CommentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = gomini.Comment
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(CommentSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'POST':
            self.Meta.depth = 0
        else:
            self.Meta.depth = 1

class PostSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = gomini.Post
        fields = "__all__"

    def get_comments(self, obj):
        comments = obj.comments().all()
        serializer = CommentSerializer(comments, many=True)
        return serializer.data

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            url = obj.image.url
            if request is not None:
                return request.build_absolute_uri(url)
            else:
                return url
        return None

    def __init__(self, *args, **kwargs):
        super(PostSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'POST':
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3

class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = gomini.Bookmark
        fields = "__all__"


    def __init__(self, *args, **kwargs):
        super(BookmarkSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'POST':
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3

class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = gomini.Notification
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(NotificationSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'POST':
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = gomini.ContactMessage
        fields = "__all__"

class AuthorStats(serializers.Serializer):
    views = serializers.IntegerField(default=0)
    posts = serializers.IntegerField(default=0)
    likes = serializers.IntegerField(default=0)
    bookmarks = serializers.IntegerField(default=0)
