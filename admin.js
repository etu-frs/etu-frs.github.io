// Admin Dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    // Rich text editor initialization for textareas with class 'rich-editor'
    if (document.querySelectorAll('.rich-editor').length > 0) {
        document.querySelectorAll('.rich-editor').forEach(function(editor) {
            ClassicEditor
                .create(editor, {
                    toolbar: ['heading', '|', 'bold', 'italic', 'link', 'bulletedList', 'numberedList', 'blockQuote'],
                    direction: 'rtl',
                    language: 'ar'
                })
                .then(editor => {
                    console.log('Editor initialized');
                })
                .catch(error => {
                    console.error('Rich text editor error:', error);
                });
        });
    }

    // Image upload preview with progress and save functionality
    const imageInputs = document.querySelectorAll('.image-upload');
    imageInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                const previewContainer = this.closest('.image-preview-container') || this.parentElement;
                const previewElement = previewContainer.querySelector('.image-preview') || previewContainer.querySelector('img');
                const progressElement = previewContainer.querySelector('.upload-progress');
                const progressBarElement = progressElement ? progressElement.querySelector('.upload-progress-bar') : null;
                
                // Create save button if it doesn't exist
                let saveButton = previewContainer.querySelector('.save-image-btn');
                if (!saveButton) {
                    saveButton = document.createElement('button');
                    saveButton.className = 'btn btn-sm btn-success mt-2';
                    saveButton.innerHTML = '<i class="fas fa-save"></i> حفظ الصورة';
                    saveButton.type = 'button';
                    saveButton.classList.add('save-image-btn');
                    
                    // Create progress bar if it doesn't exist
                    if (!progressElement) {
                        const progressDiv = document.createElement('div');
                        progressDiv.className = 'upload-progress mt-2';
                        
                        const progressBar = document.createElement('div');
                        progressBar.className = 'upload-progress-bar';
                        progressDiv.appendChild(progressBar);
                        
                        previewContainer.appendChild(progressDiv);
                    }
                    
                    previewContainer.appendChild(saveButton);
                }
                
                reader.onload = function(e) {
                    if (previewElement) {
                        previewElement.src = e.target.result;
                        previewElement.classList.remove('hidden');
                    }
                    
                    // Set data attribute with file info for later upload
                    saveButton.dataset.imageData = e.target.result;
                    saveButton.dataset.fileName = file.name;
                    
                    // Show the button after preview is loaded
                    saveButton.style.display = 'block';
                };
                
                reader.readAsDataURL(file);
                
                // Add click event to save button
                saveButton.addEventListener('click', function() {
                    const formData = new FormData();
                    formData.append('image', file);
                    formData.append('section', this.dataset.section || 'content');
                    formData.append('key', this.dataset.key || 'image');
                    
                    const progressBar = previewContainer.querySelector('.upload-progress-bar');
                    if (progressBar) {
                        progressBar.style.width = '0%';
                        progressBar.parentElement.style.display = 'block';
                    }
                    
                    saveButton.disabled = true;
                    saveButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> جاري الرفع...';
                    
                    // Create and send XMLHttpRequest to track upload progress
                    const xhr = new XMLHttpRequest();
                    xhr.open('POST', '/api/image/upload', true);
                    
                    xhr.upload.onprogress = function(e) {
                        if (e.lengthComputable && progressBar) {
                            const percentComplete = (e.loaded / e.total) * 100;
                            progressBar.style.width = percentComplete + '%';
                        }
                    };
                    
                    xhr.onload = function() {
                        if (xhr.status === 200) {
                            const response = JSON.parse(xhr.responseText);
                            if (response.success) {
                                // Update image preview with the uploaded image URL if provided
                                if (response.url && previewElement) {
                                    previewElement.src = response.url;
                                }
                                
                                // Show success message
                                const successAlert = document.createElement('div');
                                successAlert.className = 'alert alert-success mt-2';
                                successAlert.innerHTML = 'تم رفع الصورة بنجاح!';
                                previewContainer.appendChild(successAlert);
                                
                                setTimeout(() => {
                                    successAlert.remove();
                                }, 3000);
                                
                                // Hide progress bar
                                if (progressBar && progressBar.parentElement) {
                                    progressBar.parentElement.style.display = 'none';
                                }
                                
                                saveButton.innerHTML = '<i class="fas fa-check"></i> تم الحفظ';
                                setTimeout(() => {
                                    saveButton.innerHTML = '<i class="fas fa-save"></i> حفظ الصورة';
                                    saveButton.disabled = false;
                                }, 2000);
                            } else {
                                handleUploadError(response.message || 'حدث خطأ أثناء رفع الصورة');
                            }
                        } else {
                            handleUploadError('حدث خطأ في الاتصال بالخادم');
                        }
                    };
                    
                    xhr.onerror = function() {
                        handleUploadError('حدث خطأ في الاتصال بالخادم');
                    };
                    
                    function handleUploadError(message) {
                        const errorAlert = document.createElement('div');
                        errorAlert.className = 'alert alert-danger mt-2';
                        errorAlert.textContent = message;
                        previewContainer.appendChild(errorAlert);
                        
                        setTimeout(() => {
                            errorAlert.remove();
                        }, 3000);
                        
                        // Reset button
                        saveButton.innerHTML = '<i class="fas fa-save"></i> حفظ الصورة';
                        saveButton.disabled = false;
                        
                        // Hide progress bar
                        if (progressBar && progressBar.parentElement) {
                            progressBar.parentElement.style.display = 'none';
                        }
                    }
                    
                    xhr.send(formData);
                });
            }
        });
    });

    // AJAX form submissions
    const ajaxForms = document.querySelectorAll('form[data-ajax="true"]');
    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            const actionUrl = this.getAttribute('action');
            
            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> جارٍ المعالجة...';
            
            fetch(actionUrl, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                // Show alert based on response
                const alertDiv = document.createElement('div');
                alertDiv.className = data.success 
                    ? 'alert alert-success' 
                    : 'alert alert-danger';
                alertDiv.textContent = data.message;
                
                const alertContainer = document.querySelector('.alert-container');
                alertContainer.innerHTML = '';
                alertContainer.appendChild(alertDiv);
                
                // Reset form if successful
                if (data.success) {
                    form.reset();
                    
                    // If there's a redirect URL, navigate after delay
                    if (data.redirect) {
                        setTimeout(() => {
                            window.location.href = data.redirect;
                        }, 1000);
                    }
                }
                
                // Reset button state
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
                
                // Auto-hide alert after 4 seconds
                setTimeout(() => {
                    alertDiv.classList.add('fade');
                    setTimeout(() => alertDiv.remove(), 500);
                }, 4000);
            })
            .catch(error => {
                console.error('Error submitting form:', error);
                
                // Show error alert
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-danger';
                alertDiv.textContent = 'حدث خطأ في النظام. يرجى المحاولة مرة أخرى.';
                
                const alertContainer = document.querySelector('.alert-container');
                alertContainer.innerHTML = '';
                alertContainer.appendChild(alertDiv);
                
                // Reset button state
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            });
        });
    });

    // Live content editing
    const liveEditElements = document.querySelectorAll('[data-live-edit="true"]');
    liveEditElements.forEach(element => {
        element.addEventListener('click', function() {
            if (this.getAttribute('data-editing') === 'true') return;
            
            const originalContent = this.innerHTML;
            const sectionId = this.getAttribute('data-section-id');
            const contentKey = this.getAttribute('data-key');
            
            // Create and configure edit field
            const editField = document.createElement('textarea');
            editField.className = 'form-control text-right';
            editField.style.direction = 'rtl';
            editField.value = this.textContent.trim();
            editField.rows = 3;
            
            // Replace element with edit field
            this.innerHTML = '';
            this.appendChild(editField);
            this.setAttribute('data-editing', 'true');
            
            // Focus the textarea
            editField.focus();
            
            // Create save/cancel buttons
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'mt-2 text-left';
            
            const saveButton = document.createElement('button');
            saveButton.className = 'btn btn-sm btn-success ml-2';
            saveButton.textContent = 'حفظ';
            
            const cancelButton = document.createElement('button');
            cancelButton.className = 'btn btn-sm btn-secondary';
            cancelButton.textContent = 'إلغاء';
            
            buttonContainer.appendChild(saveButton);
            buttonContainer.appendChild(cancelButton);
            this.appendChild(buttonContainer);
            
            // Cancel button handler
            cancelButton.addEventListener('click', function() {
                element.innerHTML = originalContent;
                element.removeAttribute('data-editing');
            });
            
            // Save button handler
            saveButton.addEventListener('click', function() {
                const newValue = editField.value.trim();
                
                // Show loading spinner
                buttonContainer.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="sr-only">جارٍ الحفظ...</span></div>';
                
                // Send AJAX request to update content
                fetch('/api/content/update', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        section_id: sectionId,
                        key: contentKey,
                        value: newValue
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update the element with new content
                        element.innerHTML = newValue;
                        element.removeAttribute('data-editing');
                        
                        // Show success notification
                        const notification = document.createElement('div');
                        notification.className = 'alert alert-success alert-dismissible fade show position-fixed';
                        notification.style.top = '20px';
                        notification.style.right = '20px';
                        notification.style.zIndex = '9999';
                        notification.innerHTML = `
                            <strong>نجاح!</strong> ${data.message}
                            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        `;
                        
                        document.body.appendChild(notification);
                        
                        // Auto-remove notification after 3 seconds
                        setTimeout(() => {
                            notification.remove();
                        }, 3000);
                    } else {
                        // Restore original content on error
                        element.innerHTML = originalContent;
                        element.removeAttribute('data-editing');
                        
                        // Show error alert
                        alert('خطأ: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error updating content:', error);
                    element.innerHTML = originalContent;
                    element.removeAttribute('data-editing');
                    alert('حدث خطأ في النظام. يرجى المحاولة مرة أخرى.');
                });
            });
        });
    });
    
    // Handle image upload via base64
    const profileImageElement = document.getElementById('profileImageUpload');
    if (profileImageElement) {
        profileImageElement.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const base64Data = e.target.result;
                    
                    // Send base64 image to server
                    fetch('/api/image/upload_base64', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            image: base64Data,
                            section: 'about',
                            key: 'profile_image'
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Update profile image
                            const previewElement = document.getElementById('profileImagePreview');
                            if (previewElement) {
                                previewElement.src = data.url;
                                previewElement.classList.remove('hidden');
                            }
                            
                            // Show success message
                            alert(data.message);
                        } else {
                            alert('خطأ: ' + data.message);
                        }
                    })
                    .catch(error => {
                        console.error('Error uploading image:', error);
                        alert('حدث خطأ في النظام. يرجى المحاولة مرة أخرى.');
                    });
                };
                reader.readAsDataURL(file);
            }
        });
    }
});

// Function to detect the admin shortcut (Ctrl+Shift+Alt+A)
let keysPressed = {};
document.addEventListener('keydown', function(e) {
    keysPressed[e.key] = true;
    
    // Check for Ctrl+Shift+Alt+A
    if (keysPressed['Control'] && keysPressed['Shift'] && keysPressed['Alt'] && keysPressed['a']) {
        const adminLink = document.getElementById('adminLink');
        if (adminLink) {
            adminLink.classList.remove('hidden');
            
            // Scroll to the admin link
            adminLink.scrollIntoView({ behavior: 'smooth' });
            
            // Flash the admin link to make it more visible
            let flashCount = 0;
            const flashInterval = setInterval(() => {
                adminLink.classList.toggle('bg-yellow-400');
                adminLink.classList.toggle('text-black');
                flashCount++;
                
                if (flashCount >= 6) {
                    clearInterval(flashInterval);
                    adminLink.classList.add('bg-yellow-400');
                    adminLink.classList.add('text-black');
                }
            }, 300);
        }
    }
});

document.addEventListener('keyup', function(e) {
    delete keysPressed[e.key];
});
