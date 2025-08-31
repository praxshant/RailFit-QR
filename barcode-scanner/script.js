// Global variables
let video = null;
let canvas = null;
let canvasCtx = null;
let stream = null;
let isScanning = false;
let cv = null;

// DOM Elements
const webcamView = document.getElementById('webcamView');
const uploadView = document.getElementById('uploadView');
const webcamTab = document.getElementById('webcamTab');
const uploadTab = document.getElementById('uploadTab');
const startButton = document.getElementById('startButton');
const scanButton = document.getElementById('scanButton');
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const previewImage = document.getElementById('previewImage');
const resultBox = document.getElementById('result');
const hexResult = document.getElementById('hexResult');
const errorElement = document.getElementById('error');
const toggleDebug = document.getElementById('toggleDebug');
const debugInfo = document.getElementById('debugInfo');
const debugContent = document.getElementById('debugContent');

// Debug logging
function logDebug(message, data = null) {
    const timestamp = new Date().toISOString().substr(11, 12);
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${message}`;
    
    if (data) {
        const pre = document.createElement('pre');
        pre.textContent = JSON.stringify(data, null, 2);
        logEntry.appendChild(pre);
    }
    
    debugContent.prepend(logEntry);
    
    // Limit number of log entries
    while (debugContent.children.length > 50) {
        debugContent.removeChild(debugContent.lastChild);
    }
}

// Toggle debug info
if (toggleDebug && debugInfo) {
    toggleDebug.addEventListener('click', () => {
        const isHidden = debugInfo.style.display === 'none';
        debugInfo.style.display = isHidden ? 'block' : 'none';
        toggleDebug.innerHTML = isHidden 
            ? '<i class="fas fa-bug"></i> Hide Debug Info' 
            : '<i class="fas fa-bug"></i> Show Debug Info';
    });
}

// Tab switching
function switchTab(tab) {
    // Update active tab
    webcamTab.classList.toggle('active', tab === 'webcam');
    uploadTab.classList.toggle('active', tab === 'upload');
    
    // Update active view
    webcamView.classList.toggle('active', tab === 'webcam');
    uploadView.classList.toggle('active', tab === 'upload');
    
    // Stop webcam when switching to upload tab
    if (tab === 'upload' && stream) {
        stopWebcam();
    }
    
    // Clear any previous results/errors
    clearResults();
}

webcamTab.addEventListener('click', () => switchTab('webcam'));
uploadTab.addEventListener('click', () => switchTab('upload'));

// Webcam functions
async function startWebcam() {
    try {
        video = document.getElementById('webcam');
        canvas = document.getElementById('canvas');
        canvasCtx = canvas.getContext('2d');
        
        // Set canvas size to match video
        const constraints = {
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'environment'
            },
            audio: false
        };
        
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;
        
        // Wait for video to be ready
        await new Promise((resolve) => {
            video.onloadedmetadata = () => {
                video.play();
                resolve();
            };
        });
        
        // Set canvas dimensions to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Update UI
        startButton.innerHTML = '<i class="fas fa-stop"></i> Stop Camera';
        startButton.onclick = stopWebcam;
        scanButton.disabled = false;
        
        logDebug('Webcam started');
    } catch (err) {
        console.error('Error accessing webcam:', err);
        showError('Could not access webcam. Please ensure you have granted camera permissions.');
    }
}

function stopWebcam() {
    if (stream) {
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
        stream = null;
    }
    
    if (video) {
        video.pause();
        video.srcObject = null;
    }
    
    // Update UI
    startButton.innerHTML = '<i class="fas fa-play"></i> Start Camera';
    startButton.onclick = startWebcam;
    scanButton.disabled = true;
    
    logDebug('Webcam stopped');
}

// File upload handling
function handleFileSelect(event) {
    const file = event.target.files[0] || (event.dataTransfer && event.dataTransfer.files[0]);
    
    if (!file) return;
    
    // Check if file is an image
    if (!file.type.match('image.*')) {
        showError('Please select an image file (JPEG, PNG, etc.)');
        return;
    }
    
    // Create a preview of the image
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImage.src = e.target.result;
        previewImage.style.display = 'block';
        
        // Process the image
        processImage(previewImage);
    };
    reader.readAsDataURL(file);
    
    // Reset the file input to allow selecting the same file again
    fileInput.value = '';
}

// Drag and drop handling
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    
    if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        const event = new Event('change');
        fileInput.dispatchEvent(event);
    }
});

dropZone.addEventListener('click', () => {
    fileInput.click();
});

// Scan button click handler
scanButton.addEventListener('click', () => {
    if (!video || !canvas || !canvasCtx) return;
    
    // Draw current video frame to canvas
    canvasCtx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Process the captured frame
    processImage(canvas);
});

// Process the image with OpenCV
async function processImage(imageElement) {
    if (!cv) {
        showError('OpenCV.js is not loaded yet. Please wait...');
        return;
    }
    
    try {
        showLoading('Processing image...');
        
        // Create a temporary canvas to process the image
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        // Set canvas dimensions to match the image
        tempCanvas.width = imageElement.naturalWidth || imageElement.videoWidth || imageElement.width;
        tempCanvas.height = imageElement.naturalHeight || imageElement.videoHeight || imageElement.height;
        
        // Draw the image to the canvas
        tempCtx.drawImage(imageElement, 0, 0, tempCanvas.width, tempCanvas.height);
        
        // Convert canvas to OpenCV Mat
        const src = cv.imread(tempCanvas);
        
        // Process the image to detect and decode the barcode
        const result = await detectAndDecodeBarcode(src);
        
        // Display the result
        if (result && result.barcode) {
            showResult(result.barcode, result.debugInfo);
        } else {
            showError('No barcode detected or could not decode the barcode.');
        }
        
        // Clean up
        src.delete();
    } catch (err) {
        console.error('Error processing image:', err);
        showError('An error occurred while processing the image.');
    }
}

// Detect and decode barcode from image
async function detectAndDecodeBarcode(src) {
    try {
        // Convert to grayscale
        const gray = new cv.Mat();
        cv.cvtColor(src, gray, cv.COLOR_RGBA2GRAY);
        
        // Apply Gaussian blur to reduce noise
        const blurred = new cv.Mat();
        cv.GaussianBlur(gray, blurred, new cv.Size(5, 5), 0);
        
        // Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
        const clahe = new cv.CLAHE(2.0, new cv.Size(8, 8));
        const claheMat = new cv.Mat();
        clahe.apply(blurred, claheMat);
        
        // Apply adaptive threshold
        const binary = new cv.Mat();
        cv.adaptiveThreshold(claheMat, binary, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, 
                            cv.THRESH_BINARY_INV, 25, 10);
        
        // Apply morphological operations to clean up the image
        const kernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(3, 3));
        const morph = new cv.Mat();
        cv.morphologyEx(binary, morph, cv.MORPH_CLOSE, kernel);
        
        // Find contours
        const contours = new cv.MatVector();
        const hierarchy = new cv.Mat();
        cv.findContours(morph.clone(), contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);
        
        // Debug: Draw all contours
        const debugDraw = src.clone();
        cv.drawContours(debugDraw, contours, -1, [0, 255, 0, 255], 2);
        
        // Find the largest contour that's likely to be our barcode
        let maxArea = 0;
        let maxContour = null;
        
        for (let i = 0; i < contours.size(); i++) {
            const contour = contours.get(i);
            const area = cv.contourArea(contour);
            const rect = cv.boundingRect(contour);
            const aspectRatio = rect.width / rect.height;
            
            // Look for contours that are wide and not too tall (barcode-like shape)
            if (area > maxArea && aspectRatio > 2) {
                maxArea = area;
                maxContour = contour;
            }
        }
        
        if (!maxContour || maxArea < 1000) { // Minimum area threshold
            logDebug('No significant barcode contour found');
            return null;
        }
        
        // Get the bounding rect of the largest contour
        const rect = cv.boundingRect(maxContour);
        
        // Add some padding to ensure we get the entire barcode
        const padding = 10;
        const x = Math.max(0, rect.x - padding);
        const y = Math.max(0, rect.y - padding);
        const width = Math.min(src.cols - x, rect.width + 2 * padding);
        const height = Math.min(src.rows - y, rect.height + 2 * padding);
        
        // Extract the ROI (Region of Interest)
        const roiRect = new cv.Rect(x, y, width, height);
        const roi = src.roi(roiRect);
        
        // Debug: Draw the ROI
        cv.rectangle(debugDraw, new cv.Point(x, y), 
                    new cv.Point(x + width, y + height), 
                    [255, 0, 0, 255], 2);
        
        // Process the ROI to decode the barcode
        const barcodeData = await decodeBarcode(roi);
        
        // Clean up
        gray.delete();
        blurred.delete();
        claheMat.delete();
        binary.delete();
        morph.delete();
        kernel.delete();
        contours.delete();
        hierarchy.delete();
        debugDraw.delete();
        roi.delete();
        
        return {
            barcode: barcodeData,
            debugInfo: {
                contourArea: maxArea,
                boundingBox: rect,
                imageSize: { width: src.cols, height: src.rows }
            }
        };
    } catch (err) {
        console.error('Error in detectAndDecodeBarcode:', err);
        return null;
    }
}

// Decode the barcode from the ROI
async function decodeBarcode(roi) {
    try {
        // Convert to grayscale
        const gray = new cv.Mat();
        cv.cvtColor(roi, gray, cv.COLOR_RGBA2GRAY);
        
        // Apply adaptive thresholding
        const binary = new cv.Mat();
        cv.adaptiveThreshold(gray, binary, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, 
                           cv.THRESH_BINARY_INV, 25, 10);
        
        // Calculate the vertical projection profile
        const projection = new Array(roi.cols).fill(0);
        const data = binary.data;
        
        // Count black pixels in each column
        for (let y = 0; y < roi.rows; y++) {
            for (let x = 0; x < roi.cols; x++) {
                const idx = y * roi.cols + x;
                if (data[idx] > 0) {
                    projection[x]++;
                }
            }
        }
        
        // Smooth the projection to reduce noise
        const smoothedProjection = [...projection];
        const windowSize = 5;
        const halfWindow = Math.floor(windowSize / 2);
        
        for (let i = halfWindow; i < projection.length - halfWindow; i++) {
            let sum = 0;
            for (let j = -halfWindow; j <= halfWindow; j++) {
                sum += projection[i + j];
            }
            smoothedProjection[i] = Math.round(sum / windowSize);
        }
        
        // Find local maxima (peaks) in the projection
        const peaks = [];
        const minPeakHeight = Math.max(...smoothedProjection) * 0.3; // Minimum peak height
        
        for (let i = 1; i < smoothedProjection.length - 1; i++) {
            if (smoothedProjection[i] > minPeakHeight &&
                smoothedProjection[i] > smoothedProjection[i - 1] &&
                smoothedProjection[i] > smoothedProjection[i + 1]) {
                peaks.push({
                    position: i,
                    height: smoothedProjection[i]
                });
            }
        }
        
        // If we found too many peaks, take the strongest ones
        const maxBars = 16;
        let selectedPeaks = [...peaks]
            .sort((a, b) => b.height - a.height)
            .slice(0, maxBars)
            .sort((a, b) => a.position - b.position);
        
        // If we have fewer peaks than needed, try to interpolate
        if (selectedPeaks.length < maxBars && selectedPeaks.length >= 2) {
            const newPeaks = [];
            const avgSpacing = (selectedPeaks[selectedPeaks.length - 1].position - selectedPeaks[0].position) / (selectedPeaks.length - 1);
            
            for (let i = 0; i < maxBars; i++) {
                const expectedPos = selectedPeaks[0].position + (i * avgSpacing);
                let closestPeak = selectedPeaks[0];
                let minDist = Math.abs(selectedPeaks[0].position - expectedPos);
                
                for (const peak of selectedPeaks) {
                    const dist = Math.abs(peak.position - expectedPos);
                    if (dist < minDist) {
                        minDist = dist;
                        closestPeak = peak;
                    }
                }
                
                newPeaks.push({
                    position: Math.round(expectedPos),
                    height: closestPeak.height
                });
            }
            
            selectedPeaks = newPeaks;
        }
        
        // Normalize heights to 16 levels (0-15)
        const maxHeight = Math.max(...selectedPeaks.map(p => p.height), 1);
        const normalizedHeights = selectedPeaks.map(peak => {
            // Map height to 0-15 range (0 is the shortest, 15 is the tallest)
            return Math.min(15, Math.max(0, Math.round((peak.height / maxHeight) * 15)));
        });
        
        // Convert heights to hex digits (0-F)
        const hexDigits = normalizedHeights.map(height => {
            // Map height (0-15) to hex digit (0-F)
            return Math.min(15, Math.max(0, Math.round(height))).toString(16).toUpperCase();
        });
        
        // Clean up
        gray.delete();
        binary.delete();
        
        // Return the first 16 digits or pad with zeros if needed
        return hexDigits.slice(0, 16).join('').padEnd(16, '0');
        
    } catch (err) {
        console.error('Error in decodeBarcode:', err);
        return null;
    }
}

// UI Helpers
function showLoading(message) {
    resultBox.innerHTML = `<div class="loading">${message}</div>`;
    errorElement.textContent = '';
}

function showResult(hexString, debugInfo = null) {
    // Format the hex string with spaces every 4 characters for better readability
    const formattedHex = hexString.replace(/(.{4})(?=.)/g, '$1 ');
    
    hexResult.textContent = formattedHex;
    resultBox.innerHTML = `
        <p>Decoded Barcode:</p>
        <div class="hex-result">${formattedHex}</div>
    `;
    
    // Add copy to clipboard button
    const copyButton = document.createElement('button');
    copyButton.className = 'btn secondary';
    copyButton.style.marginTop = '10px';
    copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy to Clipboard';
    copyButton.onclick = () => {
        navigator.clipboard.writeText(hexString).then(() => {
            const originalText = copyButton.innerHTML;
            copyButton.innerHTML = '<i class="fas fa-check"></i> Copied!';
            setTimeout(() => {
                copyButton.innerHTML = originalText;
            }, 2000);
        });
    };
    
    resultBox.appendChild(copyButton);
    errorElement.textContent = '';
    
    // Log debug info if available
    if (debugInfo) {
        logDebug('Barcode decoded successfully', {
            hexString,
            ...debugInfo
        });
    }
}

function showError(message) {
    errorElement.textContent = message;
    resultBox.innerHTML = '<p class="placeholder">Scan a barcode to see the result</p>';
    hexResult.textContent = '';
    
    logDebug('Error: ' + message);
}

function clearResults() {
    resultBox.innerHTML = '<p class="placeholder">Scan a barcode to see the result</p>';
    hexResult.textContent = '';
    errorElement.textContent = '';
}

// Initialize the application
function init() {
    logDebug('Application initialized');
    
    // Set up file input change handler
    fileInput.addEventListener('change', handleFileSelect);
    
    // Set up start button
    startButton.addEventListener('click', startWebcam);
    
    // Initial tab
    switchTab('webcam');
}

// OpenCV.js ready callback
function onOpenCvReady() {
    logDebug('OpenCV.js is ready');
    cv = window.cv;
    init();
}

// Check if OpenCV is already loaded (in case the script loads after OpenCV)
if (window.cv) {
    onOpenCvReady();
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
