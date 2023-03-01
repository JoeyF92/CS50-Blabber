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
            console.log(result.post.post);
            console.log(result.post.user);
            console.log(result.post.likes);
            console.log(result.post.timestamp);
        })
        
        return false;
    }

    function loadPost(e){
        //check if user loading next or previous posts
        if(e.target.dataset.pageDirection === 'Next'){
            pageCount ++;
        }
        else if(e.target.dataset.pageDirection === 'False'){
            pageCount --;
        }
        //fetch requested page of posts
        fetch('/load_post/' + pageCount)
        .then(response => response.json())
        .then(data => {
            console.log(data);
            console.log(data.posts[0]['timestamp'])
            console.log('hi');

            // trigger animation to hide posts
            //delete all posts on page
            document.querySelectorAll('.post-group').forEach(item => item.remove());
            //add new posts to the page
            for (i = 0; i <10; i++){
                let postSection = document.querySelector('.post-section')
                //here we're looping through 1-10, and creating a post group for each to append to the section
                let postGroup = document.createElement('div');
                postGroup.classList.add('post-group');
                let leftPost = document.createElement('div');
                leftPost.classList.add('left-post');
                let rightPost = document.createElement('div');
                rightPost.classList.add('right-post');
                let userNameP = document.createElement('p');
                userNameP.innerHTML = data.page[i]['post'];
                let postP = document.createElement('p');
                postP.innerHTML = 'hello';
                let timeP = document.createElement('p');
                timeP.innerHTML = 'hello';
                let likeP = document.createElement('p');
                likeP.innerHTML  = 'hello';
                rightPost.appendChild(userNameP);
                leftPost.append(postP, timeP, likeP);
                postGroup.append(rightPost, leftPost);
                postSection.append(postGroup);
                console.log(postSection);
            }        
        })

        

    }
        

    main()


})