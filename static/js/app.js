// JavaScript untuk Sistem Ujian Online

class UjianProctor {
    constructor(ujianId, durasi) {
        this.ujianId = ujianId;
        this.durasi = durasi * 60; // convert to seconds
        this.timeLeft = this.durasi;
        this.pelanggaranCount = 0;
        this.maxPelanggaran = 3;
        this.currentSoal = 1;
        this.totalSoal = 0;
        this.jawaban = {};
        this.isExamActive = true;
        
        this.initializeExam();
    }
    
    initializeExam() {
        this.startTimer();
        this.setupEventListeners();
        this.startProctorMonitoring();
    }
    
    startTimer() {
        this.timerInterval = setInterval(() => {
            if (this.timeLeft <= 0) {
                this.endExam('Waktu habis');
                return;
            }
            
            this.timeLeft--;
            this.updateTimerDisplay();
        }, 1000);
    }
    
    updateTimerDisplay() {
        const hours = Math.floor(this.timeLeft / 3600);
        const minutes = Math.floor((this.timeLeft % 3600) / 60);
        const seconds = this.timeLeft % 60;
        
        const display = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        document.getElementById('timer').textContent = display;
        
        // Warning colors
        if (this.timeLeft < 300) { // 5 minutes
            document.getElementById('timer').className = 'timer-display bg-danger text-white';
        } else if (this.timeLeft < 600) { // 10 minutes
            document.getElementById('timer').className = 'timer-display bg-warning text-dark';
        }
    }
    
    setupEventListeners() {
        // Answer selection
        document.addEventListener('change', (e) => {
            if (e.target.type === 'radio' && e.target.name.startsWith('soal_')) {
                const soalId = e.target.name.split('_')[1];
                this.jawaban[soalId] = e.target.value;
                this.updateNavigationButton(soalId);
                this.saveProgress();
            }
        });
        
        // Navigation buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-soal')) {
                const soalNumber = parseInt(e.target.dataset.soal);
                this.navigateToSoal(soalNumber);
            }
            
            if (e.target.id === 'btnNext') {
                this.nextSoal();
            }
            
            if (e.target.id === 'btnPrev') {
                this.prevSoal();
            }
            
