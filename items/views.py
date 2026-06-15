from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Q, Max
from django.urls import reverse
from .models import Item, ClaimRequest, CustomUser, Conversation, Message, ConversationRead
import json
import os


def welcome(request):
    """Welcome page with login/register options"""
    # Check if user is authenticated
    if request.user.is_authenticated:
        return redirect('items:dashboard')
    return render(request, "items/welcome.html")

def user_register(request):
    """User registration page with database storage"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        college = request.POST.get('college')
        
        # Validation
        if not all([username, email, password, password_confirm, full_name, phone, college]):
            messages.error(request, "Please fill all fields.")
            return render(request, "items/register.html")
        
        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, "items/register.html")
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "items/register.html")
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, "items/register.html")
        
        # Create user
        try:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                phone=phone,
                college=college
            )
            messages.success(request, f"Account created successfully! Welcome {full_name}!")
            login(request, user)
            return redirect('items:dashboard')
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
    
    return render(request, "items/register.html")

def user_login(request):
    """User login page with database authentication"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.full_name or user.username}!")
                return redirect('items:dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please enter both username and password.")
    
    return render(request, "items/login.html")

def user_logout(request):
    """Logout user and redirect to welcome"""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, f"Goodbye, {username}!")
    return redirect('items:welcome')







def home(request):
    """Redirect to welcome page"""
    return redirect('items:welcome')

# Database-backed views for items
@login_required
def dashboard_db(request):
    """Dashboard with lost/found items from database"""
    # Exclude hidden items; show recent entries
    lost_items = Item.objects.filter(item_type='Lost', is_hidden_from_dashboard=False).order_by('-created_at')[:3]
    found_items = Item.objects.filter(item_type='Found', is_hidden_from_dashboard=False).order_by('-created_at')[:3]
    
    # Pending claims for items owned by the current user
    pending_claims = ClaimRequest.objects.filter(item__owner=request.user, status='pending').count()
    
    context = {
        'lost_items': lost_items,
        'found_items': found_items,
        'pending_claims': pending_claims,
    }
    return render(request, "items/dashboard.html", context)

@login_required
def chats_home(request):
    """Chats landing page: show sidebar; do not auto-open a conversation.
    The user must click a conversation to view it.
    """
    qs = (Conversation.objects
          .filter(participants=request.user)
          .annotate(last_msg_at=Max('messages__created_at'))
          .prefetch_related('participants', 'messages__sender')
          .order_by('-last_msg_at', '-created_at'))
    # Unique per other participant
    conversations = []
    seen = set()
    for c in qs:
        other = c.participants.exclude(id=request.user.id).first()
        if other and other.id not in seen:
            conversations.append(c)
            seen.add(other.id)
    # Build unread map for sidebar
    unread_map = {}
    for c in conversations:
        read = ConversationRead.objects.filter(conversation=c, user=request.user).first()
        if read:
            unread_count = c.messages.filter(created_at__gt=read.last_read_at).exclude(sender=request.user).count()
        else:
            unread_count = c.messages.exclude(sender=request.user).count()
        unread_map[c.id] = unread_count
        setattr(c, 'unread_count', unread_count)

    # Render chat page with empty thread and sidebar only
    return render(request, 'items/chat.html', {
        'conversation': None,
        'messages': [],
        'owner_user': None,
        'other_user': None,
        'other_conversations': [],
        'sidebar_conversations': conversations,
        'unread_map': unread_map,
        'active_conversation_id': None,
        'allow_end': False,
        'claim_status': None,
        'my_items_lost': Item.objects.filter(owner=request.user, item_type='Lost').order_by('-created_at'),
        'my_items_found': Item.objects.filter(owner=request.user, item_type='Found').order_by('-created_at'),
        'their_items_lost': Item.objects.none(),
        'their_items_found': Item.objects.none(),
    })



def lost_items_db(request):
    """View all lost items from database"""
    items = Item.objects.filter(item_type='Lost', is_hidden_from_dashboard=False).order_by('-created_at')
    return render(request, "items/lost_items.html", {"items": items})

def found_items_db(request):
    """View all found items from database"""
    items = Item.objects.filter(item_type='Found', is_hidden_from_dashboard=False).order_by('-created_at')
    return render(request, "items/found_items.html", {"items": items})

