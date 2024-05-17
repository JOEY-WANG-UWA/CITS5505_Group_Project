

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

//upload
document.addEventListener("DOMContentLoaded", function () {
    // Prevent Dropzone from auto discovering the form
    Dropzone.autoDiscover = false;

    // Initialize Dropzone
    var myDropzone = new Dropzone("#dropzone-area", {
        url: document.getElementById('file-upload').action,  // Ensure this matches your Flask route
        paramName: "file",
        maxFilesize: 2, // MB
        acceptedFiles: ".jpg,.jpeg,.png,.gif,.webp",
        dictDefaultMessage: "Drag files here or click to upload",
        autoProcessQueue: false,  // Prevent auto upload
        uploadMultiple: true,  // Upload multiple files in one request
        parallelUploads: 10,  // Number of parallel uploads
        addRemoveLinks: true,  // Add remove links
        init: function() {
            var myDropzone = this;
            var fileList = [];

            // Handle form submission
            document.querySelector("#file-upload").addEventListener("submit", function(event) {
                event.preventDefault();
                event.stopPropagation();

                if (myDropzone.getQueuedFiles().length > 0) {
                    // Create a FormData object and append form data
                    var formData = new FormData(this);
                    // Append each file to the FormData object
                    myDropzone.getQueuedFiles().forEach(function(file) {
                        formData.append("file", file);
                    });

                    // Use XMLHttpRequest to send the form data
                    var xhr = new XMLHttpRequest();
                    xhr.open("POST", document.getElementById('file-upload').action, true);
                    xhr.onload = function () {
                        if (xhr.status === 200) {
                            window.location.href = "/gallery";  // Redirect to gallery page
                        } else {
                            // Handle error
                            alert("An error occurred: " + xhr.responseText);
                        }
                    };
                    xhr.send(formData);
                } else {
                    // If no files, just submit the form
                    this.submit();
                }
            });

            // Append form data to the file upload
            this.on("sendingmultiple", function(files, xhr, formData) {
                var formElements = document.querySelectorAll("#file-upload input, #file-upload select, #file-upload textarea");
                formElements.forEach(function(element) {
                    formData.append(element.name, element.value);
                });
            });

            // Handle file added event
            this.on("addedfile", function(file) {
                fileList.push(file.name);
            });

            // Handle file removed event
            this.on("removedfile", function(file) {
                var index = fileList.indexOf(file.name);
                if (index > -1) {
                    fileList.splice(index, 1);
                }
            });

            // Handle successful file upload
            this.on("successmultiple", function(files, response) {
                // Optionally handle successful uploads
                window.location.href = "/gallery";  // Redirect to gallery page
            });

            // Handle upload errors
            this.on("errormultiple", function(files, response) {
                // Ensure response is converted to string if necessary
                if (typeof response !== "string") {
                    response = JSON.stringify(response);
                }
                files.forEach(function(file) {
                    file.previewElement.querySelector(".dz-error-message").textContent = response;
                });
            });
        }
    });

    // Initialize Sortable on Dropzone element
    Sortable.create(myDropzone.element, {
        draggable: ".dz-preview",
        onEnd: function(evt) {
            var files = myDropzone.getAcceptedFiles();
            var orderedFiles = [];
            document.querySelectorAll("#dropzone-area .dz-preview").forEach(function(element) {
                var filename = element.querySelector(".dz-filename span").innerText;
                var file = files.find(f => f.name === filename);
                if (file) {
                    orderedFiles.push(file);
                }
            });
            myDropzone.files = orderedFiles;
        }
    });
});
