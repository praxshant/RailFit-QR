// frontend/src/app.js - QR-only system with role-based UI (Manufacturer, Vendor, Railway Official)
class RailwayQRApp {
    constructor() {
        const origin = window.location.origin || 'http://localhost:5000';
        this.apiBase = `${origin.replace(/\/$/, '')}/api`;
        this.currentUser = null;
        this.authToken = localStorage.getItem('railway_auth_token');
        this.eventsBound = false;

        this.initializeApp();
        this.setupEventListeners();
    }

    initializeApp() {
        if (this.authToken) {
            this.verifyToken();
        } else {
            this.showLogin();
        }
    }

    async verifyToken() {
        try {
            const response = await fetch(`${this.apiBase}/verify-token`, {
                headers: { 'Authorization': `Bearer ${this.authToken}` }
            });
            const result = await response.json();
            if (result.success) {
                this.currentUser = result.user;
                this.showDashboard(result.user.role);
                this.updateUserInfo(result.user);
            } else {
                localStorage.removeItem('railway_auth_token');
                this.showLogin();
            }
        } catch (error) {
            console.error('Token verification failed:', error);
            this.showLogin();
        }
    }

    setupEventListeners() {
        if (this.eventsBound) return; // avoid duplicate bindings
        // Login
        const loginForm = document.getElementById('login-form');
        if (loginForm) loginForm.addEventListener('submit', (e) => this.handleLogin(e));

        // Manufacturer
        const genForm = document.getElementById('qr-generator-form');
        if (genForm) genForm.addEventListener('submit', (e) => this.handleQRGeneration(e));

        // Vendor
        const searchForm = document.getElementById('parts-search-form');
        if (searchForm) searchForm.addEventListener('submit', (e) => this.handlePartsSearch(e));
        const summaryForm = document.getElementById('parts-summary-form');
        if (summaryForm) summaryForm.addEventListener('submit', (e) => this.handlePartsSummary(e));

        // Railway Official
        const uploadInput = document.getElementById('qr-upload');
        if (uploadInput) uploadInput.addEventListener('change', (e) => this.handleQRUpload(e));

        // Expose helpers
        window.app = this;
        this.eventsBound = true;
    }

