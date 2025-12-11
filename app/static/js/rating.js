// Rating Form Handler
document.addEventListener('DOMContentLoaded', function() {
    const ratingForm = document.getElementById('rating-form');
    const starRating = document.getElementById('star-rating');
    const ratingDisplay = document.getElementById('rating-display');
    const recentRatingsContainer = document.getElementById('recent-ratings');
    
    // Star rating interaction
    if (starRating) {
        const stars = starRating.querySelectorAll('input[type="radio"]');
        stars.forEach(star => {
            star.addEventListener('change', function() {
                const value = this.value;
                const emoji = getRatingEmoji(parseInt(value));
                ratingDisplay.innerHTML = `${value} ${value === '1' ? 'Star' : 'Stars'} ${emoji}`;
            });
        });
    }
    
    // Form submission
    if (ratingForm) {
        ratingForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const submitBtn = event.target.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerText;
            
            // Show loading state
            submitBtn.innerText = 'Submitting...';
            submitBtn.disabled = true;
            
            fetch('/rating/submit', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    Swal.fire({
                        title: 'Thank You!',
                        text: data.message,
                        icon: 'success',
                        background: '#050510',
                        color: '#fff',
                        confirmButtonColor: '#2979ff'
                    });
                    event.target.reset();
                    ratingDisplay.innerHTML = '';
                    loadRecentRatings(); // Refresh the ratings list
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: data.message,
                        icon: 'error',
                        background: '#050510',
                        color: '#fff'
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    title: 'Error',
                    text: 'An error occurred. Please try again.',
                    icon: 'error',
                    background: '#050510',
                    color: '#fff'
                });
            })
            .finally(() => {
                submitBtn.innerText = originalText;
                submitBtn.disabled = false;
            });
        });
    }
    
    // Load recent ratings
    loadRecentRatings();
});

function getRatingEmoji(rating) {
    const emojis = {
        5: '<span class="rating-emoji">🤩</span>',
        4: '<span class="rating-emoji">😊</span>',
        3: '<span class="rating-emoji">🙂</span>',
        2: '<span class="rating-emoji">😐</span>',
        1: '<span class="rating-emoji">😞</span>'
    };
    return emojis[rating] || '';
}

function getStarsHTML(rating) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        stars += i <= rating ? '★' : '☆';
    }
    return stars;
}

function loadRecentRatings() {
    const container = document.getElementById('recent-ratings');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading reviews</div>';
    
    fetch('/rating/all')
        .then(response => response.json())
        .then(data => {
            if (data.ratings && data.ratings.length > 0) {
                container.innerHTML = '';
                data.ratings.forEach(rating => {
                    const card = createRatingCard(rating);
                    container.appendChild(card);
                });
            } else {
                container.innerHTML = '<div class="text-center" style="color: rgba(255,255,255,0.6); padding: 40px;">No reviews yet. Be the first to rate us!</div>';
            }
        })
        .catch(error => {
            console.error('Error loading ratings:', error);
            container.innerHTML = '<div class="text-center" style="color: rgba(255,255,255,0.6);">Unable to load reviews</div>';
        });
}

function createRatingCard(rating) {
    const card = document.createElement('div');
    card.className = 'rating-card';
    
    card.innerHTML = `
        <div class="rating-card-header">
            <div class="rating-card-name">${escapeHtml(rating.name)}</div>
            <div class="rating-card-stars">${getStarsHTML(rating.rating)}</div>
        </div>
        <div class="rating-card-message">${escapeHtml(rating.message)}</div>
        <div class="rating-card-date">${rating.date}</div>
    `;
    
    return card;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
