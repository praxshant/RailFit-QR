# Custom Barcode Scanner

A web application for scanning and decoding custom 16-bar barcodes using HTML5, CSS, JavaScript, and OpenCV.js. The barcode consists of 16 vertical black bars with varying heights that represent hexadecimal digits (0-F).

## Features

- **Webcam Scanning**: Real-time barcode scanning using your device's camera
- **Image Upload**: Upload and process barcode images (JPEG, PNG)
- **Responsive Design**: Works on both desktop and mobile devices
- **Modern UI**: Clean, user-friendly interface with a purple theme
- **Debug Tools**: Built-in debug information for troubleshooting

## How It Works

The application processes barcodes with the following specifications:
- 16 vertical black bars with fixed width
- Variable heights representing hex digits (0-F)
- Bars are bottom-aligned on a white background
- Heights are normalized to 16 discrete levels (level 1 = 0, level 16 = F)

## Getting Started

### Prerequisites

- A modern web browser (Chrome, Firefox, Edge, or Safari)
- Webcam (for live scanning)
- Internet connection (only required for loading OpenCV.js)

### Running the Application

1. Clone or download this repository
2. Open `index.html` in your preferred web browser
3. Grant camera permissions when prompted (for webcam scanning)

### Using the Webcam Scanner

1. Click the "Start Camera" button
2. Position the barcode in front of your camera
3. Click "Scan Now" to capture and process the barcode
4. The decoded hex string will be displayed below

### Using Image Upload

1. Click the "Upload Image" tab
2. Drag and drop an image file or click to browse
3. The application will automatically process the image
4. The decoded hex string will be displayed below

## Barcode Format

- Each bar's height represents a hex digit (0-F)
- The barcode should be horizontally aligned
- The background should be white with black bars
- The barcode should be clearly visible and well-lit

## Troubleshooting

- **Camera not working**: Ensure you've granted camera permissions in your browser
- **No barcode detected**: Try adjusting the lighting or position of the barcode
- **Incorrect decoding**: Ensure the barcode is clearly visible and properly aligned
- **Debug information**: Use the "Toggle Debug Info" button to view detailed processing information

## Browser Compatibility

This application works best in modern browsers with WebAssembly support:
- Google Chrome (recommended)
- Mozilla Firefox
- Microsoft Edge
- Apple Safari

## License

This project is open source and available under the MIT License.

## Acknowledgments

- OpenCV.js for computer vision capabilities
- Font Awesome for icons
- Google Fonts for typography