def item_detail_db(request, item_id):
    """Detail page for a single item from database"""
    item = get_object_or_404(Item, id=item_id)
    
    # Find matching items of opposite type, exclude hidden items
    if item.item_type == 'Lost':
        matching_items = Item.objects.filter(
            item_type='Found',
            category=item.category,
            is_hidden_from_dashboard=False
        ).exclude(id=item_id)[:5]
    else:
        matching_items = Item.objects.filter(
            item_type='Lost',
            category=item.category,
            is_hidden_from_dashboard=False
        ).exclude(id=item_id)[:5]
    
    # Get pending claim requests for this item
    claim_requests = ClaimRequest.objects.filter(item=item, status='pending')
    
    context = {
        "item": item,
        "matching_items": matching_items,
        "claim_requests": claim_requests,
    }
    return render(request, "items/item.html", context)

@login_required
def claim_item(request, item_id):
    """Allow users to claim an item by uploading verification photos"""
    item = get_object_or_404(Item, id=item_id)
    
    # Only claims for Found items, and owner cannot claim their own item
    if item.item_type != 'Found':
        messages.error(request, 'Only Found items can be claimed.')
        return redirect('items:detail', item_id=item_id)
    if request.user == item.owner:
        messages.error(request, 'You cannot claim an item you posted.')
        return redirect('items:detail', item_id=item_id)
    
    if request.method == 'POST':
        claimant_name = request.POST.get('claimant_name')
        claimant_email = request.POST.get('claimant_email')
        claimant_phone = request.POST.get('claimant_phone', '')
        additional_details = request.POST.get('additional_details', '')
        
        # Handle photo uploads
        verification_photos = []
        for key, file in request.FILES.items():
            if key.startswith('photo_'):
                # Save uploaded file
                file_path = default_storage.save(f'verification_photos/{file.name}', ContentFile(file.read()))
                verification_photos.append(file_path)
        
        if claimant_name and claimant_email and verification_photos:
            # Create claim request
            claim_request = ClaimRequest.objects.create(
                item=item,
                claimant_name=claimant_name,
                claimant_email=claimant_email,
                claimant_phone=claimant_phone,
                verification_photos=verification_photos,
                additional_details=additional_details
            )

            # Ensure a conversation exists between claimant and owner for this item
            convo = Conversation.objects.filter(item=item, participants=request.user).filter(participants=item.owner).first()
            if not convo:
                convo = Conversation.objects.create(item=item)
                convo.participants.add(request.user)
                convo.participants.add(item.owner)

            # Post an initial claim message into the conversation (reference the item)
            verify_url = request.build_absolute_uri(reverse('items:verify_claim', args=[claim_request.id]))
            initial_text = (
                f"New claim for '{item.title}' submitted by @{request.user.username}\n"
                f"Name: {claimant_name}\nEmail: {claimant_email}\nPhone: {claimant_phone or 'N/A'}\n"
                f"Details: {additional_details or 'N/A'}\n"
                f"Review claim: {verify_url}"
            )
            Message.objects.create(conversation=convo, sender=request.user, text=initial_text, message_item=item)

            messages.success(request, f'Claim request submitted successfully! A chat with the owner has been opened for follow-up.')
            return redirect('items:chat_detail', conversation_id=convo.id)
        else:
            messages.error(request, 'Please provide all required information and at least one verification photo.')
    
    return render(request, "items/claim_item.html", {"item": item})

@login_required
def verify_claim(request, claim_id):
    """Allow item owner to verify or reject a claim request"""
    claim = get_object_or_404(ClaimRequest, id=claim_id)
    
    # Check if current user owns the item
    if claim.item.owner != request.user:
        messages.error(request, 'You can only verify claims for your own items.')
        return redirect('items:dashboard')

    # Try to locate the claimant user account via email
    claimant_user = CustomUser.objects.filter(email=claim.claimant_email).first()
    claim_chat_url = None
    if claimant_user:
        # Find existing conversation between owner and claimant for this item
        existing = Conversation.objects.filter(item=claim.item, participants=request.user).filter(participants=claimant_user).first()
        if existing:
            claim_chat_url = reverse('items:chat_detail', args=[existing.id])

    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'verify':
            claim.status = 'verified'
            claim.verified_at = timezone.now()
            claim.verified_by = request.user
            claim.save()
            
            # Mark the item as found and hidden from dashboard when claim is accepted
            item = claim.item
            item.is_found = True
            item.is_hidden_from_dashboard = True
            item.is_claimed = True
            item.save()
            
            messages.success(request, f'Claim verified and item marked as found! You can now contact {claim.claimant_name} at {claim.claimant_email}.')
            return redirect('items:dashboard')
        elif action == 'reject':
            claim.status = 'rejected'
            claim.verified_by = request.user
            claim.save()
            messages.info(request, 'Claim rejected.')
            return redirect('items:detail', item_id=claim.item.id)
        
        # This line will only be reached if action is neither verify nor reject
        return redirect('items:dashboard')
    
    return render(request, "items/verify_claim.html", {"claim": claim, "claim_chat_url": claim_chat_url})

