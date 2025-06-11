// =======================================================================
// === Porting Infrastructure (Pygame, OS, etc. shims)
// =======================================================================

// --- Pygame Constants and Input Shim ---
export const WINDOW_WIDTH = 800;
export const WINDOW_HEIGHT = 600;
export const FPS = 60;

export const COLORS = {
    BLACK: [0, 0, 0],
    WHITE: [255, 255, 255],
    RED: [255, 0, 0],
    GREEN: [0, 255, 0],
    BLUE: [0, 0, 255],
    GRAY: [128, 128, 128],
    DARK_GRAY: [40, 40, 40],
    LIGHT_GRAY: [200, 200, 200],
    CYAN: [0, 255, 255],
    YELLOW: [255, 255, 0],
    JOYSTICK_BASE: [80, 80, 80, 150],
    JOYSTICK_KNOB: [120, 120, 120, 255],
    BUTTON_IDLE: [100, 100, 100],
    BUTTON_HOVER: [130, 130, 130],
    BUTTON_PRESSED: [80, 180, 80],
    TOGGLE_ON: [80, 200, 80],
    TOGGLE_OFF: [200, 80, 80],
    CAMERA_AREA: [50, 50, 70, 100],
    TEXT_COLOR: [230, 230, 230],
    CONNECTION_STATUS_OK: [0, 255, 0],
    CONNECTION_STATUS_FAIL: [255, 0, 0],
};

export function toCssColor(c, alpha = 1) {
    if (c.length === 4) return `rgba(${c[0]}, ${c[1]}, ${c[2]}, ${c[3] / 255})`;
    return `rgba(${c[0]}, ${c[1]}, ${c[2]}, ${alpha})`;
}

export const Keys = {
    K_1: '1',
    K_2: '2',
    K_3: '3',
    K_4: '4',
    K_5: '5',
    K_6: '6',
    K_7: '7',
    K_8: '8',
    K_9: '9',
    K_q: 'q',
    K_w: 'w',
    K_e: 'e',
    K_a: 'a',
    K_s: 's',
    K_d: 'd',
    K_f: 'f',
    K_g: 'g',
    K_r: 'r',
    K_z: 'z',
    K_x: 'x',
    K_c: 'c',
    K_LCTRL: 'Control',
    K_LSHIFT: 'Shift',
    K_TAB: 'Tab',
    K_SPACE: ' ',
    K_ESCAPE: 'Escape',
    K_F5: 'F5',
    K_F6: 'F6',
    K_F7: 'F7',
};

// --- Global Input State Manager ---
export class InputManager {
    constructor(canvas) {
        this.keysPressed = new Set();
        this.mousePos = { x: 0, y: 0 };
        this.mouseLeftPressed = false;

        window.addEventListener('keydown', e => this.keysPressed.add(e.key));
        window.addEventListener('keyup', e => this.keysPressed.delete(e.key));
        canvas.addEventListener('mousemove', e => {
            const rect = canvas.getBoundingClientRect();
            this.mousePos.x = e.clientX - rect.left;
            this.mousePos.y = e.clientY - rect.top;
        });
        canvas.addEventListener('mousedown', e => {
            if (e.button === 0) this.mouseLeftPressed = true;
        });
        canvas.addEventListener('mouseup', e => {
            if (e.button === 0) this.mouseLeftPressed = false;
        });
    }

    getPressed() {
        // Mimics pygame.key.get_pressed() using a Proxy for easy checking
        return new Proxy({}, {
            get: (target, prop) => this.keysPressed.has(prop)
        });
    }

    getMousePos() {
        return [this.mousePos.x, this.mousePos.y];
    }

    getMousePressed() {
        // [left, middle, right]
        return [this.mouseLeftPressed, false, false];
    }
}

// --- Drawing Helpers ---
export class PygameDraw {
    constructor(ctx) {
        this.ctx = ctx;
    }
    rect(surface, color, [x, y, w, h], width = 0, borderRadius = 0) {
        this.ctx.fillStyle = toCssColor(color);
        this.ctx.strokeStyle = toCssColor(color);
        this.ctx.lineWidth = width;
        if (width > 0) {
            this.ctx.strokeRect(x, y, w, h);
        } else {
            this.ctx.fillRect(x, y, w, h);
        }
    }
    circle(surface, color, [x, y], radius, width = 0) {
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, 2 * Math.PI);
        this.ctx.fillStyle = toCssColor(color);
        this.ctx.strokeStyle = toCssColor(color);
        this.ctx.lineWidth = width > 0 ? width : 1;
        if (width === 0) {
            this.ctx.fill();
        } else {
            this.ctx.stroke();
        }
    }
}

// --- OS/File Shim for Browser ---
export class BrowserFileHandler {
    static createDownloadLink(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.textContent = `Download ${filename}`;
        a.style.display = 'block';
        a.style.marginTop = '5px';
        a.onclick = () => setTimeout(() => URL.revokeObjectURL(url), 100);
        return a;
    }

    static saveScreenshotFile(base64Data, sessionId, toolName) {
        const logArea = document.getElementById('data-collection-log');
        if (!logArea) return;

        const byteString = atob(base64Data);
        const mimeString = 'image/png';
        const ab = new ArrayBuffer(byteString.length);
        const ia = new Uint8Array(ab);
        for (let i = 0; i < byteString.length; i++) {
            ia[i] = byteString.charCodeAt(i);
        }
        const blob = new Blob([ab], { type: mimeString });
        const filename = `${Math.floor(Date.now() / 1000)}_${toolName}.png`;

        const link = this.createDownloadLink(blob, filename);
        logArea.appendChild(link);
        logArea.scrollTop = logArea.scrollHeight;

        return filename;
    }

    static downloadLog(content, filename) {
        const blob = new Blob([content], { type: 'text/plain' });
        const link = this.createDownloadLink(blob, filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}