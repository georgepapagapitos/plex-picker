document.addEventListener('DOMContentLoaded', () => {
    console.log("Document loaded");
    const modal = document.getElementById('trailerModal');
    const iframe = document.getElementById('trailerIframe');
    const closeBtn = document.querySelector('.modal .close');

    // Open modal when button is clicked
    document.querySelectorAll('.trailer-button').forEach(button => {
        button.addEventListener('click', () => {
            console.log("Button clicked");
            const trailerUrl = button.getAttribute('data-trailer-url');
            console.log("Trailer URL:", trailerUrl);
            iframe.src = trailerUrl;
            modal.style.display = 'block';
        });
    });

    // Close modal when close button is clicked
    closeBtn.addEventListener('click', () => {
        console.log("Close button clicked");
        modal.style.display = 'none';
        iframe.src = ''; // Stop video playback
    });

    // Close modal when clicking outside of the modal
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            console.log("Clicked outside modal");
            modal.style.display = 'none';
            iframe.src = ''; // Stop video playback
        }
    });
});