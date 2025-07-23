from django.db import models
from django.contrib.auth.models import AbstractUser
from slugify import slugify
from django.db.models import SlugField
from django.core.validators import RegexValidator
import re
from django.db.models import JSONField
from shortuuid.django_fields import ShortUUIDField
import shortuuid

class UnicodeSlugField(SlugField):
    default_validators = [
        RegexValidator(
            re.compile(r'^[-\w\u0600-\u06FF]+$', re.UNICODE),
            'Enter a valid “slug” consisting of letters, numbers, underscores, hyphens, or Persian characters.',
            'invalid'
        ),
    ]

# Create your models here.
class User(AbstractUser):
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    image = models.FileField(upload_to="image", default="default/default-user.jpg", null=True, blank=True)
    bio = models.CharField(max_length=100, null=True, blank=True)
    about = models.CharField(max_length=100, null=True, blank=True)
    author = models.BooleanField(default=False)
    receive_updates = models.BooleanField(default=False)  # New field added to track user preference for updates
    date = models.DateTimeField(auto_now_add=True)
    otp = models.CharField(max_length=10, blank=True, null=True)
    reset_token = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username
    

    def save(self, *args, **kwargs):
        email_username, mobile = self.email.split("@")
        if (self.full_name == "" or self.full_name == None) and (self.first_name or self.last_name):
            self.full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
            # Do not clear first_name and last_name, keep them as is
        elif self.full_name == "" or self.full_name == None:
            self.full_name = email_username
        else:
            # If full_name is set but first_name or last_name are empty, split full_name
            if (self.first_name == "" or self.first_name is None) or (self.last_name == "" or self.last_name is None):
                parts = self.full_name.split()
                if len(parts) == 1:
                    self.first_name = parts[0]
                    self.last_name = ""
                elif len(parts) >= 2:
                    self.first_name = parts[0]
                    self.last_name = " ".join(parts[1:])
        if self.username == "" or self.username == None:
            self.username = email_username  
    
        super(User, self).save(*args, **kwargs)

class Category(models.Model):
    title = models.CharField(max_length=100)
    image = models.FileField(upload_to="image", null=True, blank=True)
    slug = models.SlugField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "Category"

    def save(self, *args, **kwargs):
        if self.slug == "" or self.slug == None:
            self.slug = slugify(self.title)
        super(Category, self).save(*args, **kwargs)
    
    def post_count(self):
        return Post.objects.filter(category=self).count()

class Post(models.Model):
    STATUS = ( 
        ("Active", "Active"), 
        ("Draft", "Draft"),
        ("Disabled", "Disabled"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    image = models.FileField(upload_to="image", null=True, blank=True)
    description = JSONField(null=True, blank=True)
    tags = models.CharField(max_length=100, default="")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    status = models.CharField(max_length=100, choices=STATUS, default="Active")
    view = models.IntegerField(default=0)
    likes = models.ManyToManyField(User, blank=True, related_name="likes_user")
    slug = models.SlugField(max_length=250, unique=True, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "Post"

    def save(self, *args, **kwargs):
        # Normalize slug to be URL-safe and lowercase
        if self.slug == "" or self.slug == None:
            base_slug = slugify(self.title)
            # Ensure base_slug is not empty
            if not base_slug:
                base_slug = "post"
            self.slug = base_slug + "-" + shortuuid.uuid()[:2]
        else:
            # Normalize existing slug
            self.slug = slugify(self.slug)
        # Validate description field to be JSON; if not, convert plain text to JSON with draft.js raw format
        import json
        if self.description is not None and not isinstance(self.description, dict):
            try:
                json.loads(self.description)
            except Exception:
                plain_text_raw = {
                    "blocks": [
                        {
                            "key": "plain",
                            "text": self.description or "",
                            "type": "unstyled",
                            "depth": 0,
                            "inlineStyleRanges": [],
                            "entityRanges": [],
                            "data": {}
                        }
                    ],
                    "entityMap": {}
                }
                self.description = plain_text_raw
        super(Post, self).save(*args, **kwargs)
    
    def comments(self):
        return Comment.objects.filter(post=self).order_by("-id")

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    comment = models.TextField(default="")
    reply = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.post.title} - {self.name}"
    
    class Meta:
        verbose_name_plural = "Comment"

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.post.title} - {self.user.username if self.user else 'Unknown'}"
    
    class Meta:
        verbose_name_plural = "Bookmark"

class Notification(models.Model):
    NOTI_TYPE = ( ("Like", "Like"), ("Comment", "Comment"), ("Bookmark", "Bookmark"), ("ContactMessage", "ContactMessage"))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=100, choices=NOTI_TYPE)
    seen = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Notification"
    
    def __str__(self):
        if self.post:
            return f"{self.type} - {self.post.title}"
        else:
            return "Notification"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    responded = models.BooleanField(default=False)
    response = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"ContactMessage from {self.name} - {self.subject}"
