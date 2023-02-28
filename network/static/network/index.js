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
        let url = '/load_post/' + pageCount;
        fetch('/load_post/' + pageCount)
        .then(response => response.json())
        .then(res => console.log(res))
        

    }
        

    main()


})