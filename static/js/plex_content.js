// static/js/plex_content.js

document.addEventListener("DOMContentLoaded", function () {
    const moviesList = document.getElementById("movie-list");
    const showsList = document.getElementById("show-list");
    const searchForm = document.getElementById("search-form");
    const resetButton = document.getElementById("reset-button");
    const searchInput = document.querySelector('input[name="query"]');

    function fetchContent(url, params) {
        console.log('Fetching content:', url, params);
        fetch(`${url}?${new URLSearchParams(params)}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
            .then(response => {
                console.log('Response received:', response);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.text();
            })
            .then(text => {
                console.log('Raw response:', text);
                try {
                    const data = JSON.parse(text);
                    console.log('Data received:', data);
                    updateContent(data);
                } catch (error) {
                    console.error('Error parsing JSON:', error);
                    console.log('Received non-JSON response.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }

    function updateContent(response) {
        if (moviesList) {
            updateList(moviesList, response.movies, 'movie', response.movie_page, response.movie_total_pages);
        }
        if (showsList) {
            updateList(showsList, response.shows, 'show', response.show_page, response.show_total_pages);
        }
    }

    function updateList(listElement, items, type, currentPage, totalPages) {
        listElement.innerHTML = items.map(item => `
            <li class="bg-gray-800 rounded-md p-3 hover:bg-gray-700 transition duration-150">
                <a href="/${type}s/${item.pk}/" class="text-blue-400 hover:text-blue-300">${item.fields.title}</a>
                <span class="text-gray-400">(${item.fields.year})</span>
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
        attachPaginationListeners(paginationElement);
    }

    function attachPaginationListeners(paginationElement) {
        paginationElement.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', function (event) {
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
    resetButton.addEventListener('click', function (event) {
        event.preventDefault();
        searchInput.value = '';
        fetchContent(window.location.pathname, {});
        history.pushState({}, '', window.location.pathname);
    });

    // Handle form submission
    searchForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const params = new URLSearchParams(new FormData(searchForm));
        fetchContent(window.location.pathname, params);
        history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
    });

    // Attach pagination listeners to existing pagination elements
    document.querySelectorAll('.movie-pagination, .show-pagination').forEach(attachPaginationListeners);

    // Handle browser back/forward buttons
    window.addEventListener('popstate', function (event) {
        fetchContent(window.location.pathname, new URLSearchParams(window.location.search));
    });

    // Only fetch content if there are search parameters or pagination
    if (window.location.search) {
        console.log('Triggering initial load due to search parameters');
        fetchContent(window.location.pathname, new URLSearchParams(window.location.search));
    }
});