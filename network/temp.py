
def refactor(page_number, user=None, page_type='Index'):
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
    if page_type == 'Profile':
        # do a query for all posts, filtering for posts by the user id (traverse the foreign key again)
        all_posts = Post.objects.filter(user=user)
    #else we're looking at the index page
    else:
        # main query for extracting all posts. use annotate + count to work out number of likes per post
        all_posts = Post.objects.all()

    all_posts = all_posts.annotate(num_likes=Count('likes')).annotate(
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