@login_required
def post_item_db(request):
    """Post a lost or found item to database"""
    if request.method == 'POST':
        item_type = request.POST.get('type')
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        location = request.POST.get('location')
        date = request.POST.get('date')
        
        # Handle image upload
        image = None
        if 'image' in request.FILES:
            uploaded_file = request.FILES['image']
            file_path = default_storage.save(f'item_images/{uploaded_file.name}', ContentFile(uploaded_file.read()))
            image = f'/media/{file_path}'
        else:
            image = request.POST.get('image_url', '')
        
        # Use registered user's contact information automatically
        contact = request.user.email or f"{request.user.username}@findit.com"
        
        if all([title, description, category, location, date]):
            # Normalize type
            item_type = 'Found' if item_type == 'Found' else 'Lost'
            
            item = Item.objects.create(
                title=title,
                description=description,
                item_type=item_type,
                category=category,
                location=location,
                date_lost_found=date,
                image=image,
                contact_info=contact,
                owner=request.user
            )
            messages.success(request, f'{item_type} item posted successfully!')
            return redirect('items:profile')
        else:
            messages.error(request, "Please fill all required fields.")
    
    return render(request, "items/post.html")

@login_required
def profile_db(request):
    """User profile page with lost/found items from database"""
    lost_items = Item.objects.filter(owner=request.user, item_type='Lost').order_by('-created_at')
    found_items = Item.objects.filter(owner=request.user, item_type='Found').order_by('-created_at')
    
    # Claims submitted by the current user
    user_claims = ClaimRequest.objects.filter(claimant_email=request.user.email).order_by('-created_at')

    # Incoming claims for items owned by the current user
    incoming_claims = ClaimRequest.objects.filter(item__owner=request.user).select_related('item').order_by('-created_at')
    
    # Calculate resolved items count
    resolved_count = Item.objects.filter(owner=request.user, is_found=True).count()

    # Items you've posted that are claimed/resolved (read-only section)
    claimed_items = Item.objects.filter(owner=request.user, is_claimed=True).order_by('-created_at')
    resolved_items = Item.objects.filter(owner=request.user, is_found=True).order_by('-created_at')
    
    return render(request, "items/profile.html", {
        "user": request.user,
        "lost_items": lost_items,
        "found_items": found_items,
        "user_claims": user_claims,
        "incoming_claims": incoming_claims,
        "claimed_items": claimed_items,
        "resolved_items": resolved_items,
        "resolved_count": resolved_count,
    })

@login_required
def delete_item_db(request, item_id):
    """Delete an item from database"""
    item = get_object_or_404(Item, id=item_id)
    
    # Check if user owns the item or is admin
    if item.owner != request.user and not request.user.is_staff:
        messages.error(request, 'You can only delete your own posts.')
        return redirect('items:detail', item_id=item_id)
    
    item.delete()
    messages.success(request, f'Item "{item.title}" has been deleted successfully!')
    return redirect('items:profile')


@login_required
def edit_item_db(request, item_id):
    """Edit an existing item (owner or admin only)."""
    item = get_object_or_404(Item, id=item_id)

    # Only the owner or admin can edit
    if item.owner != request.user and not request.user.is_staff:
        messages.error(request, 'You can only edit your own posts.')
        return redirect('items:detail', item_id=item_id)

    if request.method == 'POST':
        item_type = request.POST.get('type', item.item_type)
        title = request.POST.get('title', item.title)
        description = request.POST.get('description', item.description)
        category = request.POST.get('category', item.category)
        location = request.POST.get('location', item.location)
        date = request.POST.get('date', item.date_lost_found)

        # Handle image upload (optional)
        if 'image' in request.FILES and request.FILES['image']:
            uploaded_file = request.FILES['image']
            file_path = default_storage.save(f'item_images/{uploaded_file.name}', ContentFile(uploaded_file.read()))
            item.image = f'/media/{file_path}'

        if all([title, description, category, location, date]):
            item.item_type = 'Found' if item_type == 'Found' else 'Lost'
            item.title = title
            item.description = description
            item.category = category
            item.location = location
            item.date_lost_found = date
            item.save()
            messages.success(request, 'Item updated successfully!')
            return redirect('items:detail', item_id=item.id)
        else:
            messages.error(request, 'Please fill all required fields.')

    return render(request, 'items/edit_item.html', { 'item': item })


