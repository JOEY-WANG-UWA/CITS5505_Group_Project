document.addEventListener('DOMContentLoaded', function () {
    const defaultErrorMessage = 'Server error, please try again later.';
    let hoverTimer = null;

    function showPostDetails(imgUrl, title, description) {
        console.log(imgUrl, title, description);
        $('#modalImg').attr('src', imgUrl);
        $('#postModalLabel').text(title);
        $('#modalDesc').text(description);
        $('#modalLikes').text('Likes: ' + likes);
        $('#postModal').modal('show');
    }