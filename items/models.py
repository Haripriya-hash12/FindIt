from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    """Extended User model with additional profile fields"""
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    
    full_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    college = models.CharField(max_length=200, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class Item(models.Model):
    TYPE_CHOICES = [
        ('Lost', 'Lost'),
        ('Found', 'Found'),
    ]
    
    CATEGORY_CHOICES = [
        ('Electronics', 'Electronics'),
        ('Accessories', 'Accessories'),
        ('Keys', 'Keys'),
        ('Bags', 'Bags'),
        ('Books', 'Books'),
        ('Clothing', 'Clothing'),
        ('Jewelry', 'Jewelry'),
        ('Documents', 'Documents'),
        ('Other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    item_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    location = models.CharField(max_length=200)
    date_lost_found = models.DateField()
    image = models.URLField(blank=True, null=True)
    contact_info = models.CharField(max_length=200)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='owned_items')
    is_verified = models.BooleanField(default=False)
    is_claimed = models.BooleanField(default=False)
    is_hidden_from_dashboard = models.BooleanField(default=False)
    is_found = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.item_type}: {self.title}"
    
    class Meta:
        ordering = ['-created_at']

class ClaimRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='claim_requests')
    claimant_name = models.CharField(max_length=100)
    claimant_email = models.CharField(max_length=200)
    claimant_phone = models.CharField(max_length=20, blank=True)
    verification_photos = models.JSONField(default=list)  # List of photo URLs
    additional_details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_claims')
    
    def __str__(self):
        return f"Claim for {self.item.title} by {self.claimant_name}"
    
    class Meta:
        ordering = ['-created_at']


class Conversation(models.Model):
    """A conversation between two users. Item is optional; messages can reference items."""
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='conversations', null=True, blank=True)
    participants = models.ManyToManyField(CustomUser, related_name='conversations')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        users = ', '.join([u.username for u in self.participants.all()[:2]])
        return f"Conversation between {users}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField()
    message_item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, related_name='message_refs')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.text[:30]}..."


class ConversationRead(models.Model):
    """Tracks a user's last read timestamp for a conversation to compute unread counts."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='reads')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='conversation_reads')
    last_read_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('conversation', 'user')

    def __str__(self):
        return f"Read {self.conversation_id} by {self.user.username} at {self.last_read_at}"
