document.addEventListener('DOMContentLoaded', function() {
    const getRecommendationsBtn = document.getElementById('getRecommendations');
    const userNameInput = document.getElementById('userName');
    const recommendationsDiv = document.getElementById('recommendations');

    getRecommendationsBtn.addEventListener('click', async function() {
        const userName = userNameInput.value.trim();
        const mood = document.getElementById('mood').value;

        if (!userName) {
            showError('Please enter your name');
            return;
        }

        try {
            const response = await fetch(`/recommend?name=${encodeURIComponent(userName)}&mood=${encodeURIComponent(mood)}`);
            console.log('Response status:', response.status);
            
            const data = await response.json();
            console.log('Data:', data);

            if (response.ok) {
                displayRecommendations(data, userName, mood);
            } else {
                showError(data.error || 'An error occurred');
            }
        } catch (error) {
            console.error('Full error object:', error);
            console.error('Error name:', error.name);
            console.error('Error message:', error.message);
            console.error('Error stack:', error.stack);
            showError('Failed to fetch recommendations: ' + error.message);
        }
    });

    function displayRecommendations(recommendations, userName, mood) {
        console.log('displayRecommendations called with:', recommendations);
        console.log('Type:', typeof recommendations);
        console.log('Is array:', Array.isArray(recommendations));
        
        recommendationsDiv.innerHTML = '';

        if (!Array.isArray(recommendations)) {
            showError('Invalid response format');
            return;
        }

        if (recommendations.length === 0) {
            recommendationsDiv.innerHTML = '<p>No recommendations available.</p>';
            return;
        }

        recommendations.forEach(rec => {
            const recDiv = document.createElement('div');
            recDiv.className = 'recommendation';

            // Create star rating HTML
            const starsHtml = `
                <div class="star-rating" data-item-id="${rec.item_id}">
                    ${[1, 2, 3, 4, 5].map(star => 
                        `<span class="star" data-value="${star}" onclick="giveStarRating('${rec.item_id}', ${star})">★</span>`
                    ).join('')}
                    <span class="rating-text"></span>
                </div>
            `;

            recDiv.innerHTML = `
                <div class="agent-mood">${rec.agent_mood || 'Here\'s a recommendation!'}</div>
                <h3>${rec.title} (${rec.year})</h3>
                <p><strong>Genres:</strong> ${rec.genres || 'N/A'}</p>
                <p><strong>Score:</strong> ${rec.score ? rec.score.toFixed(2) : 'N/A'}</p>
                <p><strong>Reason:</strong> ${rec.reason}</p>
                <p><strong>Description:</strong> ${rec.llm_description || 'No description available'}</p>
                ${starsHtml}
            `;

            recommendationsDiv.appendChild(recDiv);
        });
        
        // Store userName and mood globally
        window.currentUserName = userName;
        window.currentMood = mood;
        
        // Load stats and saved ratings after recommendations
        loadStats(userName);
        loadRatings(userName, mood);
    }

    function showError(message) {
        recommendationsDiv.innerHTML = `<div class="error">${message}</div>`;
    }
});

function loadStats(userName) {
    fetch(`/stats?name=${encodeURIComponent(userName)}`)
        .then(r => r.json())
        .then(data => {
            if (!data.error) {
                document.getElementById('totalFeedback').textContent = data.total_feedback;
                document.getElementById('likedCount').textContent = data.liked_count;
                document.getElementById('dislikedCount').textContent = data.disliked_count;
                document.getElementById('favoriteMood').textContent = data.favorite_mood || '-';
            }
        })
        .catch(e => console.error('Stats error:', e));
}

async function giveStarRating(itemId, rating) {
    const userName = window.currentUserName;
    const mood = window.currentMood;

    if (!userName || !mood) {
        alert('Please get recommendations first');
        return;
    }

    // Visual feedback: highlight stars
    setStarState(itemId, rating);

    try {
        const response = await fetch('/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: userName,
                item_id: itemId,
                rating: rating,
                mood: mood
            })
        });

        const result = await response.json();
        if (response.ok) {
            if (result.status === 'already_rated') {
                alert(`Vec si ocijenio ovaj film s ocjenom ${result.rating}/5`);
                setStarState(itemId, result.rating);
            } else {
                setStarState(itemId, rating);
            }
            loadStats(userName);
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Failed to send feedback');
    }
}

function loadRatings(userName, mood) {
    fetch(`/ratings?name=${encodeURIComponent(userName)}${mood ? `&mood=${encodeURIComponent(mood)}` : ''}`)
        .then(r => r.json())
        .then(data => {
            if (data && Array.isArray(data.ratings)) {
                data.ratings.forEach(r => setStarState(r.item_id, r.rating));
            }
        })
        .catch(err => console.error('loadRatings error:', err));
}

function setStarState(itemId, rating) {
    const starDiv = document.querySelector(`.star-rating[data-item-id="${itemId}"]`);
    if (!starDiv) return;
    const stars = starDiv.querySelectorAll('.star');
    stars.forEach((s, i) => {
        if (i < rating) {
            s.classList.add('active');
        } else {
            s.classList.remove('active');
        }
    });
    const label = ratingLabel(rating);
    starDiv.querySelector('.rating-text').textContent = `${rating}/5 ${label ? '- ' + label : ''}`;
}

function ratingLabel(rating) {
    if (rating <= 2) return 'vise se ne prikazuje';
    if (rating === 3) return 'ok';
    if (rating >= 3.5 && rating < 4) return 'odlican';
    if (rating >= 4) return 'voljeli';
    return '';
}