// Portfolio Animations Enhancement
// JavaScript for smooth animations on Victor's sports analytics portfolio

class PortfolioAnimations {
  constructor() {
    this.observerOptions = {
      root: null,
      rootMargin: '0px',
      threshold: 0.1
    };
    
    this.scrollObserver = null;
    this.staggerObserver = null;
    this.initialized = false;
  }

  // Initialize all animations
  init() {
    if (this.initialized) return;
    
    console.log('🎨 Initializing portfolio animations...');
    
    // Initialize scroll animations
    this.initScrollAnimations();
    
    // Initialize flip cards
    this.initFlipCards();
    
    // Initialize demo players
    this.initDemoPlayers();
    
    // Initialize chalkboard effects
    this.initChalkboardEffects();
    
    this.initialized = true;
    console.log('✅ Portfolio animations initialized');
  }

  // ===== SCROLL ANIMATIONS =====
  
  initScrollAnimations() {
    // Create Intersection Observer for fade-in animations
    this.scrollObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          
          // Add delay for staggered items
          if (entry.target.classList.contains('stagger-item')) {
            const index = Array.from(entry.target.parentNode.children).indexOf(entry.target);
            entry.target.style.transitionDelay = `${index * 0.1}s`;
          }
        }
      });
    }, this.observerOptions);

    // Observe all elements with animation classes
    document.querySelectorAll('.fade-in-up, .stagger-item').forEach(el => {
      this.scrollObserver.observe(el);
    });
  }

  // ===== FLIP CARD ANIMATIONS =====
  
  initFlipCards() {
    // Add flip functionality to project cards
    document.querySelectorAll('.flip-card').forEach(card => {
      const flipBtn = card.querySelector('.flip-btn');
      const closeBtn = card.querySelector('.close-btn');
      
      if (flipBtn) {
        flipBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          card.classList.add('flipped');
        });
      }
      
      if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          card.classList.remove('flipped');
        });
      }
      
      // Close on click outside (optional)
      card.addEventListener('click', (e) => {
        if (card.classList.contains('flipped') && !e.target.closest('.flip-card-front, .flip-card-back')) {
          card.classList.remove('flipped');
        }
      });
    });
  }

  // ===== DEMO PLAYER CONTROLS =====
  
  initDemoPlayers() {
    document.querySelectorAll('.demo-player').forEach(player => {
      const media = player.querySelector('video, img[data-gif]');
      const playBtn = player.querySelector('.play-btn');
      const pauseBtn = player.querySelector('.pause-btn');
      const progress = player.querySelector('.progress');
      
      if (!media) return;
      
      // Handle GIFs (img elements with data-gif attribute)
      if (media.tagName === 'IMG' && media.dataset.gif) {
        const originalSrc = media.src;
        const gifSrc = media.dataset.gif;
        let isPlaying = false;
        
        if (playBtn) {
          playBtn.addEventListener('click', () => {
            if (!isPlaying) {
              media.src = gifSrc;
              isPlaying = true;
              playBtn.style.display = 'none';
              if (pauseBtn) pauseBtn.style.display = 'block';
            }
          });
        }
        
        if (pauseBtn) {
          pauseBtn.addEventListener('click', () => {
            if (isPlaying) {
              media.src = originalSrc;
              isPlaying = false;
              pauseBtn.style.display = 'none';
              if (playBtn) playBtn.style.display = 'block';
            }
          });
          
          // Hide pause button initially for GIFs
          pauseBtn.style.display = 'none';
        }
      }
      
      // Handle videos
      if (media.tagName === 'VIDEO') {
        if (playBtn) {
          playBtn.addEventListener('click', () => {
            media.play();
            playBtn.style.display = 'none';
            if (pauseBtn) pauseBtn.style.display = 'block';
          });
        }
        
        if (pauseBtn) {
          pauseBtn.addEventListener('click', () => {
            media.pause();
            pauseBtn.style.display = 'none';
            if (playBtn) playBtn.style.display = 'block';
          });
          
          // Update button states based on video events
          media.addEventListener('play', () => {
            playBtn.style.display = 'none';
            if (pauseBtn) pauseBtn.style.display = 'block';
          });
          
          media.addEventListener('pause', () => {
            pauseBtn.style.display = 'none';
            if (playBtn) playBtn.style.display = 'block';
          });
        }
        
        // Update progress bar for videos
        if (progress && media.tagName === 'VIDEO') {
          media.addEventListener('timeupdate', () => {
            const percent = (media.currentTime / media.duration) * 100;
            progress.style.width = `${percent}%`;
          });
        }
      }
    });
  }

  // ===== CHALKBOARD EFFECTS =====
  
  initChalkboardEffects() {
    // Add chalk writing effect to headings
    document.querySelectorAll('h1, h2, .chalk-text').forEach(heading => {
      heading.classList.add('chalk-writing');
      
      // Remove animation after first completion for better performance
      setTimeout(() => {
        heading.style.animation = 'none';
      }, 2000);
    });
  }

  // ===== UTILITY FUNCTIONS =====
  
  // Add fade-in animation to element
  fadeIn(element, delay = 0) {
    element.classList.add('fade-in-up');
    element.style.transitionDelay = `${delay}s`;
    
    // Trigger reflow to ensure animation works
    void element.offsetWidth;
    
    // Observe for scroll
    if (this.scrollObserver) {
      this.scrollObserver.observe(element);
    } else {
      // Fallback: show immediately
      setTimeout(() => {
        element.classList.add('visible');
      }, delay * 1000);
    }
  }

  // Create a loading spinner
  createSpinner(container) {
    const spinner = document.createElement('div');
    spinner.className = 'chalk-spinner';
    spinner.setAttribute('aria-label', 'Loading...');
    container.appendChild(spinner);
    return spinner;
  }

  // Remove loading spinner
  removeSpinner(spinner) {
    if (spinner && spinner.parentNode) {
      spinner.parentNode.removeChild(spinner);
    }
  }

  // ===== CLEANUP =====
  
  destroy() {
    if (this.scrollObserver) {
      this.scrollObserver.disconnect();
    }
    
    if (this.staggerObserver) {
      this.staggerObserver.disconnect();
    }
    
    // Remove event listeners
    document.querySelectorAll('.flip-card, .demo-player').forEach(el => {
      el.replaceWith(el.cloneNode(true));
    });
    
    this.initialized = false;
    console.log('🧹 Portfolio animations cleaned up');
  }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.portfolioAnimations = new PortfolioAnimations();
  window.portfolioAnimations.init();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PortfolioAnimations;
}