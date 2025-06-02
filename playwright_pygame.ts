import { chromium, Browser, BrowserContext, Page } from 'playwright';
import { app, BrowserWindow, ipcMain } from 'electron';
import { EventEmitter } from 'events';

interface MouseCommand {
    action: string;
    x?: number;
    y?: number;
    button?: 'left' | 'middle' | 'right';
}

/**
 * JSEvaluator handles connection to the Chromium browser via Playwright
 * and exposes methods for controlling the Minecraft page.
 */
export class JSEvaluator {
    private playwright: any = null;
    private browser: Browser | null = null;
    private context: BrowserContext | null = null;
    public page: Page | null = null;
    public isConnected = false;
    private lastMouseX = 400;
    private lastMouseY = 300;

    async setup(): Promise<boolean> {
        this.playwright = await chromium.connectOverCDP('http://localhost:9222').catch(() => null);
        if (!this.playwright) {
            console.error('Failed to connect to browser');
            return false;
        }
        this.browser = this.playwright;

        if (!this.browser) {
            console.error('No browser instance available');
            return false;
        }

        const contexts = this.browser.contexts();
        let minecraftPage: Page | null = null;
        for (const context of contexts) {
            for (const page of context.pages()) {
                if (page.url().includes('mcraft.fun')) {
                    minecraftPage = page;
                    this.context = context;
                    break;
                }
            }
            if (minecraftPage) break;
        }
        if (!minecraftPage && contexts.length) {
            this.context = contexts[0];
            minecraftPage = this.context.pages()[0] || await this.context.newPage();
        }
        if (!minecraftPage) {
            console.error('No page found');
            return false;
        }
        this.page = minecraftPage;
        await this.checkAndActivateGame();
        await this.injectVisibleCursor();
        this.isConnected = true;
        return true;
    }

    async checkAndActivateGame() {
        if (!this.page) return;
        await this.page.evaluate(() => {
            const canvas = document.querySelector('canvas');
            if (canvas) {
                canvas.focus();
                (canvas as HTMLElement).click();
            }
        });
    }

    async injectVisibleCursor() {
        if (!this.page) return;
        await this.page.addStyleTag({
            content: `#playwright-cursor {position: fixed;width: 20px;height: 20px;background: rgba(255,0,0,0.8);border: 2px solid white;border-radius: 50%;pointer-events: none;z-index:10000;transform:translate(-50%,-50%);transition:none;box-shadow:0 0 10px rgba(255,0,0,0.6);}`,
        });
        await this.page.evaluate(() => {
            const existing = document.getElementById('playwright-cursor');
            if (existing) existing.remove();
            const cursor = document.createElement('div');
            cursor.id = 'playwright-cursor';
            cursor.style.display = 'none';
            document.body.appendChild(cursor);
            (window as any).playwrightCursor = cursor;
        });
    }

    async updateCursorPosition(x: number, y: number) {
        if (!this.page) return;
        await this.page.evaluate(([cx, cy]) => {
            const cursor = (window as any).playwrightCursor as HTMLElement | undefined;
            if (cursor) {
                cursor.style.left = `${cx}px`;
                cursor.style.top = `${cy}px`;
                cursor.style.display = 'block';
            }
        }, [x, y]);
    }

    async mouseMove(x: number, y: number) {
        if (!this.page) return;
        const deltaX = x - this.lastMouseX;
        const deltaY = y - this.lastMouseY;
        this.lastMouseX = x;
        this.lastMouseY = y;
        if (deltaX === 0 && deltaY === 0) return;
        await this.page.evaluate(([mx, my, dx, dy]) => {
            const canvas = document.querySelector('canvas');
            if (!canvas) return;
            const evt = new MouseEvent('mousemove', { bubbles: true, cancelable: true, view: window });
            Object.defineProperty(evt, 'movementX', { value: dx });
            Object.defineProperty(evt, 'movementY', { value: dy });
            Object.defineProperty(evt, 'clientX', { value: mx });
            Object.defineProperty(evt, 'clientY', { value: my });
            canvas.dispatchEvent(evt);
        }, [x, y, deltaX, deltaY]);
        await this.updateCursorPosition(x, y);
    }

    async mouseDown(button: 'left' | 'middle' | 'right' = 'left') {
        if (!this.page) return;
        const btn = button === 'left' ? 0 : button === 'middle' ? 1 : 2;
        const x = this.lastMouseX;
        const y = this.lastMouseY;
        await this.page.evaluate(([b, cx, cy]) => {
            const canvas = document.querySelector('canvas');
            if (!canvas) return;
            const evt = new MouseEvent('mousedown', { button: b, buttons: 1 << b, clientX: cx, clientY: cy, bubbles: true, cancelable: true });
            canvas.dispatchEvent(evt);
        }, [btn, x, y]);
    }