@login_required
def start_claim_chat(request, claim_id):
    """Start or resume chat between item owner and claimant (single per pair)."""
    claim = get_object_or_404(ClaimRequest, id=claim_id)
    item = claim.item

    # Determine users involved
    claimant_user = CustomUser.objects.filter(email=claim.claimant_email).first()
    owner_user = item.owner

    # Only participants may initiate: owner or claimant
    if request.user not in [owner_user, claimant_user]:
        messages.error(request, 'You are not allowed to access this chat.')
        return redirect('items:dashboard')

    # Ensure conversation exists for this pair (ignore item)
    if not claimant_user:
        messages.error(request, 'Claimant user account not found.')
        return redirect('items:verify_claim', claim_id=claim.id)

    convo = Conversation.objects.filter(participants=owner_user).filter(participants=claimant_user).order_by('-created_at').first()
    if not convo:
        convo = Conversation.objects.create(item=None)
        convo.participants.add(owner_user)
        convo.participants.add(claimant_user)

    return redirect('items:chat_detail', conversation_id=convo.id)


@login_required
def start_chat(request, item_id):
    """Start (or resume) a chat between the current user and the item's owner (single per pair)."""
    item = get_object_or_404(Item, id=item_id)

    # Prevent chatting with self just in case
    if item.owner == request.user:
        messages.info(request, 'This is your item. You can manage it from your profile.')
        return redirect('items:detail', item_id=item_id)

    # Find existing conversation between these two users (any item)
    existing = Conversation.objects.filter(participants=request.user).filter(participants=item.owner).order_by('-created_at').first()
    if existing:
        return redirect('items:chat_detail', conversation_id=existing.id)

    # Create a new conversation for this pair; item optional
    convo = Conversation.objects.create(item=None)
    convo.participants.add(request.user)
    convo.participants.add(item.owner)

    return redirect('items:chat_detail', conversation_id=convo.id)


