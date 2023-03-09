var pageCount = 1; 
document.addEventListener('DOMContentLoaded', function() {
    //use this for showing messages
    const flashDiv = document.querySelector('.message');

    function main(){
        

        if(document.querySelector('form')){
            document.querySelector('form').addEventListener('submit', e => newPost(e));
        }
        document.querySelectorAll('.load-posts').forEach(item => item.addEventListener('click', e => loadPost(e)));

        
        //event listener for if user wants to edit post
        editClick();

        //event listener for liking post (needs to be function so the listeners are added when new page loaded)
        likeEventListeners();        
    }

    function likeEventListeners() {
        document.querySelectorAll('.fa-heart').forEach(item => item.addEventListener('click', e => likePost(e)));
     }

    function editClick(){
        if(document.querySelector('.edit')){
            document.querySelectorAll('.edit').forEach(item => item.addEventListener('click', e => editPost(e)));
        }
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
        //determine what page type we're on:
        const url = window.location.href
        console.log(url)
        console.log(url.indexOf('profile'))
        let pageType;
        if(url.indexOf("profile") !== -1){
            pageType = 'Profile';
        }
        else if(url.indexOf("following") !== -1){
            pageType = 'Following';
        }
        else{
            pageType = 'Index';
        }
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
        fetch('/load_post/' + pageCount + '/' + pageType)
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
        const likeText = parent.querySelector('span.num-likes');
        //to unlike the post
        if (parent.classList.contains('user-liked')) {
            likeApi('Dislike', postId)
            .then(res => {
                parent.classList  = 'user-disliked likes';
                if(res.count > 0){
                    likeText.innerHTML = '(' + res.count + ')';
                }
                else{
                    likeText.innerHTML = '';
                }
                console.log(res.count);


            })

        }
        //to like the post
        else {
            likeApi('Like', postId)
            .then(res => {
                parent.classList  = 'user-liked likes';
                if(res.count > 0){
                    likeText.innerHTML = '(' + res.count + ')';
                }
                else{
                    likeText.innerHTML = '';
                }
                console.log(res.count);
            })
        }
    }

    function likeApi(action, postId){
        url = 'likes/' + postId + '/' + action;
        return fetch(url)
        .then(response => response.json())
        .then(data => {
             return data;
        });


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

    
    function editPost(e){
        // create a text box
        const id = e.target.parentNode.parentNode.querySelector('.post-id').innerHTML;
        let div = document.createElement("div");
        //blur everything outside the text box 
        let body = document.querySelector('body');
        let postSection = document.querySelector('.body');
        postSection.classList = 'blur-section';
        div.classList = "edit-box";
   
        //create form, loaded with current post text inside
        const form = document.createElement("form");
        form.method ="POST";
        form.action = "{% url 'edit_post' %}";
        
        const label = document.createElement("label");
        label.for = "postInput";
        label.textContent = "Edit Post:";
        label.style.display = "block";

        const input = document.createElement("input");
        input.type = "text";
        input.id = "postInput";
        input.name = "post";
        input.style.width = "70%";
        input.placeholder = e.target.dataset.formContent;

        // Get the CSRF token from the cookie
        const csrfToken = Cookies.get('csrftoken');
        // Create a hidden input field for the CSRF token
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;


        const editButton = document.createElement("button");
        editButton.type = "submit";
        editButton.textContent = "Submit";
        editButton.dataset.id = id;

        const formP = document.createElement("p");
        formP.innerHTML = "or delete entirely?";
        formP.style.display = "block";
        formP.style.margin = "0.5rem 0.5rem 0.5rem auto";

        const deleteButton = document.createElement("button");
        deleteButton.type = "submit";
        deleteButton.textContent = "Delete";
        deleteButton.dataset.id = id;

        const xBox = document.createElement('i');
        xBox.classList ='fa fa-times';

        form.append(label, input, csrfInput, editButton, formP, deleteButton);
        div.append(form, xBox);
        body.append(div);
        
        //listen for user clicking 'x'
        xBox.addEventListener('click', function(){
            div.remove();
            postSection.classList = 'body';            
        })

        //create a variable for the post we're updating/deleting, so we can pass to function and update it on front end
        const origDiv = e.target

        //listen for user submitting edit
        editButton.addEventListener('click', e => editFetch(e, div, postSection, origDiv));
        //listen for user deleting post
        deleteButton.addEventListener('click', e => deleteFetch(e));
       
    }

    function editFetch(e, div, postSection, origDiv){
        e.preventDefault()
        // get form from e.target and pass in fetch call 
        let form =  e.target.form;
        //get the id of the post, to use for the dynamic url
        const editInput = e.target.form.querySelector('#postInput').value
        
        let postId = e.target.dataset.id;
        let status;
        let message;
        fetch('/edit_post/' + postId,{
            method: 'POST',
            body: new FormData(form),
        })
        .then(response => {
            status = response.status
            return response.json();
        })
        .then(text => {
            message = text['message']
            console.log(message);
            console.log(status)
            //if post updated, update original div and give success message

            if(status ==200){
                //get the parent node of the edit button clicked, so we can update it
                let origParent = origDiv.parentNode
                //update post content to what was typed in
                origDiv.parentNode.innerHTML = editInput + ' ';
                //recreate the edit button and append it
                let edit = document.createElement('a');
                edit.href = "javascript:;"
                edit.classList = "edit";
                edit.innerHTML = "Edit";
                edit.setAttribute("data-form-content", editInput);
                origParent.append(edit);
                //add the event listener back for the edit button
                editClick();
                //display success message
                successMessage(message);
            }
            else{
                //display error message
                errorMessage(message);
            }
            div.remove();
            postSection.classList = 'body'; 
        })
    }

    function deleteFetch(e){
        e.preventDefault()
        let postId = e.target.dataset.id;
        fetch('/delete_post/' + postId)
        console.log(postId)
        return false;
    }

    function successMessage(message){
        flashDiv.innerHTML = message;
        flashDiv.classList = 'message success';
    }

    function errorMessage(message){
        flashDiv.innerHTML = message;
        flashDiv.classList = 'message error';
    }


    main()


})