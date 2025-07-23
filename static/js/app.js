// UPSC Mock Exam Application JavaScript
class ExamApp {
    constructor() {
        // Check if this is a fresh start from index page
        const urlParams = new URLSearchParams(window.location.search);
        const isNewSession = urlParams.has('new') || window.location.pathname === '/exam' && !localStorage.getItem('examAnswers');
        
        if (isNewSession) {
            // Clear any existing data for fresh start
            localStorage.removeItem('examAnswers');
            localStorage.removeItem('markedForReview');
            localStorage.removeItem('examTimeLeft');
            console.log('Starting fresh exam session - cleared localStorage');
        }
        
        this.timeLeft = 10800; // 180 minutes in seconds (3 hours)
        this.timer = null;
        this.startTime = new Date();
        this.answers = JSON.parse(localStorage.getItem('examAnswers')) || {};
        this.markedForReview = new Set(JSON.parse(localStorage.getItem('markedForReview')) || []);
        this.currentQuestion = this.getCurrentQuestionFromPage();
        this.totalQuestions = this.getTotalQuestionsFromPage();
        this.isSubmitted = false;
        
        // Load saved timer state if available
        const savedTimeLeft = localStorage.getItem('examTimeLeft');
        if (savedTimeLeft && !isNewSession) {
            this.timeLeft = parseInt(savedTimeLeft);
            console.log('Restored timer from localStorage:', this.timeLeft);
        } else {
            console.log('Starting with fresh timer: 3 hours');
        }
        
        this.initializeApp();
    }

    getCurrentQuestionFromPage() {
        const container = document.querySelector('[data-current-question]');
        if (container) {
            const questionNum = parseInt(container.getAttribute('data-current-question'));
            console.log('Question from container:', questionNum);
            return questionNum;
        }
        // Fallback: get from URL
        const urlParams = new URLSearchParams(window.location.search);
        const questionFromURL = parseInt(urlParams.get('q')) || parseInt(urlParams.get('question')) || 1;
        console.log('Question from URL:', questionFromURL);
        return questionFromURL;
    }

    getTotalQuestionsFromPage() {
        const container = document.querySelector('[data-total-questions]');
        if (container) {
            return parseInt(container.getAttribute('data-total-questions'));
        }
        const totalQuestionsInput = document.getElementById('totalQuestions');
        return totalQuestionsInput ? parseInt(totalQuestionsInput.value) : 100;
    }

    initializeApp() {
        console.log('Initializing Exam App...');
        console.log('Current Question:', this.currentQuestion);
        console.log('Total Questions:', this.totalQuestions);
        console.log('Time Left:', this.timeLeft, 'seconds');
        
        // Verify essential elements exist
        const timerElement = document.getElementById('timer');
        const questionNavButtons = document.querySelectorAll('.question-nav-btn');
        
        console.log('Essential elements check:');
        console.log('- Timer element:', timerElement);
        console.log('- Question nav buttons count:', questionNavButtons.length);
        
        try {
            this.setupEventListeners();
            this.loadSavedAnswers();
            this.restoreCurrentAnswer();
            this.updateQuestionNavigation();
            this.updateProgressBar();
            this.startTimer();
            this.setupKeyboardNavigation();
            // Removed the "All the Best" toast that was showing on every navigation
            console.log('App initialization complete');
        } catch (error) {
            console.error('Error during app initialization:', error);
        }
    }

