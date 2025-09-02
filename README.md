# QR on Track: AI-Enabled TrackFit Scanner

**Hinglish Name**: Railfit Bar Scanner  
**Purpose**: A smart system for Indian Railways to mark QR codes on track fittings (metal clips, rubber pads, concrete sleepers) and track them using an AI-powered mobile app with augmented reality (AR). It connects to railway portals (UDM and TMS) to monitor quality, manage inventory, and ensure safety. Built for Smart India Hackathon 2025.

**Team**: 6 members (2 Hardware, 2 Machine Learning, 2 Full-Stack).

## What We’re Building

### Hardware: 2D Laser Marking System
**What It Does**: A small machine that etches tiny QR codes (5–10mm) on railway fittings to store info like vendor, supply date, and inspections.

**Parts**:
- **ESP32 Chip** (~₹400–800): Controls the system and uses Wi-Fi to send data.
- **Two Nema-17 Motors** (~₹1,200 each): Moves the laser to draw QR codes.
- **Engraver-2 Laser** (10W, ~₹8,000–16,000): Etches codes on metal, rubber, and concrete.
- **Aluminum Frame** (20x20cm, ~₹2,000): Holds everything together.
- **Camera (OV2640)** (~₹400): Checks if the fitting is metal, rubber, or concrete to adjust the laser.
- **Battery (12V)** (~₹2,000): Makes it portable for field tests.
- **Enclosure** (~₹1,000): Keeps the laser safe and dust/water-proof.

**How It Works**:
- The ESP32 moves the laser to etch QR codes on fittings, guided by the motors.
- The camera tells the system what material it’s marking, and AI adjusts the laser for clear codes.
- A feeder moves fittings under the laser (1–2 seconds per code).
- Wi-Fi sends marking logs to a database, and the battery lets it work anywhere.

**Why It’s Great**:
- Works on different materials without manual tweaks.
- Cheap (~₹20,000–30,000) and portable for railway depots.
- Safe and tough for outdoor use.

### Software: AI-Powered QR Scanner and Management
**What It Does**: A phone app and website that scan QR codes, show fitting details, predict problems with AI, and use AR to help workers in the field.

**Parts**:
1. **Website**:
   - Scans QR codes with a phone camera, showing vendor, supply date, warranty, and inspection info.
   - Works offline and supports English/Hindi.
   - Connects to UDM (www.ireps.gov.in) and TMS (www.irecept.gov.in) for data.
2. **AI Engine (Python)**:
   - Predicts faulty fittings (using XGBoost).
   - Spots unusual issues (DBSCAN) and predicts low stock (ARIMA).
   - Learns from worker inputs (e.g., “clip is rusted”) to get smarter.
3. **AR Interface (ARCore/ARKit)**:
   - Shows fitting info as 3D overlays on a phone or AR glasses (e.g., red flag for faulty parts).
   - Guides workers with arrows to fix issues.
   - Takes voice commands (BERT) like “Show defective clips.”
4. **Web Dashboard (Django/React)**:
   - Shows graphs of quality trends and inventory.
   - Sends email/SMS alerts for problems (e.g., low stock).
   - Securely syncs with UDM/TMS.

**How It Works**:
- Workers scan a fitting’s QR code to see its details.
- AI checks for issues (e.g., bad batches) and predicts stock needs.
- AR shows info right on the fitting, and voice commands make it hands-free.
- The dashboard helps managers see trends and get alerts.
- Worker feedback improves the AI over time.

**Why It’s Awesome**:
- AR and voice commands make fieldwork easy and modern.
- AI prevents accidents by catching problems early.
- Works on cheap phones and scales to millions of fittings.

### Deliverables
- **Hardware**: A laser system marking QR codes on 500 sample fittings.
- **Software**: A Website with QR scanning, AR, and AI, plus a web dashboard.
- **Integration**: Mock connection to UDM/TMS for data and alerts.

## Team Roles

### Hardware Engineers
- **Lead Hardware Developer**:
  - Build/program the ESP32, motors, and laser for QR marking.
  - Test on sample fittings (metal, rubber, concrete).
- **Hardware Testing and Safety**:
  - Add camera, battery, and safe enclosure.
  - Test QR codes for readability and durability.
- **Tools**: Soldering kit, multimeter, Arduino IDE, 3D printer (optional).

### Machine Learning Engineers
- **AI Model Developer**:
  - Build AI to detect materials and predict quality/inventory issues.
  - Deploy models on cloud (AWS/GCP).
- **NLP and Feedback Specialist**:
  - Add voice commands and AI feedback loop.
  - Optimize for edge devices (e.g., Raspberry Pi).
- **Tools**: Python, TensorFlow, OpenCV, Hugging Face, Colab.

### Full-Stack Developers
- **Frontend Developer**:
  - Build React app with QR scanning and AR.
  - Add offline storage and English/Hindi UI.
- **Backend and Dashboard Developer**:
  - Create backend and React dashboard.
  - Mock UDM/TMS APIs and add alerts.
- **Tools**: Django, React, Postman, VS Code.

## Feasibility
- **Cost**: ~₹20,000–30,000 (ESP32: ₹800, Nema-17: ₹2,400, Engraver-2: ₹10,000, frame/camera/battery: ₹7,000).
- **Resources**: Buy from Robu.in or Amazon India. Use free tools (Flutter, Python) and datasets (Roboflow QR, Kaggle Barcode, Rail-5k).
- **Scalability**: Wi-Fi and cloud make it work for millions of fittings.
- **Hackathon Fit**: Buildable in 3–4 months, innovative with AR/AI.
