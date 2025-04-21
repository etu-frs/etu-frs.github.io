/**
 * Portfolio items functionality for viewing, liking, and commenting
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle portfolio item viewing
    const portfolioItems = document.querySelectorAll('.gallery-item');
    if (portfolioItems.length > 0) {
        portfolioItems.forEach(item => {
            item.addEventListener('click', function() {
                const portfolioId = this.dataset.id;
                if (portfolioId) {
                    incrementViewCount(portfolioId);
                }
            });
        });
    }

    // Handle like button clicks
    const likeButtons = document.querySelectorAll('.like-btn');
    if (likeButtons.length > 0) {
        likeButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const portfolioId = this.dataset.id;
                if (portfolioId) {
                    toggleLike(portfolioId, this);
                }
            });
        });
    }

    // Handle comment button clicks to open comment modal
    const commentButtons = document.querySelectorAll('.comment-btn');
    if (commentButtons.length > 0) {
        commentButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const portfolioId = this.dataset.id;
                if (portfolioId) {
                    // Set portfolio ID in the modal
                    document.getElementById('portfolio-id-input').value = portfolioId;
                    
                    // Open comment modal
                    document.getElementById('comment-modal').classList.remove('hidden');
                    
                    // Load existing comments for this portfolio item
                    loadComments(portfolioId, document.getElementById('comments-container'));
                }
            });
        });
    }

    // Close comment modal when close button or overlay is clicked
    const modalCloseBtn = document.querySelector('.modal-close');
    const modalOverlay = document.querySelector('.modal-overlay');
    
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', function() {
            document.getElementById('comment-modal').classList.add('hidden');
        });
    }
    
    if (modalOverlay) {
        modalOverlay.addEventListener('click', function(e) {
            if (e.target === this) {
                document.getElementById('comment-modal').classList.add('hidden');
            }
        });
    }

    // Handle comment form submission
    const commentForm = document.getElementById('comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const portfolioId = document.getElementById('portfolio-id-input').value;
            submitComment(portfolioId, this);
        });
    }

    // Initialize: update all view counts when page loads
    portfolioItems.forEach(item => {
        const portfolioId = item.dataset.id;
        if (portfolioId) {
            // Get view counts for all portfolio items
            fetch(`/api/portfolio/${portfolioId}/view`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const viewCountEl = document.querySelector(`.view-count[data-id="${portfolioId}"]`);
                    if (viewCountEl) {
                        viewCountEl.textContent = data.views_count;
                    }
                }
            })
            .catch(error => console.error('Error updating view count:', error));
        }
    });
});

/**
 * Increment the view count for a portfolio item
 * @param {number} portfolioId - Portfolio item ID
 */
function incrementViewCount(portfolioId) {
    fetch(`/api/portfolio/${portfolioId}/view`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const viewCountEl = document.querySelector(`.view-count[data-id="${portfolioId}"]`);
            if (viewCountEl) {
                viewCountEl.textContent = data.views_count;
            }
        }
    })
    .catch(error => console.error('Error updating view count:', error));
}

/**
 * Toggle like for a portfolio item
 * @param {number} portfolioId - Portfolio item ID
 * @param {HTMLElement} button - The like button element
 */
function toggleLike(portfolioId, button) {
    fetch(`/api/portfolio/${portfolioId}/like`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const likeCountEl = document.querySelector(`.like-count[data-id="${portfolioId}"]`);
            if (likeCountEl) {
                likeCountEl.textContent = data.likes_count;
            }
            
            // Update like button appearance
            if (data.liked) {
                button.classList.add('liked');
                button.querySelector('i').classList.remove('far');
                button.querySelector('i').classList.add('fas');
            } else {
                button.classList.remove('liked');
                button.querySelector('i').classList.remove('fas');
                button.querySelector('i').classList.add('far');
            }
        }
    })
    .catch(error => console.error('Error updating like status:', error));
}

/**
 * Load comments for a portfolio item
 * @param {number} portfolioId - Portfolio item ID
 * @param {HTMLElement} container - Comment container element
 */
function loadComments(portfolioId, container) {
    const commentsContainer = document.getElementById('comments-list');
    if (!commentsContainer) return;
    
    fetch(`/api/portfolio/${portfolioId}/comments`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const comments = data.comments;
            
            if (comments.length === 0) {
                commentsContainer.innerHTML = '<div class="text-center p-4 text-gray-400">لا توجد تعليقات بعد. كن أول من يعلق!</div>';
                return;
            }
            
            commentsContainer.innerHTML = '';
            comments.forEach(comment => {
                const commentEl = document.createElement('div');
                commentEl.className = 'border-b border-gray-700 p-4 last:border-0';
                commentEl.innerHTML = `
                    <div class="flex justify-between mb-2">
                        <strong class="font-bold text-white">${comment.name}</strong>
                        <span class="text-gray-400 text-sm">${comment.created_at}</span>
                    </div>
                    <div class="text-gray-300">${comment.content}</div>
                `;
                commentsContainer.appendChild(commentEl);
            });
            
            // Update comment count
            const commentCountEl = document.querySelector(`.comment-count[data-id="${portfolioId}"]`);
            if (commentCountEl) {
                commentCountEl.textContent = comments.length;
            }
        }
    })
    .catch(error => console.error('Error loading comments:', error));
}

/**
 * Submit a new comment
 * @param {number} portfolioId - Portfolio item ID
 * @param {HTMLFormElement} form - Comment form element
 */
function submitComment(portfolioId, form) {
    const nameInput = form.querySelector('input[name="name"]');
    const emailInput = form.querySelector('input[name="email"]');
    const contentInput = form.querySelector('textarea[name="content"]');
    
    if (!nameInput || !contentInput) return;
    
    const name = nameInput.value.trim();
    const email = emailInput ? emailInput.value.trim() : '';
    const content = contentInput.value.trim();
    
    if (!name || !content) {
        showFormMessage(form, 'يرجى تعبئة جميع الحقول المطلوبة', 'error');
        return;
    }
    
    fetch(`/api/portfolio/${portfolioId}/comments`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name,
            email,
            content
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear form
            nameInput.value = '';
            if (emailInput) emailInput.value = '';
            contentInput.value = '';
            
            // Show success message
            showFormMessage(form, data.message, 'success');
            
            // Hide modal after submission
            setTimeout(() => {
                document.getElementById('comment-modal').classList.add('hidden');
            }, 3000);
        } else {
            showFormMessage(form, data.message || 'حدث خطأ أثناء إرسال التعليق', 'error');
        }
    })
    .catch(error => {
        console.error('Error submitting comment:', error);
        showFormMessage(form, 'حدث خطأ في النظام', 'error');
    });
}

/**
 * Show a message in the form
 * @param {HTMLFormElement} form - Comment form element
 * @param {string} message - Message to display
 * @param {string} type - Message type: 'success' or 'error'
 */
function showFormMessage(form, message, type) {
    const formMessage = document.getElementById('form-message');
    if (!formMessage) return;
    
    formMessage.textContent = message;
    formMessage.className = `mt-4 p-2 rounded ${type === 'success' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`;
    
    // Make sure form message is visible
    formMessage.classList.remove('hidden');
    
    // Clear message after a delay for success messages
    if (type === 'success') {
        setTimeout(() => {
            formMessage.textContent = '';
            formMessage.classList.add('hidden');
        }, 5000);
    }
}