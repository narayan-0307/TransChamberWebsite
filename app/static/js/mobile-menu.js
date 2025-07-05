document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.querySelector('.tp-mobile-menu-toggle');
    const offcanvasMenu = document.querySelector('.tp-offcanvas-menu');
    const offcanvasOverlay = document.querySelector('.tp-offcanvas-overlay');
    const offcanvasClose = document.querySelector('.tp-offcanvas-close');
    const submenuToggles = document.querySelectorAll('.tp-offcanvas-menu .has-dropdown > a');

    // Toggle mobile menu
    function toggleMobileMenu() {
        offcanvasMenu.classList.toggle('active');
        offcanvasOverlay.classList.toggle('active');
        document.body.style.overflow = offcanvasMenu.classList.contains('active') ? 'hidden' : '';
    }

    // Toggle submenu
    function toggleSubmenu(e) {
        e.preventDefault();
        const submenu = this.nextElementSibling;
        const parentLi = this.parentElement;

        parentLi.classList.toggle('active');
        submenu.classList.toggle('active');

        // Toggle submenu height for smooth animation
        if (submenu.classList.contains('active')) {
            submenu.style.maxHeight = submenu.scrollHeight + 'px';
        } else {
            submenu.style.maxHeight = '0';
        }
    }

    // Event listeners
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', toggleMobileMenu);
    }

    if (offcanvasClose) {
        offcanvasClose.addEventListener('click', toggleMobileMenu);
    }

    if (offcanvasOverlay) {
        offcanvasOverlay.addEventListener('click', toggleMobileMenu);
    }

    // Add click event to all submenu toggles
    submenuToggles.forEach(toggle => {
        toggle.addEventListener('click', toggleSubmenu);
    });

    // Close mobile menu on window resize if screen becomes larger than mobile breakpoint
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 1200 && offcanvasMenu.classList.contains('active')) {
            toggleMobileMenu();
        }
    });
});