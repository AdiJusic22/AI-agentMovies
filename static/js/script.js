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
        
        // Store userName and mood globally for giveFeedback
        window.currentUserName = userName;
        window.currentMood = mood;
    }

    function showError(message) {
        recommendationsDiv.innerHTML = `<div class="error">${message}</div>`;
    }
});

async function giveFeedback(itemId, rating) {
    const userName = window.currentUserName;
    const mood = window.currentMood;

    if (!userName || !mood) {
        alert('Please get recommendations first');
        return;
    }

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
            alert('Feedback recorded! Model updated.');
            // Auto-refresh recommendations after feedback
            document.getElementById('getRecommendations').click();
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Failed to send feedback');
    }
}