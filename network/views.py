import json
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import IntegrityError
from django.http import JsonResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect 
from django.urls import reverse
from django.core.paginator import Paginator
from django.core import serializers

from .models import User, Post
from .forms import NewPostForm
from django.forms.models import model_to_dict
from django.db.models import Count, Case, When, BooleanField


def index(request):
    #query for extracting all posts from the database - in reverse order of timestamp
    all_posts = Post.objects.all().order_by("-timestamp").values()
    
    # use paginator to extract just 10 posts for the page
    p = Paginator(all_posts, 10, orphans=4)
    #select page 1
    page = p.page(1)
    # check if that page has a next and/or previous page
    prev_page = p.page(1).has_previous()
    next_page = p.page(1).has_next()

    #loop over the posts in the page -  username of post, like counts and note if current user likes it    
    for post in page:
        post['like_count'] = Post.objects.get(id=post['id']).likes.all().count()
        post['user_liked'] = Post.objects.get(id=post['id']).likes.filter(id=request.user.id)
        post['user_name'] = User.objects.get(id=post['user_id'])
    context = {'posts': page, 'prev_page': prev_page, 'next_page': next_page }
    form = NewPostForm()
    context['form'] = form  
    return render(request, "network/index.html", context)

def load_post(request, page):
    #query for extracting all posts. use annotate and count to work out number of likes per post, and then case to work out if current user liked each post
    all_posts = Post.objects.annotate(
        num_likes=Count('likes'),
        user_liked=Case(
            When(likes=request.user, then=True),
            default=False,
            output_field=BooleanField(),
        )
        ).values('id', 'post', 'timestamp', 'num_likes', 'user_liked').order_by("-timestamp")

    #paginate all_posts and select page requested
    paginator = Paginator(all_posts, 10)
    page_obj = paginator.page(page)
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
    return JsonResponse(data, safe=False, status=200)

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
            post = Post.objects.get(id=instance.id)
            # extract timestamp and save to varaible as modeltodict doesnt render it so we need to add later
            timestamp = post.timestamp
            #use model to dict so we can send the instance dict in json response
            post = model_to_dict(post)
            post['timestamp'] = timestamp
            #send json response
            return JsonResponse({"message": "Posted succesfully", 'post': post }, status=201)



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
