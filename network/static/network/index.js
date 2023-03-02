var pageCount = 1; 
document.addEventListener('DOMContentLoaded', function() {

    function main(){

        document.querySelector('form').addEventListener('submit', e => newPost(e));
        document.querySelectorAll('.load-posts').forEach(item => item.addEventListener('click', e => loadPost(e)));


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
            let postType = 'New'
            let newPost = createPost(post, timestamp, username, userLiked, numLikes, postType);
        })
        
        return false;
    }

    function loadPost(e)
    {
        //check if user loading next or previous posts
        if(e.target.dataset.pageDirection === 'Next'){
            pageCount ++;
        }
        else if(e.target.dataset.pageDirection === 'Previous'){
            pageCount --;
        }
        //fetch requested page of posts
        fetch('/load_post/' + pageCount)
        .then(response => response.json())
        .then(data => {

            // trigger animation to hide posts
            removePosts = document.querySelectorAll('.post-group');
            
            //delete all posts on page - first start animation
            //removePosts.forEach(item => item.style.animationPlayState = 'running')
            //then after 1 second, remove the items
            removePosts.forEach(item => item.remove());
            //add new posts to the page
            for (i = 0; i <10; i++){
                let post = data.posts[i].post;
                let timestamp = data.posts[i].timestamp;
                let username = data.posts[i].username;
                let userLiked = data.posts[i].user_liked;
                let numLikes = data.posts[i].num_likes;
                let postType = 'Next'
                let newPost = createPost(post, timestamp, username, userLiked, numLikes, postType);
            }
            prevButton = document.querySelector('.prev-btn')
            nextButton = document.querySelector('.next-btn')
            if( data.prev_page === true){
                prevButton.hidden = false;
            }
            else
            {
                prevButton.hidden = true;
            }
            if( data.next_page === true){
                nextButton.hidden = false;
            }
            else
            {
                nextButton.hidden = true;
            }                   
        })
    }

    function createPost(post, timestamp, username, userLiked, numLikes, postType){
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

        let likeP = document.createElement('p');
        likeP.classList.add('likes');
        if(userLiked === true){
            likeP.classList.add('user-liked');
        }
        else{
            likeP.classList.add('user-disliked');
        }
        let heart = document.createElement('i');
        heart.classList.add('fa');
        heart.classList.add('fa-heart');
        likeP.append(heart);
        if(numLikes > 0){
            likeP.innerHTML  = '(' + numLikes + ')';
        }
        rightPost.append(postP, likeP);
        postGroup.append(leftPost, rightPost);

        //here i add loaded-new-post as an extra class so i can animate it

        if( postType === 'New'){
            postGroup.classList.add('post-group', 'loaded-new-post');
            postSection.insertBefore(postGroup, postSection.firstChild);
            var textbox = document.querySelector('input[name="post"]');
            textbox.value = '';
            console.log('in here')
        }
        else
        {
            postGroup.classList.add('post-group', 'loaded-next-posts' );
            postSection.append(postGroup);

        }
     }
        

    main()


})