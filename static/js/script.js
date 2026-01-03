document.addEventListener('DOMContentLoaded', function() {
    const getRecommendationsBtn = document.getElementById('getRecommendations');
    const newSessionBtn = document.getElementById('newSession');
    const userIdInput = document.getElementById('userId');
    const sessionIdInput = document.getElementById('sessionId');
    const recommendationsDiv = document.getElementById('recommendations');

    newSessionBtn.addEventListener('click', function() {
        const randomId = 'session' + Math.random().toString(36).substr(2, 9);
        sessionIdInput.value = randomId;
    });

    getRecommendationsBtn.addEventListener('click', async function() {
        const userId = userIdInput.value.trim();
        const sessionId = sessionIdInput.value.trim();
        const mood = document.getElementById('mood').value;

        if (!userId || !sessionId) {
            showError('Please enter both User ID and Session ID');
            return;
        }

        try {
            const response = await fetch(`/recommend?user_id=${encodeURIComponent(userId)}&session_id=${encodeURIComponent(sessionId)}&mood=${encodeURIComponent(mood)}`);
            const data = await response.json();

            if (response.ok) {
                displayRecommendations(data);
            } else {
                showError(data.error || 'An error occurred');
            }
        } catch (error) {
            showError('Failed to fetch recommendations');
        }
    });

    function displayRecommendations(recommendations) {
        recommendationsDiv.innerHTML = '';

        if (recommendations.length === 0) {
            recommendationsDiv.innerHTML = '<p>No recommendations available.</p>';
            return;
        }

        recommendations.forEach(rec => {
            const recDiv = document.createElement('div');
            recDiv.className = 'recommendation';

            recDiv.innerHTML = `
                <div class="agent-mood">${rec.agent_mood || 'Here\'s a recommendation!'}</div>
                <h3>${rec.title} (${rec.year})</h3>
                <p><strong>Genres:</strong> ${rec.genres || 'N/A'}</p>
                <p><strong>Score:</strong> ${rec.score ? rec.score.toFixed(2) : 'N/A'}</p>
                <p><strong>Reason:</strong> ${rec.reason}</p>
                <p><strong>Description:</strong> ${rec.llm_description || 'No description available'}</p>
                <div class="feedback-buttons">
                    <button class="like-btn" onclick="giveFeedback('${rec.item_id}', 5)">Like</button>
                    <button class="dislike-btn" onclick="giveFeedback('${rec.item_id}', 1)">Dislike</button>
                </div>
            `;

            recommendationsDiv.appendChild(recDiv);
        });
    }

    function showError(message) {
        recommendationsDiv.innerHTML = `<div class="error">${message}</div>`;
    }
});

async function giveFeedback(itemId, rating) {
    const userId = document.getElementById('userId').value.trim();
    const sessionId = document.getElementById('sessionId').value.trim();

    if (!userId || !sessionId) {
        alert('Please enter User ID and Session ID first');
        return;
    }

    try {
        const response = await fetch('/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                item_id: itemId,
                rating: rating,
                session_id: sessionId
            })
        });

        const result = await response.json();
        if (response.ok) {
            alert('Feedback recorded! Model updated.');
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Failed to send feedback');
    }
}