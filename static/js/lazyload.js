// static/js/lazyload.js

document.addEventListener("DOMContentLoaded", function() {
    var lazyloadImages = document.querySelectorAll("img.lazyload");
    var lazyloadBackgrounds = document.querySelectorAll(".lazyload-bg");
    
    function lazyload() {
        var scrollTop = window.pageYOffset;
        lazyloadImages.forEach(function(img) {
            if(img.offsetTop < (window.innerHeight + scrollTop)) {
                img.src = img.dataset.src;
                img.classList.remove('lazyload');
            }
        });
        lazyloadBackgrounds.forEach(function(el) {
            if(el.offsetTop < (window.innerHeight + scrollTop)) {
                el.style.backgroundImage = `url('${el.dataset.bg}')`;
                el.classList.remove('lazyload-bg');
            }
        });
        if(lazyloadImages.length == 0 && lazyloadBackgrounds.length == 0) { 
            document.removeEventListener("scroll", lazyload);
            window.removeEventListener("resize", lazyload);
            window.removeEventListener("orientationChange", lazyload);
        }
    }
    
    document.addEventListener("scroll", lazyload);
    window.addEventListener("resize", lazyload);
    window.addEventListener("orientationChange", lazyload);
    lazyload();
});