import { WebSocketCommand, WebSocketStatus, ConnectionStatus, JoystickSession, MovementReport, BotStatusMessage, StoredScreenshot, WebSocketMessage } from './types.js';

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

    // Movement accumulation tracking
    private movementSessions: Map<number, JoystickSession> = new Map();
    private reportTimer: number | null = null;
    private reportInterval: number = 2000; // Report every 2 seconds

    // Bot status and screenshot tracking
    private lastBotStatus: BotStatusMessage['data'] | null = null;
    private screenshots: StoredScreenshot[] = [];
    private maxScreenshots: number = 20; // Store last 20 screenshots

    // Event capture tracking
    private pendingCaptures: Map<string, any> = new Map(); // Track pending captures with context
    private originalTerminalWriteln: Function | null = null;

    // Event tracking for bot status correlation
    private lastTriggeringEvent: string = "Initial connection";
    private eventHistory: Array<{ event: string, timestamp: number }> = [];

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
        // const initMsg = { init: "pygame" };
        const initMsg = { init: "mcp" };
        await this.send(initMsg);
        console.log("✅ Registered as pygame client");

        // Send gamepad connect command
        await this.sendCommand({ type: "gamepadConnect" });
        
        // Set up terminal interception for event-driven screenshot capture
        this.setupTerminalInterception();
        
        // Test screenshot request after connection
        setTimeout(() => {
            console.log("🧪 Testing screenshot request...");
            this.requestScreenshot();
        }, 2000);

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
            const data: WebSocketMessage = JSON.parse(event.data);
            console.log("📥 Received:", data);
            
            // Handle specific message types
            if (data.type === "botStatus") {
                this.handleBotStatusMessage(data as BotStatusMessage);
            } else if (data.type === "screenshot") {
                console.log("🔥 SCREENSHOT MESSAGE DETECTED!");
                this.handleScreenshotMessage(data);
            } else {
                console.log("📨 Other message type:", data.type);
            }

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
        // Note: Command tracking could be added here for bot status correlation

        // Handle joystick movement tracking
        if (command.type === "gamepadJoystickMove") {
            this.trackJoystickMovement(command.stickIndex, command.x, command.y);
        }
        
        // Only log important commands to reduce lag
        if (command.type === "getBotStatus" || command.type === "getScreenshot") {
            console.log(`📤 ${command.type}`);
        }
        
        await this.send(command);
    }

    private trackJoystickMovement(stickIndex: number, x: number, y: number): void {
        const now = Date.now();
        
        if (!this.movementSessions.has(stickIndex)) {
            // Start new session
            this.movementSessions.set(stickIndex, {
                stickIndex,
                startTime: now,
                lastUpdateTime: now,
                totalX: x,
                totalY: y,
                movementCount: 1
            });
            
            // Start reporting timer if not already running
            if (!this.reportTimer) {
                this.startReportTimer();
            }
        } else {
            // Update existing session - just sum the x and y values
            const session = this.movementSessions.get(stickIndex)!;
            session.totalX += x;
            session.totalY += y;
            session.movementCount++;
            session.lastUpdateTime = now;
        }
        
        // Check if joystick returned to center (end session)
        if (Math.abs(x) < 0.01 && Math.abs(y) < 0.01) {
            this.endJoystickSession(stickIndex);
        }
    }

    private endJoystickSession(stickIndex: number): void {
        const session = this.movementSessions.get(stickIndex);
        if (!session) return;
        
        // Generate and log report
        const report = this.generateMovementReport(session);
        this.logMovementReport(report);
        
        // Remove session
        this.movementSessions.delete(stickIndex);
        
        // Stop timer if no active sessions
        if (this.movementSessions.size === 0 && this.reportTimer) {
            clearInterval(this.reportTimer);
            this.reportTimer = null;
        }
    }

    private startReportTimer(): void {
        this.reportTimer = window.setInterval(() => {
            // Generate periodic reports for active sessions
            this.movementSessions.forEach(session => {
                const timeSinceLastUpdate = Date.now() - session.lastUpdateTime;
                // Only report if session has been inactive for a while
                if (timeSinceLastUpdate > 1000) {
                    this.endJoystickSession(session.stickIndex);
                }
            });
        }, this.reportInterval);
    }

    private generateMovementReport(session: JoystickSession): MovementReport {
        const sessionDuration = session.lastUpdateTime - session.startTime;
        
        return {
            stickIndex: session.stickIndex,
            sessionDuration,
            totalX: session.totalX,
            totalY: session.totalY,
            movementCount: session.movementCount
        };
    }

    private logMovementReport(report: MovementReport): void {
        const stickName = report.stickIndex === 0 ? "Left" : "Right";
        const duration = (report.sessionDuration / 1000).toFixed(1);
        
        // Track this as a triggering event for bot status correlation
        this.lastTriggeringEvent = `${stickName} Stick Movement Report`;

        const reportText = [
            `🎮 ${stickName} Stick Movement Report:`,
            `   Duration: ${duration}s`,
            `   Movements: ${report.movementCount}`,
            `   Total X: ${report.totalX.toFixed(3)}`,
            `   Total Y: ${report.totalY.toFixed(3)}`,
            `${'═'.repeat(50)}`
        ].join('\n');
        
        // Log to terminal (this will automatically trigger screenshot+status capture via interception)
        const terminal = (window as any).gamepadTerminal;
        if (terminal) {
            const timestamp = new Date().toLocaleTimeString();
            terminal.writeln(`[${timestamp}] ${reportText}`);
        }

        // Directly trigger capture for movement reports since they're significant
        this.triggerEventCapture(`${stickName} Stick Movement (${duration}s, ${report.movementCount} moves)`, report);
    }

    private prettyPrintBotStatus(status: any): string {
        const lines: string[] = [];
        const pos = status.position;
        const rot = status.rotation;
        lines.push(`Position: (${pos.x}, ${pos.y}, ${pos.z}) facing ${rot.cardinalDirection} (${rot.yaw}°, ${rot.pitch}°)`);
        lines.push(`Biome: ${status.biome.displayName}`);
        const time = status.time;
        const minutes = time.timeUntilNext.minutes.toFixed(2);
        lines.push(`Day ${time.day}, ${minutes} minutes until ${time.timeUntilNext.event}`);
        lines.push(`Selected slot: ${status.inventory.currentSlot}`);
        const hotbarItems = status.inventory.hotbarItems;
        if (Object.keys(hotbarItems).length > 0) {
            const itemStrings = Object.entries(hotbarItems).map(([slot, item]: [string, any]) => `[${slot}: ${item.displayName} x${item.count}]`);
            lines.push(`Hotbar: ${itemStrings.join(' ')}`);
        } else {
            lines.push('Hotbar: Empty');
        }
        const entityStates = Object.keys(status.entityState);
        if (entityStates.length > 0) {
            const stateNames = entityStates.map(state => state.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()));
            lines.push(`Status: ${stateNames.join(', ')}`);
        }
        if (status.targetBlock.message) {
            lines.push(`Looking at: ${status.targetBlock.message}`);
        } else {
            const block = status.targetBlock;
            const canDigText = block.canDig ? 'is close enough to dig' : 'cannot dig - too far away';
            lines.push(`Looking at: ${block.displayName} (${canDigText})`);
        }
        return lines.join('\n');
    }

    private logBotStatusToMainTerminal(botStatus: BotStatusMessage['data'], triggeringEvent?: string): void {
        const terminal = (window as any).gamepadTerminal;
        if (!terminal) return;

        try {
            // Use the pretty print function to format bot status
            const formattedStatus = this.prettyPrintBotStatus(botStatus);
            
            const statusText = [
                `🤖 Bot Status Update:`,
                ...formattedStatus.split('\n').map(line => `   ${line}`),
                `${'═'.repeat(50)}`
            ].join('\n');

            const timestamp = new Date().toLocaleTimeString();
            terminal.writeln(`[${timestamp}] ${statusText}`);
        } catch (error) {
            console.error("❌ Error logging bot status to main terminal:", error);
            console.log("📊 Bot status data:", botStatus);
        }
    }

    // ========================================
    // Bot Status and Screenshot Handlers
    // ========================================

    private handleBotStatusMessage(message: BotStatusMessage): void {
        console.log("🤖 Bot Status received:", message.data);

        // Store the bot status
        this.lastBotStatus = message.data;

        // Find the associated triggering event
        const triggerEvent = this.lastTriggeringEvent;

        // Update Terminal 1 with formatted bot status including triggering event
        this.updateBotStatusTerminal(message.data, message.timestamp, triggerEvent);

        // Process any pending captures waiting for bot status
        this.processPendingCaptures("botStatus", message);
    }

    private handleScreenshotMessage(message: any): void {
        console.log("📸 Screenshot received:", {
            size: message.data ? message.data.length : 0,
            timestamp: Date.now()
        });

        // Find the associated triggering event
        const triggerEvent = this.lastTriggeringEvent;

        // Create stored screenshot with current bot status and triggering event
        const storedScreenshot: StoredScreenshot = {
            image: message.data, // base64 string
            timestamp: Date.now(),
            width: 1920,  // Default dimensions
            height: 1080,
            botStatus: this.lastBotStatus || undefined
        };

        // Add metadata about the triggering event to the screenshot
        (storedScreenshot as any).triggeringEvent = triggerEvent;

        // Add to screenshots array
        this.screenshots.unshift(storedScreenshot);

        // Keep only the last maxScreenshots
        if (this.screenshots.length > this.maxScreenshots) {
            this.screenshots = this.screenshots.slice(0, this.maxScreenshots);
        }

        console.log(`📸 Screenshot stored for event: "${triggerEvent}". Total: ${this.screenshots.length}/${this.maxScreenshots}`);

        // Update the React screenshot gallery with new data
        if ((window as any).updateScreenshotGallery) {
            console.log("📸 Updating gallery with new screenshot");
            (window as any).updateScreenshotGallery(this.screenshots);
        }

        // Update Terminal 2 (Screenshot Gallery) with metadata
        this.updateScreenshotTerminal(message, triggerEvent);

        // Process any pending captures waiting for screenshot
        this.processPendingCaptures("screenshot", message);
    }

    private updateBotStatusTerminal(botStatus: BotStatusMessage['data'], timestamp: number, triggeringEvent?: string): void {
        try {
            const terminal = (window as any).gamepadTerminal;
            if (!terminal) {
                console.warn("⚠️ Terminal 1 not available for bot status update");
                return;
            }

            // Format timestamp
            const timeStr = new Date(timestamp).toLocaleTimeString();

            // Format triggering event
            const eventStr = triggeringEvent ? JSON.stringify(triggeringEvent) : "Unknown trigger";

            // Build event-driven status header
            terminal.writeToTerminal1(`[${timeStr}] Status after: ${eventStr}`);
            terminal.writeToTerminal1('');

            // Use the pretty print function to format bot status
            const formattedStatus = this.prettyPrintBotStatus(botStatus);
            
            // Output each line of the formatted status
            formattedStatus.split('\n').forEach(line => {
                terminal.writeToTerminal1(line);
            });

            // Add separator for readability
            terminal.writeToTerminal1('');
            terminal.writeToTerminal1('═'.repeat(50));
            terminal.writeToTerminal1('');

        } catch (error) {
            console.error("❌ Error updating bot status terminal:", error);
            console.log("📊 Bot status data:", botStatus);
        }
    }

    private getCompassDirection(yawDegrees: number): string {
        // Normalize yaw to 0-360 range
        let normalizedYaw = ((yawDegrees % 360) + 360) % 360;

        if (normalizedYaw >= 337.5 || normalizedYaw < 22.5) return "South";
        if (normalizedYaw >= 22.5 && normalizedYaw < 67.5) return "Southwest";
        if (normalizedYaw >= 67.5 && normalizedYaw < 112.5) return "West";
        if (normalizedYaw >= 112.5 && normalizedYaw < 157.5) return "Northwest";
        if (normalizedYaw >= 157.5 && normalizedYaw < 202.5) return "North";
        if (normalizedYaw >= 202.5 && normalizedYaw < 247.5) return "Northeast";
        if (normalizedYaw >= 247.5 && normalizedYaw < 292.5) return "East";
        if (normalizedYaw >= 292.5 && normalizedYaw < 337.5) return "Southeast";
        return "South"; // fallback
    }

    private formatGameTime(gameTime: number): string {
        // Minecraft game time: 1000 units per hour, 24000 units per day
        const day = Math.floor(gameTime / 24000);
        const timeOfDay = gameTime % 24000;

        // Calculate time until sunset (18000 game ticks = 6 PM)
        let timeUntilSunset = 18000 - timeOfDay;
        if (timeUntilSunset <= 0) {
            timeUntilSunset += 24000; // Next day
        }
        const minutesUntilSunset = (timeUntilSunset / 1000 * 60).toFixed(1);

        return `Day ${day}, ${minutesUntilSunset} minutes until sunset`;
    }

    private formatHotbarItems(inventory: any[]): string {
        const hotbarSlots = inventory.slice(0, 9); // First 9 slots are hotbar
        const items: string[] = [];

        hotbarSlots.forEach((item, index) => {
            if (item && item.name) {
                const count = item.count > 1 ? ` x${item.count}` : "";
                items.push(`[${index}: ${item.name}${count}]`);
            }
        });

        return items.slice(0, 3).join(' '); // Show only first 3 items for compactness
    }

    // ========================================
    // Event-Driven Screenshot Capture Methods
    // ========================================

    private setupTerminalInterception(): void {
        try {
            const gamepadTerminal = (window as any).gamepadTerminal;
            if (!gamepadTerminal || !gamepadTerminal.writeln) {
                console.warn("⚠️ Terminal not available for interception setup");
                return;
            }

            // Store original writeln function
            this.originalTerminalWriteln = gamepadTerminal.writeln;

            // Override writeln to trigger screenshot + bot status capture
            gamepadTerminal.writeln = (text: string) => {
                // Call original function first
                if (this.originalTerminalWriteln) {
                    this.originalTerminalWriteln.call(gamepadTerminal, text);
                }

                // Check if this is a significant event that should trigger capture
                if (this.isSignificantLogEvent(text)) {
                    this.triggerEventCapture(`Terminal Log: ${text.substring(0, 50)}...`, { logText: text });
                }
            };

            console.log("📡 Terminal interception set up for event-driven screenshot capture");
        } catch (error) {
            console.error("❌ Failed to set up terminal interception:", error);
        }
    }

    private isSignificantLogEvent(logText: string): boolean {
        // Define patterns that indicate significant events
        const significantPatterns = [
            '🎮 Left Stick Movement Report:',
            '🎮 Right Stick Movement Report:',
            '🎮 Button',
            'pressed for',
            '📤 Command:',
            'gamepadConnect',
            'gamepadDestroy',
            'Movement Report:',
            '═'.repeat(10) // Movement report separators
        ];

        return significantPatterns.some(pattern => logText.includes(pattern));
    }

    private triggerEventCapture(eventDescription: string, context?: any): void {
        const timestamp = Date.now();

        // Update the last triggering event
        this.lastTriggeringEvent = eventDescription;

        // Add to event history
        this.eventHistory.unshift({ event: eventDescription, timestamp });

        // Keep only last 10 events
        if (this.eventHistory.length > 10) {
            this.eventHistory = this.eventHistory.slice(0, 10);
        }

        console.log(`🔥 Event trigger: ${eventDescription}`);

        // Request both screenshot and bot status
        this.requestEventCapture(eventDescription, context);
    }

    private async requestEventCapture(eventDescription: string, context?: any): Promise<void> {
        try {
            const captureId = `capture_${Date.now()}`;

            // Store context for this capture
            this.pendingCaptures.set(captureId, {
                eventDescription,
                context,
                timestamp: Date.now(),
                botStatusReceived: false,
                screenshotReceived: false
            });

            // Request both bot status and screenshot
            await Promise.all([
                this.send({ type: "getBotStatus" }),
                this.send({ type: "getScreenshot" })
            ]);

            console.log(`📸🤖 Requested capture for: ${eventDescription}`);
        } catch (error) {
            console.error("❌ Failed to request event capture:", error);
        }
    }

    private processPendingCaptures(messageType: "botStatus" | "screenshot", message: any): void {
        // For now, just log that we received the response
        // In a more sophisticated implementation, we could correlate specific captures
        console.log(`✅ ${messageType} received for event: "${this.lastTriggeringEvent}"`, {
            messageTimestamp: message.timestamp || Date.now(),
            dataSize: JSON.stringify(message).length
        });
    }

    private updateScreenshotTerminal(message: any, triggeringEvent: string): void {
        try {
            const terminal = (window as any).gamepadTerminal;
            if (!terminal || !terminal.writeToTerminal2) {
                console.warn("⚠️ Terminal 2 not available for screenshot update");
                return;
            }

            const timeStr = new Date().toLocaleTimeString();
            const sizeKB = Math.round((message.data ? message.data.length : 0) * 0.75 / 1024); // Approximate base64 to KB

            const screenshotInfo = [
                `${'═'.repeat(50)}`,
                `📸 SCREENSHOT CAPTURED - ${timeStr}`,
                `${'═'.repeat(50)}`,
                `🔥 Triggered by: ${triggeringEvent}`,
                `📏 Dimensions: 1920x1080`,
                `💾 Size: ~${sizeKB}KB`,
                `⏰ Timestamp: ${Date.now()}`,
                `${'═'.repeat(50)}`,
                ''
            ].join('\n');

            terminal.writeToTerminal2(screenshotInfo);
        } catch (error) {
            console.error("❌ Error updating screenshot terminal:", error);
        }
    }

    private restoreTerminalInterception(): void {
        try {
            const gamepadTerminal = (window as any).gamepadTerminal;
            if (gamepadTerminal && this.originalTerminalWriteln) {
                gamepadTerminal.writeln = this.originalTerminalWriteln;
                this.originalTerminalWriteln = null;
                console.log("📡 Terminal interception restored");
            }
        } catch (error) {
            console.error("❌ Failed to restore terminal interception:", error);
        }
    }

    // ========================================
    // Public API Methods
    // ========================================

    public async requestBotStatus(): Promise<void> {
        console.log("🤖 Requesting bot status...");
        await this.sendCommand({ type: "getBotStatus" });
    }

    public async requestBotStatusWithEvent(eventDescription: string): Promise<void> {
        console.log(`🤖 Requesting bot status for event: ${eventDescription}`);
        this.lastTriggeringEvent = eventDescription;
        await this.sendCommand({ type: "getBotStatus" });
    }

    public async requestScreenshot(): Promise<void> {
        console.log("📸 Requesting screenshot...");
        await this.sendCommand({ type: "getScreenshot" });
    }

    public getLastBotStatus(): BotStatusMessage['data'] | null {
        return this.lastBotStatus;
    }

    public getScreenshots(): StoredScreenshot[] {
        return [...this.screenshots]; // Return a copy
    }

    public getLatestScreenshot(): StoredScreenshot | null {
        return this.screenshots.length > 0 ? this.screenshots[0] : null;
    }

    public clearScreenshots(): void {
        this.screenshots = [];
        console.log("📸 Screenshot history cleared");
    }

    public getScreenshotByIndex(index: number): StoredScreenshot | null {
        return index >= 0 && index < this.screenshots.length ? this.screenshots[index] : null;
    }

    public disconnect(): void {
        console.log("🔌 Disconnecting WebSocket...");
        
        // Clear movement tracking
        if (this.reportTimer) {
            clearInterval(this.reportTimer);
            this.reportTimer = null;
        }
        
        // Generate final reports for any active sessions
        this.movementSessions.forEach(session => {
            const report = this.generateMovementReport(session);
            this.logMovementReport(report);
        });
        this.movementSessions.clear();
        
        // Clear bot status and screenshots
        this.lastBotStatus = null;
        this.screenshots = [];

        // Clear event capture tracking
        this.pendingCaptures.clear();
        this.eventHistory = [];

        // Restore terminal interception
        this.restoreTerminalInterception();

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


    // Cleanup method
    public destroy(): void {
        this.disconnect();
        this.onStatusChange = undefined;
        this.onMessage = undefined;
        this.onError = undefined;
    }
}