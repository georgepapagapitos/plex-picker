// static/js/plex_content.js

document.addEventListener("DOMContentLoaded", function() {
    const moviesList = document.getElementById("movies-list");
    const showsList = document.getElementById("shows-list");
    const searchForm = document.getElementById("search-form");
    const resetButton = document.getElementById("reset-button");
    const searchInput = document.querySelector('input[name="query"]');

    function fetchContent(url, params) {
        const xhr = new XMLHttpRequest();
        xhr.open("GET", `${url}?${new URLSearchParams(params)}`, true);
        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
        xhr.onload = function() {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                updateContent(response);
            } else {
                console.error("Failed to fetch data:", xhr.statusText);
            }
        };
        xhr.send();
    }

    function updateContent(response) {
        moviesList.innerHTML = response.movies.map(movie => `
            <li class="bg-gray-800 rounded-md p-3 hover:bg-gray-700 transition duration-150">
                <a href="/movies/${movie.id}/" class="text-blue-400 hover:text-blue-300">${movie.title}</a>
                <span class="text-gray-400">(${movie.year})</span>
            </li>
        `).join("");
        showsList.innerHTML = response.shows.map(show => `
            <li class="bg-gray-800 rounded-md p-3 hover:bg-gray-700 transition duration-150">
                <a href="/shows/${show.id}/" class="text-blue-400 hover:text-blue-300">${show.title}</a>
                <span class="text-gray-400">(${show.year})</span>
            </li>
        `).join("");

        updatePagination(document.querySelector('.movie-pagination'), response.movie_page, response.movie_total_pages, 'movie');
        updatePagination(document.querySelector('.show-pagination'), response.show_page, response.show_total_pages, 'show');
    }

    function updatePagination(paginationElement, currentPage, totalPages, type) {
        const stepLinks = paginationElement.querySelector('.step-links');
        stepLinks.innerHTML = '';

        const searchParams = new URLSearchParams(window.location.search);
        searchParams.delete('movie_page');
        searchParams.delete('show_page');

        if (currentPage > 1) {
            stepLinks.innerHTML += `<a href="?${type}_page=1&${searchParams.toString()}" data-page="1" class="first-page px-3 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 mr-2">« First</a>`;
            stepLinks.innerHTML += `<a href="?${type}_page=${currentPage - 1}&${searchParams.toString()}" data-page="${currentPage - 1}" class="previous-page px-3 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 mr-2">Previous</a>`;
        }

        stepLinks.innerHTML += `<span class="current-page text-gray-400 mx-2">Page ${currentPage} of ${totalPages}</span>`;

        if (currentPage < totalPages) {
            stepLinks.innerHTML += `<a href="?${type}_page=${currentPage + 1}&${searchParams.toString()}" data-page="${currentPage + 1}" class="next-page px-3 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 ml-2">Next</a>`;
            stepLinks.innerHTML += `<a href="?${type}_page=${totalPages}&${searchParams.toString()}" data-page="${totalPages}" class="last-page px-3 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 ml-2">Last »</a>`;
        }
    }

    // Event delegation for pagination clicks
    document.addEventListener('click', function(event) {
        if (event.target.matches('.pagination a')) {
            event.preventDefault();
            const page = event.target.getAttribute('data-page');
            const type = event.target.closest('.pagination').classList.contains('movie-pagination') ? 'movie' : 'show';
            const params = new URLSearchParams(window.location.search);
            params.set(`${type}_page`, page);
            fetchContent(window.location.pathname, params);
            history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
        }
    });

    // Reset button functionality
    resetButton.addEventListener('click', function(event) {
        event.preventDefault();
        searchInput.value = '';
        fetchContent(window.location.pathname, {});
        history.pushState({}, '', window.location.pathname);
    });

    // Handle form submission
    searchForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const params = new URLSearchParams(new FormData(searchForm));
        fetchContent(window.location.pathname, params);
        history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
    });
});