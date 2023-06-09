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

from .models import User, Post, Follow
from .forms import NewPostForm
from django.forms.models import model_to_dict
from django.db.models import Count, Case, When, BooleanField, F, Subquery, OuterRef



def get_posts(page_number, user=None, page_type='Index', logged_in=False):
    #if we're looking on the follow page
    if page_type == 'Following':
        # extract the people that the current user is following - using __ to traverse the user foreign key, to retrieve the id
        following = Follow.objects.filter(user=user).values_list('user_to_follow__id', flat=True)
        # do a query for all posts, filtering for posts by the user id (traverse the foreign key again)
        all_posts = Post.objects.filter(user__id__in=following) 
    #else if we're looking at a profile page
    elif page_type == 'Profile':
        #do a query for all posts, filtering for posts by the user id (traverse the foreign key again)
        all_posts = Post.objects.filter(user=user)
    #else we're looking at the index page      
    else:
        all_posts = Post.objects.all()
    #annotate all_posts for extra fields, use count to work out number of likes per post
    all_posts = all_posts.annotate(num_likes=Count('likes'),
        #add username and id field, by traversing user
        username=F('user__username'),
        userid=F('user__id'))
    # annotate extra fields for if the page is viewed by a logged in user
    if logged_in:
        all_posts = all_posts.annotate(
        #use subquery to see if user has liked each post - using reverse relation on the user model
        user_liked=models.Exists(
            user.liked.filter(id=OuterRef('pk')).values('id')
        ),
        #add is owner field, which is True is current users id matches the posts id
        is_owner=Case(
            When(user_id=user.id, then=True),
            default=False,
            output_field=BooleanField()
        )
        #extract values we want to pass through in response and order by timestamp   
        ).values('id', 'post', 'username', 'timestamp', 'num_likes', 'user_liked', 'userid', 'edited', 'is_owner').order_by("-timestamp")
    #else if not logged in, extract the following fields from all_posts
    else:
        all_posts = all_posts.values('id', 'post', 'username', 'timestamp', 'num_likes', 'userid', 'edited').order_by("-timestamp")

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
        #extract posts for page one index, logged in user
        context = get_posts(1, request.user, 'Index', logged_in=True)
        #pass in form to allow new posts to be made by user
        form = NewPostForm()
        context['form'] = form
    else:
        #extract posts for page one index, non-logged in user
        context = get_posts(1, None, 'Index', logged_in=False) 
    return render(request, "network/index.html", context)

def load_post(request, page, page_type):
    if request.user.is_authenticated:
        #extract next/prev page of posts for the requested page
        data = get_posts(page, request.user, page_type, logged_in=True)
        data['isloggedin'] = True
    else:
        data = get_posts(page, None, page_type, logged_in=False)
        data['isloggedin'] = False
    return JsonResponse(data)

@login_required
def new_post(request):
    if request.method == "POST":
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
    else:
        return JsonResponse({"error": "POST request required."}, status=400)

@login_required
def likes(request, post_id, action):
    #extract user and the post being liked/disliked
    user = request.user
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post not found.'}, status=404)
    #depending on action, add/remove like for that post
    if action == 'Like':
        post.likes.add(user)
        data = {'count': post.likes.all().count(), 'user_liked': False}
        return JsonResponse(data, status=200)
    elif action == 'Dislike':
        post.likes.remove(user)
        data = {'count': post.likes.all().count(), 'user_liked': True}
        return JsonResponse(data, status=200)
    else:
        return JsonResponse({'error': 'Invalid action.'}, status=400)

@login_required 
def following(request):
    #extract the posts of profiles followed by user
    context = get_posts(1, request.user, 'Following', logged_in=True)
    return render(request, "network/following.html", context)


@login_required
def edit_post(request, post_id):
    if request.method == "POST":
        # extract form from request
        form = NewPostForm(request.POST)
        #check form is valid so we can access cleaned data
        if form.is_valid():
            #retrieve post for the posts id, or rtn 404 if doesnt exist
            post = get_object_or_404(Post, id=post_id)
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
    return JsonResponse({"error": "POST request required."}, status=400)

@login_required
def delete_post(request, post_id):
    #check user owns the post and if so then delete
    try:
        post = Post.objects.get(id=post_id, user=request.user)
    except Post.DoesNotExist:
        return JsonResponse({"message": "Either Post not found or you don't have permission to delete it."}, status=404)
    post_delete = post.delete()
    return JsonResponse({"message": "Post Deleted Successfully."}, status=200)

def profile(request, user_id):
    #get user from user_id or raise 404 error if user not found
    user = get_object_or_404(User, id=user_id)
    #create variable for checking if current user follows the profile
    check = False
    #if user logged in
    if request.user.is_authenticated:
        #extract paginated post
        context = get_posts(1, user, 'Profile', logged_in=True)
        #check whether logged in user follows the profile
        check =  Follow.objects.filter(user = request.user, user_to_follow = user )  
        #if we're looking at the current users profile, load the new post form
        if user_id == request.user.id:
            form = NewPostForm()
            context['form'] = form
    else:
        #extract paginated post
        context = get_posts(1, user, 'Profile', logged_in=False)
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
        #check user exists
        user_to_follow = get_object_or_404(User, id=user_id)
        #then follow or unfollow depending on action
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




