document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const startBtn = document.getElementById('start-camera');
    const stopBtn = document.getElementById('stop-camera');
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const preview = document.getElementById('preview');
    const resultText = document.getElementById('result-text');
    const copyBtn = document.getElementById('copy-result');
    const statusElement = document.getElementById('scanning-status');
    
    let stream = null;
    let scanningInterval = null;
    let isScanning = false;
    
    // Camera controls
    startBtn.addEventListener('click', startCamera);
    stopBtn.addEventListener('click', stopCamera);
    
    // File upload handlers
    fileInput.addEventListener('change', handleFileUpload);
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);
    
    // Copy result button
    copyBtn.addEventListener('click', copyResult);
    
    /**
     * Start the camera and begin scanning
     */
    async function startCamera() {
        if (isScanning) return;
        
        try {
            // Request camera access
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'environment' // Prefer rear camera on mobile
                } 
            });
            
            // Set video source and play
            video.srcObject = stream;
            await video.play();
            
            // Update UI
            startBtn.disabled = true;
            stopBtn.disabled = false;
            isScanning = true;
            updateStatus('Camera started. Point at a barcode to scan...');
            
            // Start scanning at regular intervals
            scanningInterval = setInterval(scanFrame, 1000);
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            updateStatus('Error: Could not access camera. Make sure you have granted camera permissions.');
        }
    }
    
    /**
     * Stop the camera and clean up
     */
    function stopCamera() {
        if (!isScanning) return;
        
        // Stop video tracks
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        
        // Clear scanning interval
        if (scanningInterval) {
            clearInterval(scanningInterval);
            scanningInterval = null;
        }
        
        // Update UI
        startBtn.disabled = false;
        stopBtn.disabled = true;
        isScanning = false;
        updateStatus('Camera stopped');
    }
    
    /**
     * Capture and process a frame from the video stream
     */
    async function scanFrame() {
        if (!isScanning) return;
        
        try {
            // Set canvas dimensions to match video
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // Draw current video frame to canvas
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Convert to base64 for sending to server
            const imageData = canvas.toDataURL('image/jpeg', 0.8);
            
            // Send to server for processing
            const result = await decodeBarcodeAPI(imageData);
            
            if (result && result.success) {
                displayResult(result.decoded);
                stopCamera(); // Stop scanning on success
            }
            
        } catch (error) {
            console.error('Error scanning frame:', error);
        }
    }
    
    /**
     * Handle file upload
     */
    function handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Check if file is an image
        if (!file.type.startsWith('image/')) {
            updateStatus('Please upload an image file');
            return;
        }
        
        // Create preview
        const reader = new FileReader();
        reader.onload = async function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            dropZone.querySelector('p').textContent = file.name;
            
            // Process the image and handle result
            const result = await decodeBarcodeAPI(e.target.result);
            if (result && result.success) {
                displayResult(result.decoded);
            } else if (result && !result.success) {
                updateStatus(result.error || 'No barcode detected', 'error');
            }
        };
        reader.readAsDataURL(file);
    }
    
    /**
     * Handle drag over event
     */
    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('drag-over');
    }
    
    /**
     * Handle drag leave event
     */
    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('drag-over');
    }
    
    /**
     * Handle drop event
     */
    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('drag-over');
        
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            fileInput.files = e.dataTransfer.files;
            handleFileUpload({ target: { files: [file] } });
        } else {
            updateStatus('Please drop an image file');
        }
    }
    
    /**
     * Send image to server for barcode decoding
     */
    async function decodeBarcodeAPI(imageData) {
        updateStatus('Processing image...');
        
        try {
            const response = await fetch('/decode_barcode', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify({ 
                    image: imageData 
                })
            });
            
            if (!response.ok) {
                throw new Error('Server error');
            }
            
            const result = await response.json();
            
            if (result.success) {
                return result;
            } else {
                updateStatus(result.error || 'No barcode detected');
                return null;
            }
            
        } catch (error) {
            console.error('Error decoding barcode:', error);
            updateStatus('Error processing image');
            return null;
        }
    }
    
    /**
     * Display the decoded result
     */
    function displayResult(decoded) {
        resultText.textContent = decoded;
        copyBtn.style.display = 'inline-flex';
        updateStatus('Barcode scanned successfully!', 'success');
        
        // Scroll to result
        resultText.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    /**
     * Copy result to clipboard
     */
    async function copyResult() {
        try {
            await navigator.clipboard.writeText(resultText.textContent);
            
            // Visual feedback
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<span class="copy-icon">✓</span> Copied!';
            copyBtn.style.backgroundColor = 'var(--success)';
            
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
                copyBtn.style.backgroundColor = '';
            }, 2000);
            
        } catch (error) {
            console.error('Error copying text:', error);
            updateStatus('Failed to copy to clipboard');
        }
    }
    
    /**
     * Update status message
     */
    function updateStatus(message, type = 'info') {
        if (!statusElement) return;
        
        statusElement.textContent = message;
        statusElement.className = 'status-message';
        
        if (type === 'error') {
            statusElement.classList.add('error');
        } else if (type === 'success') {
            statusElement.classList.add('success');
        }
    }
    
    // Clean up on page unload
    window.addEventListener('beforeunload', stopCamera);
    
    // Handle visibility change (tab switch)
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && isScanning) {
            stopCamera();
        }
    });
});
