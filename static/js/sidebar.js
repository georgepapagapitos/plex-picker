// static/js/sidebar.js

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const content = document.querySelector('main');

    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('-translate-x-full');
    });

    // Close sidebar when clicking outside on mobile
    content.addEventListener('click', function() {
        if (window.innerWidth < 1024) {  // 1024px is the 'lg' breakpoint in Tailwind
            sidebar.classList.add('-translate-x-full');
        }
    });

    // Ensure sidebar is visible when resizing to larger screen
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 1024) {
            sidebar.classList.remove('-translate-x-full');
        }
    });
});