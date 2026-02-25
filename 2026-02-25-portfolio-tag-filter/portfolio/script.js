// Mobile navigation toggle
const navToggle = document.querySelector('.nav-toggle');
const navMenu = document.querySelector('.nav-menu');

if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => {
        const isExpanded = navToggle.getAttribute('aria-expanded') === 'true';
        navToggle.setAttribute('aria-expanded', !isExpanded);
        navToggle.classList.toggle('active');
        navMenu.classList.toggle('active');
    });

    // Close menu when clicking a link
    navMenu.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            navToggle.classList.remove('active');
            navMenu.classList.remove('active');
            navToggle.setAttribute('aria-expanded', 'false');
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
            navToggle.classList.remove('active');
            navMenu.classList.remove('active');
            navToggle.setAttribute('aria-expanded', 'false');
        }
    });
}

// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const navHeight = document.querySelector('.nav')?.offsetHeight || 0;
            const targetPosition = target.getBoundingClientRect().top + window.scrollY - navHeight - 20;
            
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// Active navigation state on scroll
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-link[href^="#"]');

function updateActiveNav() {
    const scrollPosition = window.scrollY + 150;

    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.offsetHeight;
        const sectionId = section.getAttribute('id');

        if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${sectionId}`) {
                    link.classList.add('active');
                }
            });
        }
    });
}

// Throttle scroll events
let scrollTimeout;
window.addEventListener('scroll', () => {
    if (scrollTimeout) return;
    scrollTimeout = setTimeout(() => {
        updateActiveNav();
        scrollTimeout = null;
    }, 100);
});

window.addEventListener('load', updateActiveNav);

// Intersection Observer for reveal animations
const observerOptions = {
    threshold: 0.12,
    rootMargin: '0px 0px -80px 0px'
};

const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            revealObserver.unobserve(entry.target);
        }
    });
}, observerOptions);

// Apply initial state and observe reveal elements
document.addEventListener('DOMContentLoaded', () => {
    const revealItems = document.querySelectorAll('.reveal, .project-card');

    revealItems.forEach((item, index) => {
        const delay = item.classList.contains('project-card') ? index * 0.08 : 0;
        item.style.transitionDelay = `${delay}s`;
        revealObserver.observe(item);
    });

    // Add lazy loading for GIFs (pause until in view)
    const gifImages = document.querySelectorAll('img[src$=\".gif\"]');
    const gifObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                // Force reload to start animation when visible
                const src = img.src;
                img.src = '';
                img.src = src;
                gifObserver.unobserve(img);
            }
        });
    }, { threshold: 0.1 });

    gifImages.forEach(img => gifObserver.observe(img));
});

// Reduce motion preference
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.querySelectorAll('.reveal, .project-card').forEach(item => {
        item.classList.add('visible');
        item.style.transition = 'none';
        item.style.transitionDelay = '0s';
    });
}

// Keyboard navigation for mobile menu
navToggle?.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && navMenu.classList.contains('active')) {
        navToggle.classList.remove('active');
        navMenu.classList.remove('active');
        navToggle.setAttribute('aria-expanded', 'false');
        navToggle.focus();
    }
});

// Subtle parallax for hero background
const heroBg = document.querySelector('.hero-bg');
let heroTicking = false;

function updateHeroParallax() {
    if (!heroBg) return;
    const scrollY = window.scrollY || 0;
    heroBg.style.transform = `translate3d(0, ${scrollY * 0.2}px, 0)`;
    heroTicking = false;
}

window.addEventListener('scroll', () => {
    if (!heroBg || heroTicking) return;
    heroTicking = true;
    window.requestAnimationFrame(updateHeroParallax);
});

window.addEventListener('load', updateHeroParallax);

// Portfolio tag filtering
(function() {
    'use strict';

    // Wait for DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFilter);
    } else {
        initFilter();
    }

    function initFilter() {
        const projectCards = document.querySelectorAll('.project-card');
        const filterContainer = document.querySelector('.projects-filter');
        if (!projectCards.length || !filterContainer) return;

        const allTags = new Set();
        const cardTagMap = new Map(); // card -> array of tag strings

        // Extract tags from each card
        projectCards.forEach(card => {
            const tagElements = card.querySelectorAll('.tag');
            const tags = Array.from(tagElements).map(el => el.textContent.trim());
            cardTagMap.set(card, tags);
            tags.forEach(tag => allTags.add(tag));
        });

        // Create tag buttons
        const sortedTags = Array.from(allTags).sort();
        sortedTags.forEach(tag => {
            const button = document.createElement('button');
            button.className = 'filter-btn';
            button.setAttribute('data-filter', tag);
            button.textContent = tag;
            filterContainer.appendChild(button);
        });

        // Filter function
        function filterProjects(selectedTag) {
            const isAll = selectedTag === 'all';
            projectCards.forEach(card => {
                const tags = cardTagMap.get(card) || [];
                const shouldShow = isAll || tags.includes(selectedTag);
                card.style.display = shouldShow ? '' : 'none';
                // Trigger reveal animation if needed
                if (shouldShow && !card.classList.contains('visible')) {
                    card.classList.add('visible');
                }
            });

            // Update active button
            filterContainer.querySelectorAll('.filter-btn').forEach(btn => {
                const btnTag = btn.getAttribute('data-filter');
                const isActive = (isAll && btnTag === 'all') || (!isAll && btnTag === selectedTag);
                btn.classList.toggle('active', isActive);
            });
        }

        // Event delegation for filter buttons
        filterContainer.addEventListener('click', event => {
            const button = event.target.closest('.filter-btn');
            if (!button) return;
            const tag = button.getAttribute('data-filter');
            filterProjects(tag);
        });

        // Ensure 'All' button is active initially
        const allButton = filterContainer.querySelector('.filter-btn[data-filter="all"]');
        if (allButton) {
            allButton.classList.add('active');
        }

        // Preload data-tags attribute for CSS fallback (optional)
        projectCards.forEach(card => {
            const tags = cardTagMap.get(card) || [];
            card.setAttribute('data-tags', tags.join(' '));
        });
    }
})();