@login_required
def chat_detail(request, conversation_id):
    """View to display messages and send new messages in a conversation."""
    convo = get_object_or_404(Conversation, id=conversation_id)

    # Only participants can view/send messages
    if not convo.participants.filter(id=request.user.id).exists():
        messages.error(request, 'You are not a participant in this conversation.')
        return redirect('items:dashboard')

    # Determine other participant for display/grouping
    other_user = convo.participants.exclude(id=request.user.id).first()
    owner_user = convo.item.owner if getattr(convo, 'item', None) else None

    # Determine if this convo is tied to a claim and whether it is resolved
    claim_for_convo = None
    allow_end = True
    claim_status = None
    if other_user is not None:
        if getattr(convo, 'item', None) is not None:
            claim_for_convo = ClaimRequest.objects.filter(item=convo.item, claimant_email=other_user.email).order_by('-created_at').first()
        else:
            # Try infer from latest tagged message, if any
            last_tagged = convo.messages.filter(message_item__isnull=False).order_by('-created_at').first()
            if last_tagged is not None:
                claim_for_convo = ClaimRequest.objects.filter(item=last_tagged.message_item, claimant_email=other_user.email).order_by('-created_at').first()
        if claim_for_convo:
            claim_status = claim_for_convo.status
            allow_end = claim_status in ['verified', 'rejected', 'completed']
        else:
            allow_end = True  # Non-claim chat can be ended anytime

    # Fetch all other conversations between the same two users (regardless of item)
    other_conversations = (Conversation.objects
                           .filter(participants__id=request.user.id)
                           .filter(participants__id=other_user.id)
                           .exclude(id=convo.id)
                           .annotate(last_msg_at=Max('messages__created_at'))
                           .prefetch_related('item')
                           .order_by('-last_msg_at', '-created_at'))

    # Sidebar conversation list for this user (unique per counterpart)
    sidebar_qs = (Conversation.objects
                  .filter(participants=request.user)
                  .annotate(last_msg_at=Max('messages__created_at'))
                  .prefetch_related('participants', 'messages__sender')
                  .order_by('-last_msg_at', '-created_at'))
    sidebar_conversations = []
    unread_map = {}
    seen_ids = set()
    for c in sidebar_qs:
        otherp = c.participants.exclude(id=request.user.id).first()
        if otherp and otherp.id not in seen_ids:
            sidebar_conversations.append(c)
            seen_ids.add(otherp.id)
            # unread count: messages newer than last_read_at and not sent by me
            read = ConversationRead.objects.filter(conversation=c, user=request.user).first()
            if read:
                unread_count = c.messages.filter(created_at__gt=read.last_read_at).exclude(sender=request.user).count()
            else:
                unread_count = c.messages.exclude(sender=request.user).count()
            unread_map[c.id] = unread_count
            setattr(c, 'unread_count', unread_count)

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        item_id_str = request.POST.get('message_item_id')
        selected_item = None
        if item_id_str:
            try:
                # Only allow tagging items owned by either participant
                selected_item = Item.objects.filter(id=int(item_id_str), owner__in=[request.user, other_user]).first()
            except Exception:
                selected_item = None
        if text:
            Message.objects.create(conversation=convo, sender=request.user, text=text, message_item=selected_item)
            return redirect('items:chat_detail', conversation_id=conversation_id)
        else:
            messages.error(request, 'Message cannot be empty.')

    messages_qs = convo.messages.select_related('sender', 'message_item').all()

    # Mark conversation as read for current user
    cr, _ = ConversationRead.objects.get_or_create(conversation=convo, user=request.user)
    cr.last_read_at = timezone.now()
    cr.save()

    # Item options to tag messages: only Lost/Found belonging to participants, grouped by owner and type
    my_items_lost = Item.objects.filter(owner=request.user, item_type='Lost').order_by('-created_at')
    my_items_found = Item.objects.filter(owner=request.user, item_type='Found').order_by('-created_at')
    their_items_lost = Item.objects.none()
    their_items_found = Item.objects.none()
    if other_user is not None:
        their_items_lost = Item.objects.filter(owner=other_user, item_type='Lost').order_by('-created_at')
        their_items_found = Item.objects.filter(owner=other_user, item_type='Found').order_by('-created_at')

    return render(request, 'items/chat.html', {
        'conversation': convo,
        'messages': messages_qs,
        'owner_user': owner_user,
        'other_user': other_user,
        'other_conversations': other_conversations,
        'sidebar_conversations': sidebar_conversations,
        'allow_end': allow_end,
        'claim_status': claim_status,
        'my_items_lost': my_items_lost,
        'my_items_found': my_items_found,
        'their_items_lost': their_items_lost,
        'their_items_found': their_items_found,
        'unread_map': unread_map,
        'active_conversation_id': convo.id if 'convo' in locals() else None,
    })


@login_required
def end_chat(request, conversation_id):
    """End chat for the current user. For claim chats, only after verify/reject/complete."""
    convo = get_object_or_404(Conversation, id=conversation_id)
    if not convo.participants.filter(id=request.user.id).exists():
        messages.error(request, 'You are not a participant in this conversation.')
        return redirect('items:dashboard')

    # Check claim resolution if applicable
    other_user = convo.participants.exclude(id=request.user.id).first()
    allow_end = True
    if other_user is not None:
        claim_for_convo = ClaimRequest.objects.filter(item=convo.item, claimant_email=other_user.email).order_by('-created_at').first()
        if claim_for_convo and claim_for_convo.status not in ['verified', 'rejected', 'completed']:
            allow_end = False
    
    if not allow_end:
        messages.error(request, 'You can end this chat after the claim is verified or rejected.')
        return redirect('items:chat_detail', conversation_id=conversation_id)

    # Remove current user from participants to "end" chat for them
    convo.participants.remove(request.user)

    # If no participants remain, delete the conversation
    if convo.participants.count() == 0:
        convo.delete()
        messages.success(request, 'Chat ended and conversation removed.')
        return redirect('items:chat_list')

    messages.success(request, 'Chat ended. You will no longer see this conversation.')
    return redirect('items:chat_list')
