from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Item, ClaimRequest, Conversation, Message

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin interface for custom user model"""
    list_display = ('username', 'email', 'full_name', 'college', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'full_name', 'college')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'full_name', 'phone', 'college', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'full_name', 'phone', 'college'),
        }),
    )

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Admin interface for items"""
    list_display = ('title', 'item_type', 'category', 'location', 'owner', 'created_at', 'is_verified')
    list_filter = ('item_type', 'category', 'is_verified', 'created_at')
    search_fields = ('title', 'description', 'location', 'owner__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'item_type', 'category', 'location', 'date_lost_found')
        }),
        ('Media & Contact', {
            'fields': ('image', 'contact_info')
        }),
        ('Owner & Status', {
            'fields': ('owner', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(ClaimRequest)
class ClaimRequestAdmin(admin.ModelAdmin):
    """Admin interface for claim requests"""
    list_display = ('claimant_name', 'item', 'status', 'created_at', 'verified_by')
    list_filter = ('status', 'created_at', 'verified_at')
    search_fields = ('claimant_name', 'claimant_email', 'item__title')
    readonly_fields = ('created_at', 'verified_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Claimant Information', {
            'fields': ('claimant_name', 'claimant_email', 'claimant_phone', 'additional_details')
        }),
        ('Item & Verification', {
            'fields': ('item', 'verification_photos', 'status', 'verified_by', 'verified_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('item', 'claimant_name', 'claimant_email')
        return self.readonly_fields


class MessageInline(admin.TabularInline):
    """Inline for messages within a conversation"""
    model = Message
    extra = 0
    readonly_fields = ('sender', 'text', 'created_at')
    can_delete = True
    ordering = ('created_at',)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin interface for conversations"""
    list_display = ('id', 'item_title', 'participants_list', 'message_count', 'created_at')
    list_filter = ('created_at', 'item__item_type')
    search_fields = ('item__title', 'participants__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    filter_horizontal = ('participants',)
    inlines = [MessageInline]
    
    def item_title(self, obj):
        return obj.item.title if obj.item else '-' 
    item_title.short_description = 'Item'
    
    def participants_list(self, obj):
        return ', '.join([p.username for p in obj.participants.all()])
    participants_list.short_description = 'Participants'
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
    
    fieldsets = (
        ('Conversation Info', {
            'fields': ('item', 'participants')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for messages"""
    list_display = ('id', 'conversation_item', 'message_item', 'sender', 'text_preview', 'created_at')
    list_filter = ('created_at', 'sender')
    search_fields = ('text', 'sender__username', 'conversation__item__title')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def conversation_item(self, obj):
        return f"{obj.conversation.item.title} (#{obj.conversation.id})"
    conversation_item.short_description = 'Conversation'
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Message Preview'
    
    fieldsets = (
        ('Message Info', {
'fields': ('conversation', 'sender', 'text', 'message_item')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
