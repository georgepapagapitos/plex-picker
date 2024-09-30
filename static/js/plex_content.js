// static/js/plex_content.js

document.addEventListener("DOMContentLoaded", function() {
    const moviesList = document.getElementById("movie-list");
    const showsList = document.getElementById("show-list");
    const searchForm = document.getElementById("search-form");
    const resetButton = document.getElementById("reset-button");
    const searchInput = document.querySelector('input[name="query"]');

    function fetchContent(url, params) {
        const xhr = new XMLHttpRequest();
        xhr.open("GET", `${url}?${params.toString()}`, true);
        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    updateContent(response);
                } catch (e) {
                    console.error("Error parsing JSON response:", e);
                }
            } else {
                console.error("Failed to fetch data:", xhr.statusText);
            }
        };
        xhr.onerror = function() {
            console.error("Network error occurred");
        };
        xhr.send();
    }

    function updateContent(response) {
        if (moviesList) {
            updateList(moviesList, response.movies, 'movie', response.movie_page, response.movie_total_pages);
        } else {
            console.error("Movies list element not found");
        }
        if (showsList) {
            updateList(showsList, response.shows, 'show', response.show_page, response.show_total_pages);
        } else {
            console.error("Shows list element not found");
        }
    }

    function updateList(listElement, items, type, currentPage, totalPages) {
        if (!listElement) {
            console.error(`List element for ${type} not found`);
            return;
        }
        listElement.innerHTML = items.map(item => `
            <li class="bg-gray-800 rounded-md p-3 hover:bg-gray-700 transition duration-150">
                <a href="/${type}s/${item.id}/" class="text-blue-400 hover:text-blue-300">${item.title}</a>
                <span class="text-gray-400">(${item.year})</span>
            </li>
        `).join("");

        updatePagination(`.${type}-pagination`, currentPage, totalPages, type);
    }

    function updatePagination(selector, currentPage, totalPages, type) {
        const paginationElement = document.querySelector(selector);
        if (!paginationElement) return;

        let html = '<span class="step-links flex items-center justify-center space-x-2">';

        if (currentPage > 1) {
            html += `<a href="#" data-page="1" data-type="${type}" class="first-page px-3 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500">« First</a>`;
            html += `<a href="#" data-page="${currentPage - 1}" data-type="${type}" class="previous-page px-3 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500">Previous</a>`;
        }

        html += `<span class="current-page text-gray-400">Page ${currentPage} of ${totalPages}</span>`;

        if (currentPage < totalPages) {
            html += `<a href="#" data-page="${currentPage + 1}" data-type="${type}" class="next-page px-3 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500">Next</a>`;
            html += `<a href="#" data-page="${totalPages}" data-type="${type}" class="last-page px-3 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500">Last »</a>`;
        }

        html += '</span>';

        paginationElement.innerHTML = html;

        // Reattach event listeners to pagination links
        paginationElement.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', function(event) {
                event.preventDefault();
                const page = this.getAttribute('data-page');
                const paginationType = this.getAttribute('data-type');
                const params = new URLSearchParams(window.location.search);
                params.set(`${paginationType}_page`, page);
                if (searchInput.value) {
                    params.set('query', searchInput.value);
                }
                fetchContent(window.location.pathname, params);
                history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
            });
        });
    }

    // Reset button functionality
    resetButton.addEventListener('click', function(event) {
        event.preventDefault();
        searchInput.value = '';
        fetchContent(window.location.pathname, new URLSearchParams());
        history.pushState({}, '', window.location.pathname);
    });

    // Handle form submission
    searchForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const params = new URLSearchParams(new FormData(searchForm));
        fetchContent(window.location.pathname, params);
        history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
    });

    // Initial load
    fetchContent(window.location.pathname, new URLSearchParams(window.location.search));
});