    setupEventListeners() {
        console.log('Setting up event listeners...');
        
        // Answer selection
        document.addEventListener('change', (e) => {
            if (e.target.type === 'radio' && e.target.name === 'answer') {
                console.log('Answer selected:', e.target.value);
                this.saveAnswer(e.target.value);
                this.showToast('Answer saved!', 'info', 2000);
            }
        });

        // Navigation buttons with more robust selection
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const submitBtn = document.getElementById('submitBtn');
        const markForReviewBtn = document.getElementById('markForReviewBtn');

        console.log('Button elements found:');
        console.log('- prevBtn:', prevBtn);
        console.log('- nextBtn:', nextBtn);
        console.log('- submitBtn:', submitBtn);
        console.log('- markForReviewBtn:', markForReviewBtn);

        if (prevBtn) {
            prevBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Previous button clicked');
                this.navigateToQuestion(this.currentQuestion - 1);
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Next button clicked');
                if (this.currentQuestion === this.totalQuestions) {
                    this.showSubmitModal();
                } else {
                    this.navigateToQuestion(this.currentQuestion + 1);
                }
            });
        }

        if (submitBtn) {
            submitBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Submit button clicked');
                this.showSubmitModal();
            });
        }

        if (markForReviewBtn) {
            markForReviewBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Mark for review button clicked');
                this.toggleMarkForReview();
            });
        }

        // Question navigation buttons with more specific targeting
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('question-nav-btn')) {
                e.preventDefault();
                const questionNum = parseInt(e.target.dataset.question);
                console.log('Question nav button clicked:', questionNum);
                if (!isNaN(questionNum)) {
                    this.navigateToQuestion(questionNum);
                }
            }
        });

        // Submit modal checkbox
        const confirmCheckbox = document.getElementById('confirmSubmission');
        if (confirmCheckbox) {
            confirmCheckbox.addEventListener('change', (e) => {
                const submitBtn = document.querySelector('.btn-confirm-submit');
                if (submitBtn) {
                    submitBtn.disabled = !e.target.checked;
                }
            });
        }

        console.log('Event listeners setup complete');
    }

    startTimer() {
        console.log('Starting timer with', this.timeLeft, 'seconds');
        const timerElement = document.getElementById('timer');
        if (!timerElement) {
            console.error('Timer element not found');
            return;
        }

        // Set initial timer display
        this.updateTimerDisplay();

        this.timer = setInterval(() => {
            if (this.timeLeft <= 0) {
                this.timeUp();
                return;
            }

            this.timeLeft--;
            this.updateTimerDisplay();
            
            // Save timer state to localStorage
            localStorage.setItem('examTimeLeft', this.timeLeft.toString());

            // Change color when time is low
            if (this.timeLeft <= 600) { // 10 minutes
                timerElement.classList.add('timer-warning');
            }
            if (this.timeLeft <= 300) { // 5 minutes
                timerElement.classList.add('timer-critical');
                timerElement.classList.remove('timer-warning');
            }
        }, 1000);
    }

    updateTimerDisplay() {
        const timerElement = document.getElementById('timer');
        if (!timerElement) return;

        const hours = Math.floor(this.timeLeft / 3600);
        const minutes = Math.floor((this.timeLeft % 3600) / 60);
        const seconds = this.timeLeft % 60;

        const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Update the timer content while preserving the icon
        timerElement.innerHTML = `<i class="fas fa-clock me-1"></i>${timeString}`;
    }

    timeUp() {
        clearInterval(this.timer);
        this.showToast('Time is up! Submitting exam...', 'warning', 3000);
        setTimeout(() => {
            this.submitExam();
        }, 3000);
    }

    saveAnswer(answer) {
        console.log('Saving answer:', answer, 'for question:', this.currentQuestion);
        this.answers[this.currentQuestion] = answer;
        localStorage.setItem('examAnswers', JSON.stringify(this.answers));
        this.updateQuestionNavigation();
        this.updateProgressBar();
        
        // Update status text
        const statusText = document.getElementById('statusText');
        if (statusText) {
            statusText.innerHTML = `<i class="fas fa-check-circle me-1"></i>Answer saved: Option ${answer}`;
        }
    }

    loadSavedAnswers() {
        const saved = localStorage.getItem('examAnswers');
        if (saved) {
            this.answers = JSON.parse(saved);
            console.log('Loaded saved answers:', this.answers);
        }
    }

    restoreCurrentAnswer() {
        const currentAnswer = this.answers[this.currentQuestion];
        console.log('Restoring answer for question', this.currentQuestion, ':', currentAnswer);
        
        // Clear all radio buttons first
        const radios = document.querySelectorAll('input[name="answer"]');
        radios.forEach(radio => radio.checked = false);
        
        if (currentAnswer) {
            const radio = document.querySelector(`input[name="answer"][value="${currentAnswer}"]`);
            if (radio) {
                radio.checked = true;
                const statusText = document.getElementById('statusText');
                if (statusText) {
                    statusText.innerHTML = `<i class="fas fa-check-circle me-1"></i>Answer saved: Option ${currentAnswer}`;
                }
            }
        } else {
            const statusText = document.getElementById('statusText');
            if (statusText) {
                statusText.innerHTML = `<i class="fas fa-info-circle me-1"></i>Select an option to save your answer`;
            }
        }
    }

    navigateToQuestion(questionNum) {
        if (questionNum < 1 || questionNum > this.totalQuestions) {
            return;
        }
        
        console.log('Navigating to question:', questionNum);
        
        // Save current answer if any is selected
        const selectedAnswer = document.querySelector('input[name="answer"]:checked');
        if (selectedAnswer) {
            this.saveAnswer(selectedAnswer.value);
        }
        
        // Navigate to new question using the correct parameter name
        window.location.href = `/exam?q=${questionNum}`;
    }

    updateQuestionNavigation() {
        // Update question navigation buttons
        document.querySelectorAll('.question-nav-btn').forEach(btn => {
            const questionNum = parseInt(btn.dataset.question);
            
            // Remove all status classes
            btn.classList.remove('attempted', 'not-attempted', 'marked-for-review', 'current');
            
            if (questionNum === this.currentQuestion) {
                btn.classList.add('current');
            } else if (this.markedForReview.has(questionNum)) {
                btn.classList.add('marked-for-review');
            } else if (this.answers[questionNum]) {
                btn.classList.add('attempted');
            } else {
                btn.classList.add('not-attempted');
            }
        });
    }

    updateProgressBar() {
        const answeredQuestions = Object.keys(this.answers).length;
        const progressPercent = (answeredQuestions / this.totalQuestions) * 100;
        
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        if (progressBar) {
            progressBar.style.width = `${progressPercent}%`;
            progressBar.setAttribute('aria-valuenow', progressPercent);
        }
        
        if (progressText) {
            progressText.textContent = `${answeredQuestions}/${this.totalQuestions} Questions Answered`;
        }
    }

    toggleMarkForReview() {
        if (this.markedForReview.has(this.currentQuestion)) {
            this.markedForReview.delete(this.currentQuestion);
            this.showToast('Removed from review list', 'info');
        } else {
            this.markedForReview.add(this.currentQuestion);
            this.showToast('Marked for review', 'warning');
        }
        
        localStorage.setItem('markedForReview', JSON.stringify([...this.markedForReview]));
        this.updateQuestionNavigation();
        
        // Update button text
        const markBtn = document.getElementById('markForReviewBtn');
        if (markBtn) {
            if (this.markedForReview.has(this.currentQuestion)) {
                markBtn.innerHTML = '<i class="fas fa-star me-2"></i>Unmark Review';
                markBtn.classList.add('btn-warning');
                markBtn.classList.remove('btn-outline-warning');
            } else {
                markBtn.innerHTML = '<i class="fas fa-star me-2"></i>Mark for Review';
                markBtn.classList.add('btn-outline-warning');
                markBtn.classList.remove('btn-warning');
            }
        }
    }

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Don't interfere if user is typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    if (this.currentQuestion > 1) {
                        this.navigateToQuestion(this.currentQuestion - 1);
                    }
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    if (this.currentQuestion < this.totalQuestions) {
                        this.navigateToQuestion(this.currentQuestion + 1);
                    }
                    break;
                case '1':
                case '2':
                case '3':
                case '4':
                    e.preventDefault();
                    const optionValue = ['A', 'B', 'C', 'D'][parseInt(e.key) - 1];
                    const radio = document.querySelector(`input[name="answer"][value="${optionValue}"]`);
                    if (radio) {
                        radio.checked = true;
                        this.saveAnswer(optionValue);
                    }
                    break;
                case 'm':
                case 'M':
                    e.preventDefault();
                    this.toggleMarkForReview();
                    break;
            }
        });
    }

    showSubmitModal() {
        console.log('Attempting to show submit modal...');
        const modal = document.getElementById('submitModal');
        if (!modal) {
            console.error('Submit modal not found!');
            // Fallback: direct submit
            if (confirm('Are you sure you want to submit the exam?')) {
                this.submitExam();
            }
            return;
        }
        
        console.log('Submit modal found:', modal);
        
        // Generate submission summary
        const summary = this.generateSubmissionSummary();
        const summaryElement = document.getElementById('submissionSummary');
        if (summaryElement) {
            summaryElement.innerHTML = summary;
        }
        
        // Reset checkbox
        const checkbox = document.getElementById('confirmSubmission');
        if (checkbox) {
            checkbox.checked = false;
        }
        
        // Disable submit button
        const submitBtn = document.querySelector('.btn-confirm-submit');
        if (submitBtn) {
            submitBtn.disabled = true;
        }
        
        // Show modal
        try {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            console.log('Modal shown successfully');
        } catch (error) {
            console.error('Error showing modal:', error);
            // Fallback: direct submit
            if (confirm('Are you sure you want to submit the exam?')) {
                this.submitExam();
            }
        }
    }

    generateSubmissionSummary() {
        const answeredCount = Object.keys(this.answers).length;
        const unansweredCount = this.totalQuestions - answeredCount;
        const markedCount = this.markedForReview.size;
        
        return `
            <div class="row text-center">
                <div class="col-md-4">
                    <div class="border rounded p-3">
                        <h4 class="text-success">${answeredCount}</h4>
                        <small>Answered</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="border rounded p-3">
                        <h4 class="text-danger">${unansweredCount}</h4>
                        <small>Not Answered</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="border rounded p-3">
                        <h4 class="text-warning">${markedCount}</h4>
                        <small>Marked for Review</small>
                    </div>
                </div>
            </div>
            <div class="mt-3 text-center">
                <p class="mb-0">Time Remaining: <strong>${this.formatTime(this.timeLeft)}</strong></p>
            </div>
        `;
    }

    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    showToast(message, type = 'info', duration = 3000) {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'warning' ? 'warning' : type === 'error' ? 'danger' : 'info'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : type === 'error' ? 'times-circle' : 'info-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();
        
        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    submitExam() {
        if (this.isSubmitted) return;
        
        this.isSubmitted = true;
        clearInterval(this.timer);
        
        console.log('Submitting exam with answers:', this.answers);
        
        // Save all data
        const examData = {
            answers: this.answers,
            markedForReview: [...this.markedForReview],
            timeLeft: this.timeLeft,
            submissionTime: new Date().toISOString()
        };
        
        console.log('Sending exam data:', examData);
        
        // Send to server
        fetch('/submit_exam', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(examData)
        })
        .then(response => {
            console.log('Submit response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Submit response data:', data);
            if (data.success) {
                // Clear local storage
                localStorage.removeItem('examAnswers');
                localStorage.removeItem('markedForReview');
                
                console.log('Exam submitted successfully. Redirecting to results...');
                
                // Use the redirect URL provided by the server (includes results ID)
                const redirectUrl = data.redirect_url || '/results';
                
                // Small delay to ensure data is saved, then redirect
                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 500);
            } else {
                console.error('Submit failed:', data);
                this.showToast('Error submitting exam: ' + (data.error || 'Unknown error'), 'error');
                this.isSubmitted = false;
            }
        })
        .catch(error => {
            console.error('Submit error:', error);
            this.showToast('Error submitting exam. Please try again.', 'error');
            this.isSubmitted = false;
        });
    }
}

