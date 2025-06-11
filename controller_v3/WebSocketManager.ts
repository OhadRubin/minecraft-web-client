import { WebSocketCommand, WebSocketStatus, ConnectionStatus } from './types.js';

export interface WebSocketManagerOptions {
    url: string;
    onStatusChange?: (status: WebSocketStatus) => void;
    onMessage?: (data: any) => void;
    onError?: (error: Event) => void;
}

export class WebSocketManager {
    private websocket: WebSocket | null = null;
    private url: string;
    private connected: boolean = false;
    private reconnectTimer: number | null = null;
    private reconnectAttempts: number = 0;
    private maxReconnectAttempts: number = 5;
    private reconnectDelay: number = 1000;

    // Callbacks
    private onStatusChange?: (status: WebSocketStatus) => void;
    private onMessage?: (data: any) => void;
    private onError?: (error: Event) => void;

    constructor(options: WebSocketManagerOptions) {
        this.url = options.url;
        this.onStatusChange = options.onStatusChange;
        this.onMessage = options.onMessage;
        this.onError = options.onError;
    }

    public async connect(): Promise<void> {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            console.log("⚠️ WebSocket already connected");
            return;
        }

        try {
            console.log("🔌 Connecting to WebSocket...");
            this.websocket = new WebSocket(this.url);

            this.websocket.onopen = this.handleOpen.bind(this);
            this.websocket.onclose = this.handleClose.bind(this);
            this.websocket.onerror = this.handleError.bind(this);
            this.websocket.onmessage = this.handleMessage.bind(this);

        } catch (error) {
            console.error("❌ Failed to create WebSocket:", error);
            this.connected = false;
            this.notifyStatusChange();
        }
    }

    private async handleOpen(): Promise<void> {
        console.log("✅ WebSocket opened");
        this.reconnectAttempts = 0;
        
        // Clear any existing reconnect timer
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        // Register as pygame client
        const initMsg = { init: "pygame" };
        await this.send(initMsg);
        console.log("✅ Registered as pygame client");

        // Send gamepad connect command
        await this.sendCommand({ type: "gamepadConnect" });
        
        this.connected = true;
        this.notifyStatusChange();
    }

    private handleClose(): void {
        console.log("❌ WebSocket disconnected");
        this.connected = false;
        this.websocket = null;
        this.notifyStatusChange();

        // Attempt to reconnect
        this.scheduleReconnect();
    }

    private handleError(error: Event): void {
        console.error("❌ WebSocket error:", error);
        this.connected = false;
        this.notifyStatusChange();
        
        if (this.onError) {
            this.onError(error);
        }
    }

    private handleMessage(event: MessageEvent): void {
        try {
            const data = JSON.parse(event.data);
            console.log("📥 Received:", data);
            
            if (this.onMessage) {
                this.onMessage(data);
            }
        } catch (error) {
            console.error("❌ Error parsing message:", error);
        }
    }

    private scheduleReconnect(): void {
        if (this.reconnectTimer || this.reconnectAttempts >= this.maxReconnectAttempts) {
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`🔄 Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
        
        this.reconnectTimer = window.setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, delay);
    }

    public async send(data: any): Promise<void> {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            console.warn("⚠️ Cannot send - WebSocket not connected");
            return;
        }

        try {
            this.websocket.send(JSON.stringify(data));
            console.log("📤 Sent:", data);
        } catch (error) {
            console.error("❌ Error sending data:", error);
        }
    }

    public async sendCommand(command: WebSocketCommand): Promise<void> {
        // Log to server console
        this.logToServer(`📤 sendCommand called with: ${JSON.stringify(command)}`);
        
        await this.send(command);
    }

    public disconnect(): void {
        console.log("🔌 Disconnecting WebSocket...");
        
        // Clear reconnect timer
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        // Close websocket
        if (this.websocket) {
            // Send destroy command before closing
            if (this.websocket.readyState === WebSocket.OPEN) {
                this.send({ type: "gamepadDestroy" });
            }
            
            this.websocket.close();
            this.websocket = null;
        }

        this.connected = false;
        this.notifyStatusChange();
    }

    public isConnected(): boolean {
        return this.connected;
    }

    public getReadyState(): number {
        return this.websocket ? this.websocket.readyState : WebSocket.CLOSED;
    }

    private notifyStatusChange(): void {
        if (this.onStatusChange) {
            const status: WebSocketStatus = {
                connected: this.connected,
                reconnectAttempts: this.reconnectAttempts,
                readyState: this.getReadyState()
            };
            this.onStatusChange(status);
        }
    }

    // Set connection status handler
    public setConnectionHandler(handler: (status: ConnectionStatus) => void): void {
        // Convert WebSocketStatus to ConnectionStatus
        this.onStatusChange = (status: WebSocketStatus) => {
            if (status.connected) {
                handler(ConnectionStatus.Connected);
            } else if (status.reconnectAttempts > 0 && status.reconnectAttempts < this.maxReconnectAttempts) {
                handler(ConnectionStatus.Connecting);
            } else if (status.readyState === WebSocket.CLOSED) {
                handler(ConnectionStatus.Disconnected);
            } else {
                handler(ConnectionStatus.Error);
            }
        };
    }

    // Log to server console via HTTP request
    private logToServer(message: string): void {
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] ${message}`;
        
        // Send to server log endpoint
        fetch('/log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: logMessage })
        }).catch(error => {
            // Silent fail - don't log fetch errors to avoid recursion
            console.log(`Failed to log to server: ${error.message}`);
        });
        
        // Also log to browser console
        console.log(logMessage);
    }

    // Cleanup method
    public destroy(): void {
        this.disconnect();
        this.onStatusChange = undefined;
        this.onMessage = undefined;
        this.onError = undefined;
    }
}