import json
from bson import json_util
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
    #query for extracting all posts from the database - in reverse order of timestamp
    all_posts = Post.objects.all().order_by("-timestamp").values('post', 'user', 'timestamp', 'likes', 'id', 'user_id')
    #extract page requested from the allposts query
    page = Paginator(all_posts, 10, orphans=4).page(page)

    # check if that page has a next and/or previous page
    prev_page = page.has_previous()
    next_page = page.has_next()

    #create a list of 10 dicts to pass through like information about the posts
    likes = [{}] * 10
    for i in range(10):
        likes[i]['like_count'] = Post.objects.get(id=page[i]['id']).likes.all().count()
        if Post.objects.get(id=page[i]['id']).likes.filter(id=request.user.id):
            likes[i]['user_liked'] = True
        likes[i]['user_name'] = User.objects.get(id=page[i]['user_id']).username
    
    #jsonify the queryset of posts to send through to the api response
    json_page = [json.dumps(p, default=json_util.default) for p in page]

    return JsonResponse({"message": "Loaded succesfully", "page": json_page, "likes": likes, 'prev_page' : prev_page, 'next_page' : next_page}, status=200)
    

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