// Global function for confirm submit (called from modal)
function confirmSubmit() {
    if (window.examApp) {
        window.examApp.submitExam();
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, checking for exam page...');
    
    // Check if we're on the exam page
    const examContainer = document.querySelector('[data-current-question]');
    if (examContainer) {
        console.log('Exam page detected, initializing app...');
        console.log('Container found:', examContainer);
        console.log('Current question:', examContainer.getAttribute('data-current-question'));
        console.log('Total questions:', examContainer.getAttribute('data-total-questions'));
        
        // Add a small delay to ensure all elements are loaded
        setTimeout(() => {
            window.examApp = new ExamApp();
        }, 100);
    } else {
        console.log('Not on exam page, exam container not found');
    }
    
    // Debug: Log all buttons found
    console.log('Navigation buttons found:');
    console.log('- Previous button:', document.getElementById('prevBtn'));
    console.log('- Next button:', document.getElementById('nextBtn'));
    console.log('- Submit button:', document.getElementById('submitBtn'));
    console.log('- Mark for review button:', document.getElementById('markForReviewBtn'));
    console.log('- Question nav buttons:', document.querySelectorAll('.question-nav-btn').length);
});

// Test function to verify JavaScript is loaded
window.testExamApp = function() {
    console.log('JavaScript is working!');
    console.log('ExamApp available:', typeof ExamApp);
    console.log('Window examApp:', window.examApp);
    
    // Test button click handlers
    const nextBtn = document.getElementById('nextBtn');
    if (nextBtn) {
        console.log('Next button found, testing click...');
        nextBtn.click();
    } else {
        console.log('Next button not found');
    }
    
    return 'Test complete - check console for details';
};