    async handleLogin(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        const loginData = {
            username: formData.get('username'),
            password: formData.get('password'),
            role: formData.get('role')
        };
        if (!loginData.role) { alert('Please select your role'); return; }
        try {
            const res = await fetch(`${this.apiBase}/login`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(loginData)
            });
            const result = await res.json();
            console.log('Login response:', result);
            if (result.success) {
                this.authToken = result.token;
                this.currentUser = result.user;
                localStorage.setItem('railway_auth_token', this.authToken);
                this.showDashboard(result.user.role);
                this.updateUserInfo(result.user);
            } else {
                alert(result.message || 'Login failed');
            }
        } catch (e) {
            console.error('Login error:', e);
            alert('Login failed. Please try again.');
        }
    }

    showLogin() {
        this.toggleDisplay('login-section', true);
        this.toggleDisplay('manufacturer-section', false);
        this.toggleDisplay('vendor-section', false);
        this.toggleDisplay('official-section', false);
        this.toggleFlex('user-info', false);
    }

    showDashboard(role) {
        this.toggleDisplay('login-section', false);
        this.toggleFlex('user-info', true);
        this.toggleDisplay('manufacturer-section', role === 'manufacturer');
        this.toggleDisplay('vendor-section', role === 'vendor');
        this.toggleDisplay('official-section', role === 'railway_official');

        // Role-specific initializations
        if (role === 'manufacturer') {
            this.loadPartsSpecifications();
        }
        if (role === 'railway_official') {
            // Hide upload fallback and show webcam container immediately
            const uploadSection = document.querySelector('.upload-zone');
            if (uploadSection) uploadSection.style.display = 'none';
            const webcamContainer = document.getElementById('webcam-scanner-container');
            if (webcamContainer) webcamContainer.style.display = 'block';
            this.initializeWebcamScanner();
            // Warn if insecure origin blocks camera
            this.maybeShowCameraContextWarning();
        }
    }

    updateUserInfo(user) { const el = document.getElementById('user-name'); if (el) el.textContent = user.name; }

    toggleDisplay(id, show) { const el = document.getElementById(id); if (el) el.style.display = show ? 'block' : 'none'; }
    toggleFlex(id, show) { const el = document.getElementById(id); if (el) el.style.display = show ? 'flex' : 'none'; }

    // Manufacturer: Generate QR
    async handleQRGeneration(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        const itemData = Object.fromEntries(formData.entries());
        try {
            const res = await fetch(`${this.apiBase}/manufacturer/generate-qr`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify(itemData)
            });
            const result = await res.json();
            if (result.success) {
                this.displayGeneratedQR(result);
                event.target.reset();
            } else { alert('QR generation failed: ' + (result.error || 'Unknown error')); }
        } catch (e) {
            console.error('QR generation error:', e);
            alert('QR generation failed. Please try again.');
        }
    }

    displayGeneratedQR(result) {
        const qrResult = document.getElementById('qr-result');
        const qrImage = document.getElementById('qr-image');
        const qrRef = document.getElementById('qr-ref');
        if (qrImage) qrImage.src = `data:image/png;base64,${result.qr_image}`;
        if (qrRef) qrRef.textContent = result.qr_ref;
        if (qrResult) qrResult.style.display = 'block';
        this.currentQR = { ref: result.qr_ref, filename: result.filename, image: result.qr_image };
    }

    downloadQR() {
        if (this.currentQR) {
            const link = document.createElement('a');
            link.href = `data:image/png;base64,${this.currentQR.image}`;
            link.download = this.currentQR.filename;
            link.click();
        }
    }

    // Vendor: Search
    async handlePartsSearch(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        const searchData = Object.fromEntries(formData.entries());
        try {
            const res = await fetch(`${this.apiBase}/vendor/search-parts`, {
                method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.authToken}` },
                body: JSON.stringify(searchData)
            });
            const result = await res.json();
            if (result.success) this.displaySearchResults(result); else alert('Search failed: ' + (result.error || 'Unknown'));
        } catch (e) { console.error('Search error:', e); alert('Search failed. Please try again.'); }
    }

    displaySearchResults(result) {
        const resultsDiv = document.getElementById('search-results');
        const tableDiv = document.getElementById('results-table');
        if (!tableDiv) return;
        if (result.total_items === 0) {
            tableDiv.innerHTML = '<p>No parts found matching your criteria.</p>';
        } else {
            let html = `
                <h5>Found ${result.total_items} parts</h5>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Item ID</th>
                            <th>Type</th>
                            <th>Vendor Lot</th>
                            <th>Supply Date</th>
                            <th>UDM Link</th>
                            <th>TMS Link</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            result.items.forEach((item, idx) => {
                const udmLink = result.udm_links[idx];
                const tmsLink = result.tms_links[idx];
                html += `
                    <tr>
                        <td>${item.item_id}</td>
                        <td>${item.item_type}</td>
                        <td>${item.vendor_lot}</td>
                        <td>${item.supply_date}</td>
                        <td><a href="${udmLink.link}" target="_blank" class="btn-secondary">View UDM</a></td>
                        <td><a href="${tmsLink.link}" target="_blank" class="btn-secondary">View TMS</a></td>
                    </tr>`;
            });
            html += '</tbody></table>';
            tableDiv.innerHTML = html;
        }
        if (resultsDiv) resultsDiv.style.display = 'block';
    }

    // Vendor: Summary
    async handlePartsSummary(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        const partsListText = formData.get('parts_list');
        try {
            const partsList = partsListText ? JSON.parse(partsListText) : [];
            const res = await fetch(`${this.apiBase}/vendor/parts-summary`, {
                method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.authToken}` },
                body: JSON.stringify({ parts_list: partsList })
            });
            const result = await res.json();
            if (result.success) this.displaySummaryResult(result); else alert('Summary generation failed: ' + (result.error || 'Unknown'));
        } catch (e) { console.error('Summary error:', e); alert('Invalid JSON format or summary generation failed.'); }
    }

    displaySummaryResult(result) {
        const summaryDiv = document.getElementById('summary-result');
        if (!summaryDiv) return;
        const html = `
            <h4>Parts Summary Generated</h4>
            <div class="summary-info">
                <p><strong>Total Parts:</strong> ${result.summary.total_parts}</p>
                <p><strong>Generated At:</strong> ${new Date(result.summary.generated_at).toLocaleString()}</p>
                <p><strong>Database Sync:</strong> <span class="status-success">${result.summary.database_sync ? 'Success' : 'Failed'}</span></p>
                <p><strong>UDM Sync:</strong> <span class="status-success">${result.summary.udm_sync ? 'Success' : 'Failed'}</span></p>
                <p><strong>TMS Sync:</strong> <span class="status-success">${result.summary.tms_sync ? 'Success' : 'Failed'}</span></p>
            </div>
            <div class="sync-details">
                <h5>Sync Results:</h5>
                <pre>${JSON.stringify({ udm: result.udm_sync_result, tms: result.tms_sync_result }, null, 2)}</pre>
            </div>`;
        summaryDiv.innerHTML = html;
        summaryDiv.style.display = 'block';
    }

    // ------------------ Official: Upload-based scan (legacy, kept as fallback) ------------------
    async handleQRUpload(event) {
        const input = event.target;
        const file = input && input.files && input.files[0];
        if (!file) return;
        const progressDiv = document.getElementById('scan-progress');
        const resultsDiv = document.getElementById('scan-results');
        if (progressDiv) progressDiv.style.display = 'block';
        if (resultsDiv) resultsDiv.style.display = 'none';
        try {
            const formData = new FormData();
            formData.append('image', file);
            const res = await fetch(`${this.apiBase}/official/scan-qr`, { method: 'POST', headers: { 'Authorization': `Bearer ${this.authToken}` }, body: formData });
            const result = await res.json();
            if (result.success) this.displayScanResults(result); else this.displayScanError(result.error || 'Scan failed');
        } catch (e) { console.error('Scan error:', e); this.displayScanError('Scan failed. Please try again.'); }
        finally { if (progressDiv) progressDiv.style.display = 'none'; }
    }

    displayScanResults(result) {
        const resultsDiv = document.getElementById('scan-results');
        if (!resultsDiv) return;
        const s = result.scan_result || {};
        const html = `
            <h4>✅ QR Code Scanned Successfully</h4>
            <div class="scan-info">
                <h5>Scan Details:</h5>
                <p><strong>Confidence:</strong> ${(s.confidence ? (s.confidence * 100).toFixed(1) : 'N/A')}%</p>
                <p><strong>Quality Score:</strong> ${(s.quality_score ? (s.quality_score * 100).toFixed(1) : 'N/A')}%</p>
                <p><strong>Scanned By:</strong> ${result.scanned_by || ''}</p>
                <p><strong>Scan Time:</strong> ${new Date(result.scan_timestamp).toLocaleString()}</p>
            </div>
            <div class="item-details">
                <h5>Item Information:</h5>
                <table class="results-table">
                    <tr><td><strong>Item ID</strong></td><td>${result.item_data.item_id}</td></tr>
                    <tr><td><strong>Item Type</strong></td><td>${result.item_data.item_type}</td></tr>
                    <tr><td><strong>Vendor Lot</strong></td><td>${result.item_data.vendor_lot}</td></tr>
                    <tr><td><strong>Supply Date</strong></td><td>${result.item_data.supply_date}</td></tr>
                    <tr><td><strong>Warranty</strong></td><td>${result.item_data.warranty_period || 'N/A'}</td></tr>
                    <tr><td><strong>Manufacturer</strong></td><td>${result.item_data.manufacturer || 'N/A'}</td></tr>
                </table>
            </div>`;
        resultsDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
    }

    displayScanError(error) {
        const resultsDiv = document.getElementById('scan-results');
        if (!resultsDiv) return;
        resultsDiv.innerHTML = `
            <div class="scan-error">
                <h4>❌ Scan Failed</h4>
                <p>${error}</p>
                <p>Please ensure the image contains a clear QR code and try again.</p>
            </div>`;
        resultsDiv.style.display = 'block';
    }

    // ------------------ Official: Live webcam scanning with html5-qrcode ------------------
    async loadHtml5QrcodeLibrary() {
        return new Promise((resolve, reject) => {
            if (window.Html5Qrcode) return resolve();
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    maybeShowCameraContextWarning() {
        const statusDiv = document.getElementById('scanner-status');
        if (!statusDiv) return;
        const origin = window.location.origin;
        const isLocal = /^(https?:\/\/)?(localhost|127\.0\.0\.1)/i.test(origin);
        if (!window.isSecureContext && !isLocal) {
            statusDiv.innerHTML = '<div class="scanner-error"><span class="error-icon">⚠️</span><span>Camera is blocked on insecure origins. Use http://127.0.0.1:5000/web or enable HTTPS.</span></div>';
        }
    }

    initializeWebcamScanner() {
        // Ensure upload fallback hidden and webcam container visible
        const uploadSection = document.querySelector('.upload-zone');
        if (uploadSection) uploadSection.style.display = 'none';
        const scannerContainer = document.getElementById('webcam-scanner-container');
        if (scannerContainer) scannerContainer.style.display = 'block';
        // Bind controls
        const startBtn = document.getElementById('start-scan-btn');
        const stopBtn = document.getElementById('stop-scan-btn');
        const switchBtn = document.getElementById('switch-camera');
        if (startBtn && !startBtn._bound) { startBtn.addEventListener('click', () => this.startWebcamScanning()); startBtn._bound = true; }
        if (stopBtn && !stopBtn._bound) { stopBtn.addEventListener('click', () => this.stopWebcamScanning()); stopBtn._bound = true; }
        if (switchBtn && !switchBtn._bound) { switchBtn.addEventListener('click', () => this.switchCamera()); switchBtn._bound = true; }
        // Setup cameras
        this.setupWebcamScanner();
    }

    async setupWebcamScanner() {
        try {
            if (!window.Html5Qrcode) { await this.loadHtml5QrcodeLibrary(); }
            const cameraSelect = document.getElementById('camera-select');
            if (!cameraSelect) return;
            // Enumerate cameras
            const cameras = await Html5Qrcode.getCameras();
            if (cameras && cameras.length) {
                cameraSelect.innerHTML = '';
                // Prefer back/rear camera if available
                let preferred = cameras.find(c => (c.label || '').toLowerCase().includes('back') || (c.label || '').toLowerCase().includes('rear')) || cameras[0];
                cameras.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.id;
                    opt.textContent = c.label || `Camera ${c.id}`;
                    cameraSelect.appendChild(opt);
                });
                cameraSelect.value = preferred.id;
                // Show switch button if multiple
                const switchBtn = document.getElementById('switch-camera');
                if (switchBtn) switchBtn.style.display = cameras.length > 1 ? 'inline-block' : 'none';
            } else {
                cameraSelect.innerHTML = '<option value="">No cameras found</option>';
                this.showScannerError('No cameras detected. Please allow camera permission.');
            }
        } catch (e) {
            console.error('Webcam setup error:', e);
            this.showScannerError('Failed to initialize camera. Please check permissions.');
        }
    }

    async startWebcamScanning() {
        const cameraSelect = document.getElementById('camera-select');
        const selected = cameraSelect && cameraSelect.value;
        if (!selected) { this.showScannerError('Please select a camera'); return; }
        try {
            // Create or reuse scanner
            this.html5QrCode = new Html5Qrcode('qr-reader');
            const config = {
                fps: 15,
                qrbox: { width: 320, height: 320 },
                aspectRatio: 1.333,
                disableFlip: false,
                experimentalFeatures: { useBarCodeDetectorIfSupported: true }
            };
            if (window.Html5QrcodeSupportedFormats) {
                config.formatsToSupport = [Html5QrcodeSupportedFormats.QR_CODE];
            }
            await this.html5QrCode.start(selected, config, (decodedText) => {
                this.handleWebcamScanSuccess(decodedText);
            });
            const startBtn = document.getElementById('start-scan-btn');
            const stopBtn = document.getElementById('stop-scan-btn');
            if (startBtn) startBtn.style.display = 'none';
            if (stopBtn) stopBtn.style.display = 'inline-block';
            const qrBox = document.getElementById('qr-reader');
            if (qrBox) qrBox.classList.add('scanning');
            this.showScanningStatus(true);
        } catch (e) {
            console.error('Error starting scanner:', e);
            this.showScannerError(`Failed to start camera: ${e.message}`);
        }
    }

    async stopWebcamScanning() {
        try {
            if (this.html5QrCode) {
                await this.html5QrCode.stop();
                this.html5QrCode = null;
            }
        } catch (e) { console.warn('Stop error:', e); }
        const startBtn = document.getElementById('start-scan-btn');
        const stopBtn = document.getElementById('stop-scan-btn');
        if (startBtn) startBtn.style.display = 'inline-block';
        if (stopBtn) stopBtn.style.display = 'none';
        const qrBox = document.getElementById('qr-reader');
        if (qrBox) qrBox.classList.remove('scanning');
        this.showScanningStatus(false);
    }

    async switchCamera() {
        const select = document.getElementById('camera-select');
        if (!select || !select.options.length) return;
        await this.stopWebcamScanning();
        const nextIndex = (select.selectedIndex + 1) % select.options.length;
        select.selectedIndex = nextIndex;
        this.startWebcamScanning();
    }

    handleWebcamScanSuccess(decodedText) {
        // Stop scanning and give feedback
        this.stopWebcamScanning();
        this.showScanSuccess();
        const scanResult = { data: decodedText, confidence: 1.0, method: 'webcam_realtime', timestamp: new Date().toISOString(), quality_score: 0.95 };
        if (decodedText && decodedText.startsWith('INDIAN_RAILWAYS:')) {
            const qrRef = decodedText.replace('INDIAN_RAILWAYS:', '');
            this.processRailwayQRScan(qrRef, scanResult);
        } else {
            this.displayScanError('Not a valid Indian Railways QR code');
        }
    }

    async processRailwayQRScan(qrRef, scanResult) {
        try {
            this.showProcessingStatus();
            const res = await fetch(`${this.apiBase}/lookup/${qrRef}`, { headers: { 'Authorization': `Bearer ${this.authToken}` } });
            if (res.ok) {
                const itemData = await res.json();
                this.displayWebcamScanResults({ success: true, scan_result: scanResult, item_data: itemData, ai_insights: itemData.ai_insights || {}, scanned_by: this.currentUser && this.currentUser.name, scan_timestamp: new Date().toISOString() });
            } else {
                this.displayScanError('QR code not found in database');
            }
        } catch (e) {
            console.error('Process scan error:', e);
            this.displayScanError('Network error occurred while processing scan');
        }
    }

    displayWebcamScanResults(result) {
        const resultsDiv = document.getElementById('scan-results');
        if (!resultsDiv) return;
        resultsDiv.innerHTML = `
            <div class="scan-success-header">
                <h4>✅ QR Code Scanned Successfully</h4>
                <div class="scan-method-badge">📱 Live Camera Scan</div>
            </div>
            <div class="scan-metrics">
                <div class="metric"><span class="metric-label">Confidence:</span><span class="metric-value">${(result.scan_result.confidence * 100).toFixed(1)}%</span></div>
                <div class="metric"><span class="metric-label">Quality:</span><span class="metric-value">${(result.scan_result.quality_score * 100).toFixed(1)}%</span></div>
                <div class="metric"><span class="metric-label">Method:</span><span class="metric-value">${result.scan_result.method}</span></div>
            </div>
            <div class="item-details-card">
                <h5>🔧 Item Information</h5>
                <div class="details-grid">
                    <div class="detail-item"><strong>Item ID:</strong> ${result.item_data.item_id}</div>
                    <div class="detail-item"><strong>Type:</strong> ${result.item_data.item_type}</div>
                    <div class="detail-item"><strong>Vendor Lot:</strong> ${result.item_data.vendor_lot}</div>
                    <div class="detail-item"><strong>Supply Date:</strong> ${result.item_data.supply_date}</div>
                    <div class="detail-item"><strong>Manufacturer:</strong> ${result.item_data.manufacturer || 'N/A'}</div>
                    <div class="detail-item"><strong>Warranty:</strong> ${result.item_data.warranty_period || 'N/A'}</div>
                </div>
            </div>
        `;
        resultsDiv.style.display = 'block';
        resultsDiv.style.opacity = '0';
        resultsDiv.style.transform = 'translateY(20px)';
        setTimeout(() => {
            resultsDiv.style.transition = 'all 0.5s ease';
            resultsDiv.style.opacity = '1';
            resultsDiv.style.transform = 'translateY(0)';
        }, 50);
    }

    showScanSuccess() {
        const scanBox = document.getElementById('qr-reader');
        if (scanBox) {
            scanBox.style.border = '4px solid var(--railway-green)';
            scanBox.style.boxShadow = '0 0 20px rgba(40, 167, 69, 0.5)';
            setTimeout(() => { scanBox.style.border = ''; scanBox.style.boxShadow=''; }, 1200);
        }
        this.playNotificationSound('success');
    }

    showScanningStatus(isScanning) {
        const statusDiv = document.getElementById('scanner-status');
        if (!statusDiv) return;
        statusDiv.innerHTML = isScanning ? `
            <div class="scanning-status"><div class="scanning-animation"></div><span>🎯 Looking for QR codes... Point camera at QR code</span></div>
        ` : '';
    }

    showProcessingStatus() {
        const statusDiv = document.getElementById('scanner-status');
        if (!statusDiv) return;
        statusDiv.innerHTML = `<div class="processing-status"><div class="processing-spinner"></div><span>🔍 Processing QR code and fetching item data...</span></div>`;
    }

    showScannerError(message) {
        const statusDiv = document.getElementById('scanner-status');
        if (!statusDiv) return;
        statusDiv.innerHTML = `<div class="scanner-error"><span class="error-icon">⚠️</span><span>${message}</span></div>`;
        this.playNotificationSound('error');
    }

    playNotificationSound(type) {
        try {
            const AudioCtx = window.AudioContext || window.webkitAudioContext; if (!AudioCtx) return;
            const ctx = new AudioCtx(); const osc = ctx.createOscillator(); const gain = ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            if (type === 'success') { osc.frequency.value = 900; } else { osc.frequency.value = 300; }
            gain.gain.value = 0.1; osc.start(); setTimeout(() => { gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.2); osc.stop(); }, 200);
        } catch (e) { /* ignore */ }
    }

    logout() { localStorage.removeItem('railway_auth_token'); this.authToken = null; this.currentUser = null; this.showLogin(); }
}

// Global helpers
function logout() { if (window.app) window.app.logout(); }
function downloadQR() { if (window.app) window.app.downloadQR(); }
function showSection(section) { console.log('Navigate:', section); }

document.addEventListener('DOMContentLoaded', () => { window.app = new RailwayQRApp(); });
