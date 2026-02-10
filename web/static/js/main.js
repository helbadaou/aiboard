    /**
 * AI Drawing Board - Web Version
 * Hand tracking drawing application using MediaPipe
 */

class AIDrawingBoard {
    constructor() {
        // DOM elements
        this.video = document.getElementById('video');
        this.drawingCanvas = document.getElementById('drawing-canvas');
        this.overlayCanvas = document.getElementById('overlay-canvas');
        this.statusEl = document.getElementById('status');
        this.brushSizeInput = document.getElementById('brush-size');
        this.brushSizeValue = document.getElementById('brush-size-value');
        
        // Canvas contexts
        this.drawingCtx = this.drawingCanvas.getContext('2d');
        this.overlayCtx = this.overlayCanvas.getContext('2d');
        
        // Drawing state
        this.currentColor = '#00ff00';
        this.brushSize = 5;
        this.prevPoint = null;
        this.isDrawing = false;
        
        // Text objects array
        this.textObjects = [];
        this.selectedText = null;
        this.fontSize = 32;
        this.isDragging = false;
        
        // Hand tracking
        this.hands = null;
        this.camera = null;
        
        // Initialize
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        await this.setupCamera();
        await this.setupHandTracking();
    }
    
    setupEventListeners() {
        // Color buttons
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.color-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentColor = btn.dataset.color;
            });
        });
        
        // Brush size
        this.brushSizeInput.addEventListener('input', (e) => {
            this.brushSize = parseInt(e.target.value);
            this.brushSizeValue.textContent = this.brushSize;
        });
        
        // Font size
        const fontSizeInput = document.getElementById('font-size');
        const fontSizeValue = document.getElementById('font-size-value');
        fontSizeInput.addEventListener('input', (e) => {
            this.fontSize = parseInt(e.target.value);
            fontSizeValue.textContent = this.fontSize;
        });
        
        // Add text button
        document.getElementById('add-text-btn').addEventListener('click', () => {
            this.addText();
        });
        
        // Clear button
        document.getElementById('clear-btn').addEventListener('click', () => {
            this.clearCanvas();
        });
        
        // Save button
        document.getElementById('save-btn').addEventListener('click', () => {
            this.saveDrawing();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'c' || e.key === 'C') {
                this.clearCanvas();
            } else if (e.key === '+' || e.key === '=') {
                this.brushSize = Math.min(50, this.brushSize + 2);
                this.brushSizeInput.value = this.brushSize;
                this.brushSizeValue.textContent = this.brushSize;
            } else if (e.key === '-') {
                this.brushSize = Math.max(1, this.brushSize - 2);
                this.brushSizeInput.value = this.brushSize;
                this.brushSizeValue.textContent = this.brushSize;
            }
        });
    }
    
    async setupCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                }
            });
            
            this.video.srcObject = stream;
            
            await new Promise((resolve) => {
                this.video.onloadedmetadata = () => {
                    this.video.play();
                    resolve();
                };
            });
            
            // Set canvas sizes to match video
            this.resizeCanvases();
            window.addEventListener('resize', () => this.resizeCanvases());
            
            this.updateStatus('Camera ready, loading hand tracking...', '');
            
        } catch (error) {
            console.error('Camera error:', error);
            this.updateStatus('Camera access denied', 'error');
        }
    }
    
    resizeCanvases() {
        const container = document.getElementById('canvas-container');
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        this.drawingCanvas.width = width;
        this.drawingCanvas.height = height;
        this.overlayCanvas.width = width;
        this.overlayCanvas.height = height;
    }
    
    async setupHandTracking() {
        try {
            this.hands = new Hands({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1675469240/${file}`;
                }
            });
            
            this.hands.setOptions({
                maxNumHands: 1,
                modelComplexity: 1,
                minDetectionConfidence: 0.7,
                minTrackingConfidence: 0.7
            });
            
            this.hands.onResults((results) => this.onHandResults(results));
            
            // Start camera feed
            this.camera = new Camera(this.video, {
                onFrame: async () => {
                    await this.hands.send({ image: this.video });
                },
                width: 1280,
                height: 720
            });
            
            await this.camera.start();
            
            this.updateStatus('Ready! Show your hand to draw', 'ready');
            
        } catch (error) {
            console.error('Hand tracking error:', error);
            this.updateStatus('Hand tracking failed to load', 'error');
        }
    }
    
    onHandResults(results) {
        // Clear overlay
        this.overlayCtx.clearRect(0, 0, this.overlayCanvas.width, this.overlayCanvas.height);
        
        // Always redraw text objects
        this.redrawTextObjects();
        
        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            const landmarks = results.multiHandLandmarks[0];
            
            // Draw hand landmarks
            this.drawHandLandmarks(landmarks);
            
            // Get finger states
            const gesture = this.detectGesture(landmarks);
            
            // Get index finger position
            const indexTip = landmarks[8];
            const x = indexTip.x * this.drawingCanvas.width;
            const y = indexTip.y * this.drawingCanvas.height;
            
            if (gesture === 'pinching') {
                // Pinch gesture - grab and move text
                this.handlePinchGesture(x, y, landmarks);
                this.drawCursor(x, y, '#ff00ff');
                this.showGestureIndicator('🤏 Grabbing');
            } else if (gesture === 'drawing') {
                this.isDragging = false;
                this.selectedText = null;
                this.draw(x, y);
                this.drawCursor(x, y, this.currentColor);
                this.showGestureIndicator('✏️ Drawing');
            } else if (gesture === 'moving') {
                this.isDragging = false;
                this.selectedText = null;
                this.stopDrawing();
                this.drawCursor(x, y, '#ffffff');
                this.showGestureIndicator('✌️ Moving');
            } else {
                this.isDragging = false;
                this.selectedText = null;
                this.stopDrawing();
                this.showGestureIndicator('🖐️ Paused');
            }
        } else {
            this.isDragging = false;
            this.selectedText = null;
            this.stopDrawing();
            this.showGestureIndicator('👋 Show hand');
        }
    }
    
    drawHandLandmarks(landmarks) {
        const ctx = this.overlayCtx;
        const w = this.overlayCanvas.width;
        const h = this.overlayCanvas.height;
        
        // Draw connections
        const connections = [
            [0, 1], [1, 2], [2, 3], [3, 4],     // Thumb
            [0, 5], [5, 6], [6, 7], [7, 8],     // Index
            [0, 9], [9, 10], [10, 11], [11, 12], // Middle
            [0, 13], [13, 14], [14, 15], [15, 16], // Ring
            [0, 17], [17, 18], [18, 19], [19, 20], // Pinky
            [5, 9], [9, 13], [13, 17]             // Palm
        ];
        
        ctx.strokeStyle = 'rgba(0, 200, 0, 0.6)';
        ctx.lineWidth = 2;
        
        for (const [start, end] of connections) {
            ctx.beginPath();
            ctx.moveTo(landmarks[start].x * w, landmarks[start].y * h);
            ctx.lineTo(landmarks[end].x * w, landmarks[end].y * h);
            ctx.stroke();
        }
        
        // Draw landmarks
        ctx.fillStyle = 'rgba(0, 255, 0, 0.8)';
        for (const lm of landmarks) {
            ctx.beginPath();
            ctx.arc(lm.x * w, lm.y * h, 5, 0, 2 * Math.PI);
            ctx.fill();
        }
    }
    
    detectGesture(landmarks) {
        // Finger tip and pip landmarks
        // Index: tip=8, pip=6
        // Middle: tip=12, pip=10
        // Ring: tip=16, pip=14
        // Pinky: tip=20, pip=18
        // Thumb: tip=4
        
        const indexUp = landmarks[8].y < landmarks[6].y;
        const middleUp = landmarks[12].y < landmarks[10].y;
        const ringUp = landmarks[16].y < landmarks[14].y;
        const pinkyUp = landmarks[20].y < landmarks[18].y;
        
        // Check for pinch gesture (thumb tip close to index tip)
        const thumbTip = landmarks[4];
        const indexTip = landmarks[8];
        const pinchDistance = Math.sqrt(
            Math.pow(thumbTip.x - indexTip.x, 2) + 
            Math.pow(thumbTip.y - indexTip.y, 2)
        );
        
        // Pinch: thumb and index finger tips are close together
        if (pinchDistance < 0.05) {
            return 'pinching';
        }
        
        // Drawing: only index finger up
        if (indexUp && !middleUp && !ringUp && !pinkyUp) {
            return 'drawing';
        }
        
        // Moving: index and middle up (peace sign)
        if (indexUp && middleUp && !ringUp && !pinkyUp) {
            return 'moving';
        }
        
        // Open palm or other gesture
        return 'paused';
    }
    
    draw(x, y) {
        if (this.prevPoint) {
            this.drawingCtx.beginPath();
            this.drawingCtx.strokeStyle = this.currentColor;
            this.drawingCtx.lineWidth = this.brushSize;
            this.drawingCtx.lineCap = 'round';
            this.drawingCtx.lineJoin = 'round';
            this.drawingCtx.moveTo(this.prevPoint.x, this.prevPoint.y);
            this.drawingCtx.lineTo(x, y);
            this.drawingCtx.stroke();
        }
        
        this.prevPoint = { x, y };
    }
    
    stopDrawing() {
        this.prevPoint = null;
    }
    
    drawCursor(x, y, color) {
        const ctx = this.overlayCtx;
        
        // Draw cursor circle
        ctx.beginPath();
        ctx.arc(x, y, this.brushSize / 2 + 5, 0, 2 * Math.PI);
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Draw center dot
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fillStyle = color;
        ctx.fill();
    }
    
    showGestureIndicator(text) {
        let indicator = document.getElementById('gesture-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'gesture-indicator';
            document.getElementById('canvas-container').appendChild(indicator);
        }
        indicator.textContent = text;
    }
    
    clearCanvas() {
        this.drawingCtx.clearRect(0, 0, this.drawingCanvas.width, this.drawingCanvas.height);
        this.textObjects = [];
        this.selectedText = null;
        this.prevPoint = null;
    }
    
    addText() {
        const textInput = document.getElementById('text-input');
        const text = textInput.value.trim();
        if (!text) return;
        
        // Add text at center of canvas
        const textObj = {
            id: Date.now(),
            text: text,
            x: this.drawingCanvas.width / 2,
            y: this.drawingCanvas.height / 2,
            color: this.currentColor,
            fontSize: this.fontSize
        };
        
        this.textObjects.push(textObj);
        this.redrawTextObjects();
    }
    
    redrawTextObjects() {
        // Draw all text objects on the overlay canvas
        const ctx = this.overlayCtx;
        
        for (const textObj of this.textObjects) {
            ctx.font = `bold ${textObj.fontSize}px Arial`;
            ctx.fillStyle = textObj.color;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            // Draw text outline for visibility
            ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
            ctx.lineWidth = 3;
            ctx.strokeText(textObj.text, textObj.x, textObj.y);
            ctx.fillText(textObj.text, textObj.x, textObj.y);
            
            // Highlight selected text
            if (this.selectedText && this.selectedText.id === textObj.id) {
                const metrics = ctx.measureText(textObj.text);
                const width = metrics.width + 20;
                const height = textObj.fontSize + 10;
                
                ctx.strokeStyle = '#ff00ff';
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.strokeRect(
                    textObj.x - width / 2, 
                    textObj.y - height / 2, 
                    width, 
                    height
                );
                ctx.setLineDash([]);
            }
        }
    }
    
    handlePinchGesture(x, y, landmarks) {
        // Use the midpoint between thumb and index as grab point
        const thumbTip = landmarks[4];
        const indexTip = landmarks[8];
        const grabX = ((thumbTip.x + indexTip.x) / 2) * this.drawingCanvas.width;
        const grabY = ((thumbTip.y + indexTip.y) / 2) * this.drawingCanvas.height;
        
        if (!this.isDragging) {
            // Try to select a text object
            this.selectedText = this.findTextAt(grabX, grabY);
            if (this.selectedText) {
                this.isDragging = true;
            }
        }
        
        if (this.isDragging && this.selectedText) {
            // Move the selected text
            this.selectedText.x = grabX;
            this.selectedText.y = grabY;
        }
        
        this.stopDrawing();
    }
    
    findTextAt(x, y) {
        // Find a text object at the given position (reverse order for top-most first)
        for (let i = this.textObjects.length - 1; i >= 0; i--) {
            const textObj = this.textObjects[i];
            
            // Calculate text bounds
            this.overlayCtx.font = `bold ${textObj.fontSize}px Arial`;
            const metrics = this.overlayCtx.measureText(textObj.text);
            const width = metrics.width + 40; // Extra padding for easier selection
            const height = textObj.fontSize + 20;
            
            if (x >= textObj.x - width / 2 && 
                x <= textObj.x + width / 2 &&
                y >= textObj.y - height / 2 && 
                y <= textObj.y + height / 2) {
                return textObj;
            }
        }
        return null;
    }
    
    saveDrawing() {
        // Create a temporary canvas to combine video and drawing
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.drawingCanvas.width;
        tempCanvas.height = this.drawingCanvas.height;
        const tempCtx = tempCanvas.getContext('2d');
        
        // Draw video frame (mirrored)
        tempCtx.save();
        tempCtx.scale(-1, 1);
        tempCtx.drawImage(this.video, -tempCanvas.width, 0, tempCanvas.width, tempCanvas.height);
        tempCtx.restore();
        
        // Draw the drawing canvas on top (also mirrored to match)
        tempCtx.save();
        tempCtx.scale(-1, 1);
        tempCtx.drawImage(this.drawingCanvas, -tempCanvas.width, 0);
        tempCtx.restore();
        
        // Create download link
        const link = document.createElement('a');
        link.download = `drawing-${Date.now()}.png`;
        link.href = tempCanvas.toDataURL('image/png');
        link.click();
    }
    
    updateStatus(text, className) {
        this.statusEl.textContent = text;
        this.statusEl.className = className || '';
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new AIDrawingBoard();
});