            if (e.target.id === 'btnSubmit') {
                this.showSubmitConfirmation();
            }
        });
        
        // Prevent cheating attempts
        this.preventCheating();
    }
    
    preventCheating() {
        // Disable right click
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.triggerViolation('Mencoba membuka menu konteks', 'ringan');
        });
        
        // Disable F12, Ctrl+Shift+I, etc.
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F12' || 
                (e.ctrlKey && e.shiftKey && e.key === 'I') ||
                (e.ctrlKey && e.shiftKey && e.key === 'C') ||
                (e.ctrlKey && e.key === 'u')) {
                e.preventDefault();
                this.triggerViolation('Mencoba membuka developer tools', 'berat');
            }
            
            // Disable Alt+Tab
            if (e.altKey && e.key === 'Tab') {
                e.preventDefault();
                this.triggerViolation('Mencoba beralih aplikasi', 'berat');
            }
        });
        
        // Detect window focus loss
        window.addEventListener('blur', () => {
            this.triggerViolation('Keluar dari jendela ujian', 'berat');
        });
        
        // Disable text selection
        document.addEventListener('selectstart', (e) => {
            if (!e.target.closest('.pilihan-jawaban')) {
                e.preventDefault();
            }
        });
    }
    
    startProctorMonitoring() {
        // Start video monitoring
        this.initializeCamera();
        
        // Check proctor status periodically
        this.proctorInterval = setInterval(() => {
            this.checkProctorStatus();
        }, 2000);
    }
    
    initializeCamera() {
        navigator.mediaDevices.getUserMedia({ video: true, audio: false })
            .then((stream) => {
                const video = document.getElementById('videoElement');
                video.srcObject = stream;
                video.play();
                
                // Send frame to backend for processing
                this.sendFrameToBackend();
            })
            .catch((err) => {
                console.error('Error accessing camera:', err);
                this.triggerViolation('Tidak dapat mengakses kamera', 'berat');
            });
    }
    
    sendFrameToBackend() {
        const video = document.getElementById('videoElement');
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        setInterval(() => {
            if (video.videoWidth > 0 && this.isExamActive) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0);
                
                canvas.toBlob((blob) => {
                    const formData = new FormData();
                    formData.append('frame', blob);
                    formData.append('ujian_id', this.ujianId);
                    
                    fetch('/api/proctor/process-frame', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.violation) {
                            this.handleViolationFromBackend(data);
                        }
                    })
                    .catch(err => console.error('Error sending frame:', err));
                }, 'image/jpeg', 0.7);
            }
        }, 1000); // Send frame every second
    }
    
    checkProctorStatus() {
        fetch(`/api/proctor/status/${this.ujianId}`)
            .then(response => response.json())
            .then(data => {
                if (data.violations) {
                    data.violations.forEach(violation => {
                        this.handleViolationFromBackend(violation);
                    });
                }
                
                if (data.should_end_exam) {
                    this.endExam('Terlalu banyak pelanggaran');
                }
            })
            .catch(err => console.error('Error checking proctor status:', err));
    }
    
    handleViolationFromBackend(violationData) {
        this.pelanggaranCount++;
        this.updateViolationCounter();
        
        if (violationData.level === 'berat') {
            this.showSevereViolationAlert(violationData.message);
        } else {
            this.showMildViolationAlert(violationData.message);
        }
        
        if (this.pelanggaranCount >= this.maxPelanggaran) {
            this.endExam('Terlalu banyak pelanggaran');
        }
    }
    
    triggerViolation(message, level) {
        this.pelanggaranCount++;
        this.updateViolationCounter();
        
        // Send to backend
        fetch('/api/proctor/violation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ujian_id: this.ujianId,
                message: message,
                level: level
            })
        });
        
        if (level === 'berat') {
            this.showSevereViolationAlert(message);
        } else {
            this.showMildViolationAlert(message);
        }
        
        if (this.pelanggaranCount >= this.maxPelanggaran) {
            this.endExam('Terlalu banyak pelanggaran');
        }
    }
    
    showMildViolationAlert(message) {
        const alertHtml = `
            <div class="alert alert-warning alert-pelanggaran ringan" role="alert">
                <h5><i class="fas fa-exclamation-triangle"></i> Peringatan!</h5>
                <p>${message}</p>
                <p><strong>Pelanggaran ke-${this.pelanggaranCount} dari ${this.maxPelanggaran}</strong></p>
                <button type="button" class="btn btn-warning btn-sm" onclick="this.parentElement.remove()">
                    Mengerti
                </button>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            const alert = document.querySelector('.alert-pelanggaran.ringan');
            if (alert) alert.remove();
        }, 5000);
    }
    
    showSevereViolationAlert(message) {
        const alertHtml = `
            <div class="alert alert-danger alert-pelanggaran berat" role="alert">
                <h5><i class="fas fa-ban"></i> PELANGGARAN BERAT!</h5>
                <p>${message}</p>
                <p><strong>Pelanggaran ke-${this.pelanggaranCount} dari ${this.maxPelanggaran}</strong></p>
                <p class="mb-0"><strong>Screenshot telah diambil sebagai bukti!</strong></p>
                <button type="button" class="btn btn-danger" onclick="this.parentElement.remove()">
                    OK, Saya Mengerti
                </button>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', alertHtml);
    }
    
    updateViolationCounter() {
        const counter = document.getElementById('violationCounter');
        if (counter) {
            counter.textContent = `${this.pelanggaranCount}/${this.maxPelanggaran}`;
            
            if (this.pelanggaranCount >= 2) {
                counter.className = 'warning-counter bg-danger';
            } else if (this.pelanggaranCount >= 1) {
                counter.className = 'warning-counter bg-warning text-dark';
            }
        }
    }
    
    navigateToSoal(soalNumber) {
        this.currentSoal = soalNumber;
        
        // Hide all soal
        document.querySelectorAll('.soal-container').forEach(soal => {
            soal.style.display = 'none';
        });
        
        // Show current soal
        const currentSoalElement = document.getElementById(`soal_${soalNumber}`);
        if (currentSoalElement) {
            currentSoalElement.style.display = 'block';
        }
        
        // Update navigation buttons
        this.updateNavigationButtons();
    }
    
    updateNavigationButtons() {
        document.querySelectorAll('.btn-soal').forEach(btn => {
            btn.classList.remove('current');
        });
        
        const currentBtn = document.querySelector(`[data-soal="${this.currentSoal}"]`);
        if (currentBtn) {
            currentBtn.classList.add('current');
        }
        
        // Update prev/next buttons
        const btnPrev = document.getElementById('btnPrev');
        const btnNext = document.getElementById('btnNext');
        
        if (btnPrev) btnPrev.disabled = this.currentSoal <= 1;
        if (btnNext) btnNext.disabled = this.currentSoal >= this.totalSoal;
    }
    
    updateNavigationButton(soalId) {
        const btn = document.querySelector(`[data-soal="${soalId}"]`);
        if (btn) {
            btn.classList.add('answered');
        }
    }
    
    nextSoal() {
        if (this.currentSoal < this.totalSoal) {
            this.navigateToSoal(this.currentSoal + 1);
        }
    }
    
    prevSoal() {
        if (this.currentSoal > 1) {
            this.navigateToSoal(this.currentSoal - 1);
        }
    }
    
    saveProgress() {
        // Save to localStorage as backup
        localStorage.setItem(`ujian_${this.ujianId}_progress`, JSON.stringify({
            jawaban: this.jawaban,
            currentSoal: this.currentSoal,
            timeLeft: this.timeLeft
        }));
        
        // Send to backend
        fetch('/api/ujian/save-progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ujian_id: this.ujianId,
                jawaban: this.jawaban
            })
        });
    }
    
    showSubmitConfirmation() {
        const answeredCount = Object.keys(this.jawaban).length;
        const unansweredCount = this.totalSoal - answeredCount;
        
        let message = `Anda akan mengirim ujian dengan ${answeredCount} soal terjawab.`;
        if (unansweredCount > 0) {
            message += `\n\nMasih ada ${unansweredCount} soal yang belum dijawab.`;
        }
        message += '\n\nApakah Anda yakin ingin mengirim ujian?';
        
        if (confirm(message)) {
            this.submitExam();
        }
    }
    
    submitExam() {
        this.endExam('Ujian diselesaikan');
    }
    
    endExam(reason) {
        this.isExamActive = false;
        
        // Clear intervals
        if (this.timerInterval) clearInterval(this.timerInterval);
        if (this.proctorInterval) clearInterval(this.proctorInterval);
        
        // Stop camera
        const video = document.getElementById('videoElement');
        if (video && video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
        }
        
        // Submit final answers
        fetch('/api/ujian/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ujian_id: this.ujianId,
                jawaban: this.jawaban,
                reason: reason,
                pelanggaran_count: this.pelanggaranCount
            })
        })
        .then(response => response.json())
        .then(data => {
            // Show result
            alert(`Ujian telah selesai!\nAlasan: ${reason}\nNilai: ${data.nilai || 'Sedang diproses'}`);
            
            // Redirect to dashboard
            window.location.href = '/siswa/dashboard';
        })
        .catch(err => {
            console.error('Error submitting exam:', err);
            alert('Terjadi kesalahan saat mengirim ujian. Silakan hubungi administrator.');
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            if (alert.classList.contains('alert-dismissible')) {
                alert.remove();
            }
        });
    }, 5000);
});

// Global functions
window.UjianProctor = UjianProctor;