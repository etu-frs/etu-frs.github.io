document.addEventListener('DOMContentLoaded', function() {
    // Initialize ratings display
    const renderRatingStars = function(rating) {
        let starsHtml = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= rating) {
                starsHtml += '<i class="fas fa-star text-yellow-400"></i>';
            } else {
                starsHtml += '<i class="far fa-star text-gray-400"></i>';
            }
        }
        return starsHtml;
    };
    
    document.querySelectorAll('.rating-display').forEach(function(element) {
        const rating = parseInt(element.dataset.rating || 5);
        element.innerHTML = renderRatingStars(rating);
    });
    
    // Rating selection in testimonial form
    const testimonialForm = document.getElementById('testimonialForm');
    if (testimonialForm) {
        const ratingInput = testimonialForm.querySelector('input[name="rating"]');
        const ratingStars = testimonialForm.querySelectorAll('.rating-star');
        
        ratingStars.forEach(function(star) {
            star.addEventListener('click', function() {
                const value = parseInt(this.dataset.value);
                ratingInput.value = value;
                
                // Update the visual display
                ratingStars.forEach(function(s, index) {
                    if (index < value) {
                        s.classList.remove('far');
                        s.classList.add('fas');
                        s.classList.add('text-yellow-400');
                    } else {
                        s.classList.remove('fas');
                        s.classList.remove('text-yellow-400');
                        s.classList.add('far');
                    }
                });
            });
        });
        
        // Submit testimonial form via AJAX
        testimonialForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            
            // Validate form
            const name = formData.get('name');
            const content = formData.get('content');
            
            if (!name || !content) {
                alert('يرجى تعبئة جميع الحقول المطلوبة');
                return;
            }
            
            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> جارٍ الإرسال...';
            
            fetch('/api/testimonial/add', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Create alert
                const alertEl = document.createElement('div');
                alertEl.className = data.success 
                    ? 'alert alert-success mb-4 text-right' 
                    : 'alert alert-danger mb-4 text-right';
                alertEl.textContent = data.message;
                
                // Insert alert before form
                testimonialForm.parentNode.insertBefore(alertEl, testimonialForm);
                
                // Reset form if successful
                if (data.success) {
                    testimonialForm.reset();
                    
                    // Hide form after successful submission
                    setTimeout(() => {
                        testimonialForm.style.display = 'none';
                    }, 1000);
                }
                
                // Reset button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
                
                // Auto-hide alert after 5 seconds
                setTimeout(() => {
                    alertEl.classList.add('fade');
                    setTimeout(() => alertEl.remove(), 500);
                }, 5000);
            })
            .catch(error => {
                console.error('Error submitting testimonial:', error);
                
                // Create error alert
                const alertEl = document.createElement('div');
                alertEl.className = 'alert alert-danger mb-4 text-right';
                alertEl.textContent = 'حدث خطأ في النظام. يرجى المحاولة مرة أخرى لاحقاً.';
                
                // Insert alert before form
                testimonialForm.parentNode.insertBefore(alertEl, testimonialForm);
                
                // Reset button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            });
        });
    }
    
    // Testimonial carousel functionality
    const testimonialContainer = document.querySelector('.testimonials-container');
    if (testimonialContainer) {
        const testimonials = testimonialContainer.querySelectorAll('.testimonial-card');
        const prevBtn = document.getElementById('prevTestimonial');
        const nextBtn = document.getElementById('nextTestimonial');
        
        let currentIndex = 0;
        const maxIndex = Math.max(0, testimonials.length - 1);
        
        // Function to update which testimonials are visible
        const updateTestimonials = function() {
            testimonials.forEach((testimonial, index) => {
                if (window.innerWidth >= 768) {
                    // On desktop show 3 at a time if available
                    if (index >= currentIndex && index < currentIndex + 3 && index < testimonials.length) {
                        testimonial.classList.remove('hidden');
                    } else {
                        testimonial.classList.add('hidden');
                    }
                } else {
                    // On mobile show only 1
                    if (index === currentIndex) {
                        testimonial.classList.remove('hidden');
                    } else {
                        testimonial.classList.add('hidden');
                    }
                }
            });
            
            // Update button states
            if (prevBtn && nextBtn) {
                prevBtn.disabled = currentIndex === 0;
                nextBtn.disabled = (window.innerWidth >= 768) 
                    ? (currentIndex + 3 >= testimonials.length)
                    : (currentIndex >= maxIndex);
            }
        };
        
        // Initialize
        updateTestimonials();
        
        // Handle window resize
        window.addEventListener('resize', updateTestimonials);
        
        // Button handlers
        if (prevBtn) {
            prevBtn.addEventListener('click', function() {
                if (currentIndex > 0) {
                    currentIndex--;
                    updateTestimonials();
                }
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', function() {
                const step = window.innerWidth >= 768 ? 3 : 1;
                if (currentIndex + step < testimonials.length) {
                    currentIndex++;
                    updateTestimonials();
                }
            });
        }
        
        // Auto-rotate testimonials every 5 seconds if more than 3
        if (testimonials.length > 3) {
            setInterval(() => {
                const step = window.innerWidth >= 768 ? 3 : 1;
                if (currentIndex + step < testimonials.length) {
                    currentIndex++;
                } else {
                    currentIndex = 0;
                }
                updateTestimonials();
            }, 5000);
        }
    }
});
