

function showPostDetails(imgUrl, title, description) {
    console.log(imgUrl, title, description);
    $('#modalImg').attr('src', imgUrl);
    $('#postModalLabel').text(title);
    $('#modalDesc').text(description);
    $('#modalLikes').text('Likes: ' + likes);
    $('#postModal').modal('show');
}



function toggleHeart(element) {
    if (element.classList.contains('fas')) {
        // 切换到空心
        element.classList.remove('fas');
        element.classList.add('far');
    } else {
        // 切换到实心
        element.classList.remove('far');
        element.classList.add('fas');
    }
}

function submitComment(uploadId) {
    const input = document.getElementById('comment-input-' + uploadId);
    const comment = input.value.trim();
    if (!comment) {
        alert('Comment cannot be empty!');
        return;
    }

    // Simple fetch request
    fetch(`/post_comment/${uploadId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ comment: comment }),
        credentials: 'include'  // Ensure cookies are sent with the request for user session
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Append the new comment to the comment section
                const commentSection = document.getElementById('comment-section-' + uploadId);
                const newComment = document.createElement('div');
                newComment.className = 'comment';
                newComment.innerHTML = `<strong>${data.username}</strong>: ${comment}`;
                commentSection.appendChild(newComment);
                input.value = ''; // Clear input field after posting

                // Update all comment count elements
                const commentCounts = document.querySelectorAll('.comment-count-' + uploadId);
                commentCounts.forEach(count => {
                    let currentCount = parseInt(count.textContent, 10) || 0;
                    count.textContent = currentCount + 1;
                });
            } else {
                alert('Failed to post comment: ' + data.message);
            }
        })
        .catch(error => console.error('Error:', error));
}