    async mouseUp(button: 'left' | 'middle' | 'right' = 'left') {
        if (!this.page) return;
        const btn = button === 'left' ? 0 : button === 'middle' ? 1 : 2;
        const x = this.lastMouseX;
        const y = this.lastMouseY;
        await this.page.evaluate(([b, cx, cy]) => {
            const canvas = document.querySelector('canvas');
            if (!canvas) return;
            const evt = new MouseEvent('mouseup', { button: b, buttons: 0, clientX: cx, clientY: cy, bubbles: true, cancelable: true });
            canvas.dispatchEvent(evt);
        }, [btn, x, y]);
    }

    async mouseDoubleClick(x: number, y: number, button: 'left' | 'middle' | 'right' = 'left') {
        if (!this.page) return;
        const btn = button === 'left' ? 0 : button === 'middle' ? 1 : 2;
        await this.page.evaluate(([cx, cy, b]) => {
            const canvas = document.querySelector('canvas');
            if (!canvas) return;
            const clickEvent = (type: string, detail = 1) => {
                return new MouseEvent(type, { button: b, buttons: type === 'mouseup' ? 0 : 1 << b, clientX: cx, clientY: cy, detail, bubbles: true, cancelable: true });
            };
            canvas.dispatchEvent(clickEvent('mousedown', 1));
            canvas.dispatchEvent(clickEvent('mouseup', 1));
            canvas.dispatchEvent(clickEvent('click', 1));
            setTimeout(() => {
                canvas.dispatchEvent(clickEvent('mousedown', 2));
                canvas.dispatchEvent(clickEvent('mouseup', 2));
                canvas.dispatchEvent(clickEvent('click', 2));
                canvas.dispatchEvent(clickEvent('dblclick', 2));
            }, 10);
        }, [x, y, btn]);
    }

    async close() {
        this.isConnected = false;
        if (this.page && !this.page.isClosed()) await this.page.close().catch(() => { });
        if (this.browser && this.browser.isConnected()) await this.browser.close().catch(() => { });
    }
}

/** Queue-based Playwright worker similar to the Python version */
class PlaywrightWorker extends EventEmitter {
    evaluator = new JSEvaluator();
    private queue: MouseCommand[] = [];
    private running = false;

    async start() {
        if (!(await this.evaluator.setup())) return;
        this.running = true;
        this.processLoop();
    }

    enqueue(cmd: MouseCommand) {
        this.queue.push(cmd);
    }

    private async processLoop() {
        while (this.running) {
            const cmd = this.queue.shift();
            if (cmd) {
                try {
                    await this.handleCommand(cmd);
                } catch (e) {
                    console.error('Worker error', e);
                }
            }
            await new Promise(r => setTimeout(r, 10));
        }
    }

    private async handleCommand(cmd: MouseCommand) {
        switch (cmd.action) {
            case 'move':
                await this.evaluator.mouseMove(cmd.x!, cmd.y!);
                break;
            case 'down':
                await this.evaluator.mouseDown(cmd.button);
                break;
            case 'up':
                await this.evaluator.mouseUp(cmd.button);
                break;
            case 'double_click':
                await this.evaluator.mouseDoubleClick(cmd.x!, cmd.y!, cmd.button);
                break;
            default:
                console.warn('Unknown command', cmd);
        }
    }
}

// --- Electron front-end to capture mouse events ---
let mainWindow: BrowserWindow | null = null;
const worker = new PlaywrightWorker();

function createWindow() {
    mainWindow = new BrowserWindow({ width: 1600, height: 1200, webPreferences: { nodeIntegration: true, contextIsolation: false } });
    mainWindow.loadURL('data:text/html,<html><body style="background:#202020;"></body><script>const { ipcRenderer } = require("electron");document.body.addEventListener("mousemove", e=>{ipcRenderer.send("mouse-move", e.clientX, e.clientY)});document.body.addEventListener("mousedown", e=>{ipcRenderer.send("mouse-down", e.button)});document.body.addEventListener("mouseup", e=>{ipcRenderer.send("mouse-up", e.button)});</script></html>');
    mainWindow.on('closed', () => { mainWindow = null; });
}

ipcMain.on('mouse-move', (_e, x: number, y: number) => worker.enqueue({ action: 'move', x, y }));
ipcMain.on('mouse-down', (_e, btn: number) => worker.enqueue({ action: 'down', button: btn === 0 ? 'left' : btn === 1 ? 'middle' : 'right' }));
ipcMain.on('mouse-up', (_e, btn: number) => worker.enqueue({ action: 'up', button: btn === 0 ? 'left' : btn === 1 ? 'middle' : 'right' }));

app.whenReady().then(async () => {
    createWindow();
    await worker.start();
});

app.on('window-all-closed', () => {
    worker.removeAllListeners();
    if (process.platform !== 'darwin') app.quit();
});

