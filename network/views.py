import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError, models
from django.http import JsonResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404 
from django.urls import reverse
from django.core.paginator import Paginator
from django.core import serializers

from .models import User, Post, Follow
from .forms import NewPostForm
from django.forms.models import model_to_dict
from django.db.models import Count, Case, When, BooleanField, F, Subquery, OuterRef


def paginated_post(page_number, user=None, page_type='Index'):
    #if we're looking on the follow page
    if page_type == 'Following':
        # extract the people that the current user is following - using __ to traverse the user foreign key, to retrieve the id
        following = Follow.objects.filter(user=user).values_list('user_to_follow__id', flat=True)
        # do a query for all posts, filtering for posts by the user id (traverse the foreign key again)
        all_posts = Post.objects.filter(user__id__in=following).annotate(num_likes=Count('likes')).annotate(
        user_liked=models.Exists(
        user.liked.filter(id=OuterRef('pk')).values('id')
        ),
        username=F('user__username'),
        userid=F('user__id'),
        is_owner=Case(
            When(user_id=user.id, then=True),
            default=False,
            output_field=BooleanField()
        )
        ).values('id', 'post', 'username', 'timestamp', 'num_likes', 'user_liked', 'userid', 'edited', 'is_owner').order_by("-timestamp")
    #else if we're looking at a profile page
    elif page_type == 'Profile':
        # do a query for all posts, filtering for posts by the user id (traverse the foreign key again)
        all_posts = Post.objects.filter(user=user).annotate(num_likes=Count('likes')).annotate(
        user_liked=models.Exists(
        user.liked.filter(id=OuterRef('pk')).values('id')
        ),
        username=F('user__username'),
        userid=F('user__id'),
        is_owner=Case(
            When(user_id=user.id, then=True),
            default=False,
            output_field=BooleanField()
        )
        ).values('id', 'post', 'username', 'timestamp', 'num_likes', 'user_liked', 'userid', 'edited', 'is_owner').order_by("-timestamp")
    #else we're looking at the index page
    else:
        # main query for extracting all posts. use annotate + count to work out number of likes per post
        all_posts = Post.objects.annotate(num_likes=Count('likes')).annotate(
        #use subquery to see if user has liked each post - using reverse relation on the user model
        user_liked=models.Exists(
            user.liked.filter(id=OuterRef('pk')).values('id')
        ),
        username=F('user__username'),
        userid=F('user__id'),
        is_owner=Case(
            When(user_id=user.id, then=True),
            default=False,
            output_field=BooleanField()
        )
        ).values('id', 'post', 'username', 'timestamp', 'num_likes', 'user_liked', 'userid', 'edited', 'is_owner').order_by("-timestamp")

    #paginate all_posts and select page requested
    paginator = Paginator(all_posts, 10)
    page_obj = paginator.page(page_number)
    #get list of objects for current page
    posts = page_obj.object_list

    #convert datetime object into readable string
    for post in posts:
        post['timestamp'] = post['timestamp'].strftime('%b %d %Y, %I:%M %p')
    
    #create a dictionary to send as response. converting posts to a list
    data = {
        'posts' : list(posts),
        'prev_page': page_obj.has_previous(),
        'next_page' : page_obj.has_next(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages
    }


    return data    

def guest_paginated_post(page_number, user=None, page_type='Index'):
 #if we're looking on the follow page
    if page_type == 'Following':
        # extract the people that the current user is following - using __ to traverse the user foreign key, to retrieve the id
        following = Follow.objects.filter(user=user).values_list('user_to_follow__id', flat=True)
        # do a query for all posts, filtering for posts by the user id (traverse the foreign key again)
        all_posts = Post.objects.filter(user__id__in=following).annotate(num_likes=Count('likes')).annotate(
        user_liked=models.Exists(
        user.liked.filter(id=OuterRef('pk')).values('id')
        ),
        username=F('user__username'),
        userid=F('user__id'),
        is_owner=Case(
            When(user_id=user.id, then=True),
            default=False,
            output_field=BooleanField()
        )
        ).values('id', 'post', 'username', 'timestamp', 'num_likes', 'user_liked', 'userid', 'edited', 'is_owner').order_by("-timestamp")
    #else if we're looking at a profile page
    elif page_type == 'Profile':
        # do a query for all posts, filtering for posts by the user id (traverse the foreign key again)
        all_posts = Post.objects.filter(user=user).annotate(num_likes=Count('likes')).annotate(
        username=F('user__username'),
        userid=F('user__id'),
        is_owner=Case(
            When(user_id=user.id, then=True),
            default=False,
            output_field=BooleanField()
        )
        ).values('id', 'post', 'username', 'timestamp', 'num_likes', 'userid', 'edited').order_by("-timestamp")
    #else we're looking at the index page
    else:
        # main query for extracting all posts. use annotate + count to work out number of likes per post
        all_posts = Post.objects.annotate(num_likes=Count('likes')).annotate(
        username=F('user__username'),
        userid=F('user__id'),
        ).values('id', 'post', 'username', 'timestamp', 'num_likes', 'userid', 'edited').order_by("-timestamp")

    #paginate all_posts and select page requested
    paginator = Paginator(all_posts, 10)
    page_obj = paginator.page(page_number)
    #get list of objects for current page
    posts = page_obj.object_list

    #convert datetime object into readable string
    for post in posts:
        post['timestamp'] = post['timestamp'].strftime('%b %d %Y, %I:%M %p')
    
    #create a dictionary to send as response. converting posts to a list
    data = {
        'posts' : list(posts),
        'prev_page': page_obj.has_previous(),
        'next_page' : page_obj.has_next(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages
    }


    return data    



def index(request):
    #if theres a logged in user
    if request.user.is_authenticated:
        #extract paginated post for page one - passing in the user to see what posts they liked
        context = paginated_post(1, request.user)
        #pass in form to allow new posts to be made by user
        form = NewPostForm()
        context['form'] = form
    #else use amended pagination function for none users
    else:
        context = guest_paginated_post(1, None) 
    return render(request, "network/index.html", context)

def load_post(request, page, page_type):
    if request.user.is_authenticated:
        #extract paginated post for the requested page - passing in the user to see what posts they liked
        data = paginated_post(page, request.user, page_type)
        data['isloggedin'] = True
    else:
        data = guest_paginated_post(page, None, page_type)
        data['isloggedin'] = False
    return JsonResponse(data, safe=False, status=200)

@login_required
def new_post(request):
    # Composing a new post must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    else:
        #extract users post from request, and put in a NewPostForm
        form = NewPostForm(json.loads(request.body))
        if form.is_valid():
            #Saving commit=False to get a model object, so we can add user it, then save it
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            #get post from database
            post = Post.objects.filter(id=instance.id).annotate(
                num_likes=Count('likes'),
                user_liked=Case(
                    When(likes=request.user, then=True),
                    default=False,
                    output_field=BooleanField(),
                ),
                username=F('user__username'),
                userid=F('user__id')
            ).values('id', 'post', 'timestamp', 'num_likes', 'user_liked', 'username', 'userid', 'edited').first()
            #convert queryset to a dict, so we can serialise it
            if post is not None:
                post_dict = {
                    'id': post['id'],
                    'post': post['post'],
                    'timestamp': post['timestamp'].strftime('%b %d %Y, %I:%M %p'),
                    'num_likes': post['num_likes'],
                    'user_liked': post['user_liked'],
                    'username': post['username'],
                    'userid': post['userid'],
                    'is_owner': True,
                }
                return JsonResponse({"message": "Posted succesfully", 'post': post_dict }, status=201)
        else:
            return JsonResponse({'error': 'Post not found.'}, status=404)

@login_required
def likes(request, post_id, action):
    print('hody')
    user = request.user
    post = Post.objects.get(id=post_id)
    #to dislike post:
    if post.likes.filter(id=user.id).exists():
        post.likes.remove(user)
        post.save()
        data = {'count': post.likes.all().count(), 'user_liked': False}
        return JsonResponse(data, status=200)
    else:
        post.likes.add(user)
        post.save()
        data = {'count': post.likes.all().count(), 'user_liked': True}
        return JsonResponse(data, status=200)

@login_required 
def following(request):
    #extract paginated post
    context = paginated_post(1, request.user, 'Following')
    return render(request, "network/following.html", context)

@login_required
def edit_post(request, post_id):
    # Composing a new post must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    else:
        # extract form from request
        form = NewPostForm(request.POST)
        #check form is valid so we can access cleaned data
        if form.is_valid():
            #retrieve post for the posts id
            post = Post.objects.get(id=post_id)
            #if the current user owns the post, extra the new content, append to post and save
            if post.user == request.user:
                post.post = form.cleaned_data['post']
                post.edited = True
                post.save()
                return JsonResponse({"message": "Post updated successfully."}, status=200)
            else:
                # Return an error response if the user doesn't own the post
                return JsonResponse({"error": "You don't have permission to edit this post."}, status=403)
        else:
            # Return a validation error if the form is invalid
            errors = form.errors.as_json()
            return JsonResponse({"error": errors}, status=400, content_type='application/json')

@login_required
def delete_post(request, post_id):
    #check user owns the post
    try:
        post = Post.objects.get(id=post_id, user=request.user)
    except Post.DoesNotExist:
        return JsonResponse({"message": "Either Post not found or you don't have permission to delete it."}, status=404)
    post_delete = post.delete()
    return JsonResponse({"message": "Post Deleted Successfully."}, status=200)

def profile(request, user_id):
    #get user from user_id
    user = User.objects.get(id=user_id)
    check = False
    if request.user.is_authenticated:
        #extract paginated post
        context = paginated_post(1, user, 'Profile')
        #check whether logged in user follows the profile
        check =  Follow.objects.filter(user = request.user, user_to_follow = user )  
        #if we're looking at the current users profile, load the new post form
        if user_id == request.user.id:
            form = NewPostForm()
            context['form'] = form
    else:
        #extract paginated post
        context = guest_paginated_post(1, user, 'Profile')
    #get follower and following count for the profile
    following_count = Follow.objects.filter(user = user).count()
    followers_count = Follow.objects.filter(user_to_follow = user).count()
    context['profile'] = {'userid': user.id, 'username': user.username, 'following_count':following_count, 'followers_count': followers_count}
    if check:
        context['profile']['user_follows']= True
    else:
        context['profile']['user_follows']= False
    return render(request, "network/profile.html", context)

@login_required
def follow(request, user_id, action):
    try:
        user_to_follow = get_object_or_404(User, id=user_id)
        if action == 'Follow':
            follow = Follow.objects.create(user=request.user, user_to_follow=user_to_follow)
            message =  "Followed Successfully."      
        else:
            unfollow = Follow.objects.get(user=request.user, user_to_follow = user_to_follow)
            unfollow.delete()
            message =  "Unfollowed Successfully." 
        #get updated follow/following counts for the profile
        profile_following = Follow.objects.filter(user__id = user_id).count()
        profile_followers = Follow.objects.filter(user_to_follow__id = user_id ).count()
        return JsonResponse({"message": message, "followers": profile_followers, "following" : profile_following}, status=200)       
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)
    except Follow.DoesNotExist:
        return JsonResponse({"error": "Follow not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

#stop being able to click on hearts if not logged in
#{% if user.is_authenticated %}
#add some error handling for urls that dont exist, or users not logged in or url parameters not there
#log in functionality- ie what to see if not logged in, be thorough
#consolidate new post function into paginated post function? 
#go through each function, syntax, error handling, conciseness
#then look at styles, mobile responsiveness


#issues:
#username link undefined on next page
#edit link is showing on every post- needs to be if current user