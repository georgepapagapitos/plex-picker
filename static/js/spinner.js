document.addEventListener("DOMContentLoaded", function() {
    const loadingDiv = document.getElementById('loading');
    const moviesContainer = document.getElementById('moviesContainer');
    const images = document.querySelectorAll('.movie-poster');

    function loadImage(img) {
        return new Promise((resolve, reject) => {
            if (img.complete) {
                resolve(); // If already loaded
            } else {
                img.addEventListener('load', resolve);
                img.addEventListener('error', reject);
            }
        });
    }

    if (images.length === 0) {
        // No images to load, so just hide the spinner
        loadingDiv.style.display = 'none';
        moviesContainer.style.display = 'flex';
        return;
    }

    // Create an array of promises for each image
    const imagePromises = Array.from(images).map(loadImage);

    // Wait for all images to load
    Promise.all(imagePromises)
        .then(() => {
            loadingDiv.style.display = 'none';
            moviesContainer.style.display = 'flex';
        })
        .catch(() => {
            // Handle image load errors if needed
            loadingDiv.style.display = 'none';
            moviesContainer.style.display = 'flex';
        });
});