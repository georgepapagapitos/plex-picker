// static/js/modal.js

document.addEventListener('DOMContentLoaded', () => {

    const modal = document.getElementById('trailerModal');
    const buttons = document.querySelectorAll('.trailer-button');
    const closeBtn = modal.querySelector('.close');
    const iframe = document.getElementById('trailerIframe');
    const modalTitle = document.getElementById('modalMovieTitle');


    function openModal(trailerUrl, movieTitle) {
        modalTitle.textContent = movieTitle;
        iframe.src = trailerUrl;
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.body.classList.add('overflow-hidden'); // Prevent scrolling on the body
    }
    
    function closeModal() {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        iframe.src = ''; // Stop video playback
        document.body.classList.remove('overflow-hidden'); // Restore scrolling on the body
    }

    buttons.forEach((button, index) => {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            const trailerUrl = button.getAttribute('data-trailer-url');
            const movieTitle = button.getAttribute('data-movie-title');
            openModal(trailerUrl, movieTitle);
        });
    });

    closeBtn.addEventListener('click', closeModal);

    // Close modal when clicking outside of the modal content
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Close modal on escape key press
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeModal();
        }
    });
});