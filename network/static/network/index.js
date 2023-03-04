var pageCount = 1; 
document.addEventListener('DOMContentLoaded', function() {

    function main(){

        document.querySelector('form').addEventListener('submit', e => newPost(e));
        document.querySelectorAll('.load-posts').forEach(item => item.addEventListener('click', e => loadPost(e)));
        //event listener for liking post (needs to be function so the listeners are added when new page loaded)
        likeEventListeners();
    }

    function likeEventListeners() {
        document.querySelectorAll('.fa-heart').forEach(item => item.addEventListener('click', e => likePost(e)));
     }

    function newPost(e)
    {
        e.preventDefault()
        // extract form input from e 
        form = e.target.elements;
        fetch('/new_post', {
            method: "POST",
            body: JSON.stringify({
                post: form.post.value
            }),
            headers: {
                "X-CSRFToken": form.csrfmiddlewaretoken.value
            }
        })
        .then(response => response.json())
        .then(result => {
            let post = result.post.post;
            let timestamp = result.post.timestamp;
            let username = result.post.username;
            let userLiked = result.post.user_liked;
            let numLikes = result.post.num_likes;
            let id = result.post.id;
            let postType = 'New';
            let newPost = createPost(post, timestamp, username, id, userLiked, numLikes, postType);
        })
        
        return false;
    }

    function loadPost(e)
    {
        //check if user loading next or previous posts
        console.log(e.target.dataset.pageDirection)
        if(e.target.dataset.pageDirection === 'Next'){
            pageCount ++;
            var postType = 'Next';
        }
        else if(e.target.dataset.pageDirection === 'Previous'){
            pageCount --;
            var postType = 'Prev';
        }
        //fetch requested page of posts
        fetch('/load_post/' + pageCount)
        .then(response => response.json())
        .then(data => {
            // trigger animation to hide posts
            let removePosts = document.querySelectorAll('.post-group');
            if (postType === 'Next') {
                removePosts.forEach(item => {
                    item.className = '';
                    item.classList.add('post-group');
                    item.classList.add('remove-posts-left');   
                });
            } else if (postType === 'Prev') {
                removePosts.forEach(item => {
                    item.className = '';
                    item.classList.add('post-group');
                    item.classList.add('remove-posts-right'); 
                });
            }
            //set one second timeout to allow animation to run before next steps.          
            setTimeout(() => 
            {
                //delete the current page of posts on the page
                removePosts.forEach(item => item.remove());
                
                //add new posts to the page
                for (i = 0; i < data.posts.length; i++){
                    let post = data.posts[i].post;
                    let timestamp = data.posts[i].timestamp;
                    let username = data.posts[i].username;
                    let userLiked = data.posts[i].user_liked;
                    let id = data.posts[i].id;
                    let numLikes = data.posts[i].num_likes;
                    let newPost = createPost(post, timestamp, username, id, userLiked, numLikes, postType);
                }
                //check if there is a next or previous page we can load, and show buttons accordingly
                prevButton = document.querySelector('.prev-btn')
                nextButton = document.querySelector('.next-btn')
                if( data.prev_page === true){
                    prevButton.disabled = false;
                }
                else
                {
                    prevButton.disabled = true;
                }
                if( data.next_page === true){
                    nextButton.disabled = false;
                }
                else
                {
                    nextButton.disabled = true;
                }                   
                //add like event listeners:
                likeEventListeners();
                }, 1000)              
        })
    }

    function likePost(e){
        const parent = e.target.parentNode;
        //get the posts id 
        const postId  = parent.parentNode.querySelector('.post-id').innerHTML
        //to unlike the post
        if (parent.classList.contains('user-liked')) {
            likeApi('dislike', postId);
        }
        //to like the post
        else{
            likeApi('like', postId);
        }
    }

    function likeApi(action, postId){
        action = action === 'like' ? "likes/like" : "likes/dislike";
        console.log(action);
        //fetch(url + '/' + postId)
        //.then(response => response.json())
        //.then(data => {


    }

    function createPost(post, timestamp, username, id, userLiked, numLikes, postType){
        let postSection = document.querySelector('.post-section');
        //create a new post, adding in the information from the function params
        let postGroup = document.createElement('div');
  
        let leftPost = document.createElement('div');
        leftPost.classList.add('left-post');
        
        let userNameP = document.createElement('p');
        userNameP.innerHTML = username;

        let timeP = document.createElement('p');
        timeP.classList.add('time-post');
        timeP.innerHTML = timestamp;
        
        leftPost.append(userNameP, timeP);

        let rightPost = document.createElement('div');
        rightPost.classList.add('right-post');
        let postP = document.createElement('p');
        postP.classList.add('post-post');
        postP.innerHTML = post;

        let idP = document.createElement('p');
        idP.classList.add('post-id');
        idP.innerHTML = id;
        idP.hidden = true;

        let likeP = document.createElement('p');
        if(userLiked === true){
            likeP.classList.add('user-liked');
        }
        else{
            likeP.classList.add('user-disliked');
        }
        likeP.classList.add('likes');
        let heart = document.createElement('i');
        heart.classList.add('fa');
        heart.classList.add('fa-heart');
        likeP.append(heart);
        let span = document.createElement('span');
        span.classList.add('num-likes');
        if(numLikes > 0){
            span.innerHTML  = ' (' + numLikes + ')';
        }
        likeP.append(heart, span);
        rightPost.append(postP, idP, likeP);
        postGroup.append(leftPost, rightPost);

        //here i add loaded-new-post as an extra class so i can animate it

        if( postType === 'New'){
            postGroup.classList.add('post-group', 'loaded-new-post');
            postSection.insertBefore(postGroup, postSection.firstChild);
            //remove the entered text from the input
            var textbox = document.querySelector('textarea[name="post"]');
            textbox.value = '';
          }
        else if ( postType === 'Next')
        {
            postGroup.className = '';
            postGroup.classList.add('post-group');
            postGroup.classList.add('loaded-prev-posts');   
            postSection.append(postGroup);

        }
        else if ( postType === 'Prev')
        {
            postGroup.className = '';
            postGroup.classList.add('post-group');
            postGroup.classList.add('loaded-next-posts');   
            postSection.append(postGroup);

        }
     }

        

    main()


})