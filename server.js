#!/usr/bin/env node

const express = require('express')
const netApi = require('net-browserify')
const compression = require('compression')
const path = require('path')
const cors = require('cors')
const https = require('https')
const fs = require('fs')
const WebSocket = require('ws')
const http = require('http')
// const { initWsLogger, shutdownWsLogger, logMessage } = require('./wsLogger')
let siModule
try {
    siModule = require('systeminformation')
} catch (err) {}

// Helper function to check if a message contains screenshot data
function isScreenshotMessage(message) {
    if (typeof message === 'object' && message !== null) {
        // Check for screenshot-related message types
        if (message.type === 'screenshot' || message.type === 'getScreenshot') {
            return true
        }
        // Check if message contains large screenshot data
        if (message.data && typeof message.data === 'string' && 
            (message.data.startsWith('data:image/') || message.data.length > 10000)) {
            return true
        }
    }
    return false
}

// Helper function to create a safe version of a message for console logging
function createSafeMessageForConsole(message) {
    if (isScreenshotMessage(message)) {
        const dataSize = message.data ? message.data.length : 0
        return {
            ...message,
            data: `[SCREENSHOT_DATA_FILTERED] - ${dataSize} bytes`
        }
    }
    return message
}

// =======================
// Movement Summary Feature
// =======================

// Configuration options
const movementConfig = {
    graceExpiryMs: 150,           // Grace period after movement stops
    maxSessionDurationMs: 30000,  // Auto-expire abandoned sessions  
    minMovementsForSummary: 2,    // Minimum movements to generate summary
    enableSummaries: true         // Global feature toggle
}

// Movement tracking state
const movementSessions = new Map() // key: stickIndex, value: MovementSession
const buttonSessions = new Map()   // key: buttonIndex, value: ButtonSession

// MovementSession class - tracks joystick movement sequences
class MovementSession {
    constructor(stickIndex) {
        this.stickIndex = stickIndex
        this.movements = []
        this.startTime = null
        this.endTime = null
        this.graceTimer = null
        this.active = false
        this.startBotPosition = null
        this.endBotPosition = null
    }
    
    addMovement(x, y, timestamp) {
        if (!this.startTime) this.startTime = timestamp
        this.movements.push({ x, y, timestamp })
        this.active = true
    }
    
    setStartBotPosition(position) {
        this.startBotPosition = { x: position.x, y: position.y, z: position.z }
    }
    
    setEndBotPosition(position) {
        this.endBotPosition = { x: position.x, y: position.y, z: position.z }
    }
    
    calculateWorldDistance() {
        if (!this.startBotPosition || !this.endBotPosition) return null
        
        const dx = this.endBotPosition.x - this.startBotPosition.x
        const dy = this.endBotPosition.y - this.startBotPosition.y
        const dz = this.endBotPosition.z - this.startBotPosition.z
        
        return Math.sqrt(dx * dx + dy * dy + dz * dz)
    }
    
    calculateStats() {
        if (this.movements.length === 0) return null
        
        let totalDistance = 0
        let peakVelocity = 0
        
        for (let i = 1; i < this.movements.length; i++) {
            const prev = this.movements[i - 1]
            const curr = this.movements[i]
            
            // Calculate distance between joystick points
            const dx = curr.x - prev.x
            const dy = curr.y - prev.y
            const distance = Math.sqrt(dx * dx + dy * dy)
            totalDistance += distance
            
            // Calculate velocity (distance per millisecond)
            const timeDiff = curr.timestamp - prev.timestamp
            if (timeDiff > 0) {
                const velocity = distance / timeDiff
                peakVelocity = Math.max(peakVelocity, velocity)
            }
        }
        
        const worldDistance = this.calculateWorldDistance()
        
        return {
            totalDistance: Math.round(totalDistance * 1000) / 1000, // joystick distance
            worldDistance: worldDistance ? Math.round(worldDistance * 100) / 100 : null, // world blocks
            duration: this.endTime - this.startTime,
            peakVelocity: Math.round(peakVelocity * 1000) / 1000,
            startTime: this.startTime,
            endTime: this.endTime,
            startPosition: this.startBotPosition,
            endPosition: this.endBotPosition
        }
    }
}

// ButtonSession class - tracks button press/release sequences
class ButtonSession {
    constructor(buttonIndex) {
        this.buttonIndex = buttonIndex
        this.pressStartTime = null
        this.releaseTime = null
        this.duration = null
        this.gameContext = null
    }
    
    startPress(timestamp, context) {
        this.pressStartTime = timestamp
        this.gameContext = context
    }
    
    endPress(timestamp) {
        this.releaseTime = timestamp
        this.duration = timestamp - this.pressStartTime
    }
    
    calculateStats() {
        return {
            buttonIndex: this.buttonIndex,
            duration: this.duration,
            gameContext: this.gameContext,
            pressStartTime: this.pressStartTime,
            releaseTime: this.releaseTime
        }
    }
}

// Movement summary functions
function handleJoystickMove(message, ws) {
    if (!movementConfig.enableSummaries) return false
    
    const { stickIndex, x, y } = message
    const timestamp = Date.now()
    
    // Get or create movement session for this stick
    let session = movementSessions.get(stickIndex)
    if (!session) {
        session = new MovementSession(stickIndex)
        movementSessions.set(stickIndex, session)
        console.log(`[Movement] Started new movement session for stick ${stickIndex}`)
    }
    
    if (x === 0 && y === 0) {
        // Potential sequence end - start grace period timer
        if (session.graceTimer) {
            clearTimeout(session.graceTimer)
        }
        
        console.log(`[Movement] Stick ${stickIndex} returned to center, starting grace period`)
        session.graceTimer = setTimeout(() => {
            completeMovementSequence(stickIndex)
        }, movementConfig.graceExpiryMs)
        
    } else {
        // Active movement - cancel any pending end timer
        if (session.graceTimer) {
            clearTimeout(session.graceTimer)
            session.graceTimer = null
        }
        
        // Record movement data
        session.addMovement(x, y, timestamp)
        console.log(`[Movement] Recorded movement for stick ${stickIndex}: (${x}, ${y})`)
    }
    
    return true // Indicate message was processed
}

function completeMovementSequence(stickIndex) {
    const session = movementSessions.get(stickIndex)
    if (!session || !session.active) return
    
    session.endTime = Date.now()
    const stats = session.calculateStats()
    
    if (stats && session.movements.length >= movementConfig.minMovementsForSummary) {
        console.log(`[Movement] Completing movement sequence for stick ${stickIndex}:`, stats)
        // Broadcast movement summary to all MCP clients
        broadcastMovementSummary(stickIndex, stats)
    } else {
        console.log(`[Movement] Skipping summary for stick ${stickIndex} - insufficient movements (${session.movements.length})`)
    }
    
    // Clean up completed session
    movementSessions.delete(stickIndex)
}

function broadcastMovementSummary(stickIndex, stats) {
    const summaryMessage = {
        type: "movementSummary",
        stickIndex: stickIndex,
        ...stats
    }
    
    const messageStr = JSON.stringify(summaryMessage)
    console.log(`[Movement] Broadcasting movement summary for stick ${stickIndex}`)
    
    // Send to all connected MCP clients
    for (const client of mcpClients) {
        if (client.readyState === WebSocket.OPEN) {
            client.send(messageStr)
            console.log(`[Movement] Summary sent to MCP client`)
        }
    }
    
    // Also send to pygame clients (since they can connect as either type)
    for (const client of pygameClients) {
        if (client.readyState === WebSocket.OPEN) {
            client.send(messageStr)
            console.log(`[Movement] Summary sent to pygame client`)
        }
    }
}

// Session cleanup - auto-expire abandoned sessions
function cleanupAbandonedSessions() {
    const now = Date.now()
    
    for (const [stickIndex, session] of movementSessions.entries()) {
        if (session.startTime && (now - session.startTime) > movementConfig.maxSessionDurationMs) {
            console.log(`[Movement] Auto-expiring abandoned session for stick ${stickIndex}`)
            if (session.graceTimer) clearTimeout(session.graceTimer)
            movementSessions.delete(stickIndex)
        }
    }
    
    for (const [buttonIndex, session] of buttonSessions.entries()) {
        if (session.pressStartTime && (now - session.pressStartTime) > movementConfig.maxSessionDurationMs) {
            console.log(`[Movement] Auto-expiring abandoned button session for button ${buttonIndex}`)
            buttonSessions.delete(buttonIndex)
        }
    }
}

// Cleanup interval - run every 30 seconds
setInterval(cleanupAbandonedSessions, 30000)

// =======================
// End Movement Summary Feature
// =======================

// Create our app
const app = express()
// console.log('initWsLogger')
// initWsLogger()
// process.on('exit', shutdownWsLogger)

const isProd = process.argv.includes('--prod') || process.env.NODE_ENV === 'production'
app.use(compression())
app.use(cors())
app.use(netApi({ allowOrigin: '*' }))
if (!isProd) {
    app.use('/sounds', express.static(path.join(__dirname, './generated/sounds/')))
}
// patch config
app.get('/config.json', (req, res, next) => {
    // read original file config
    let config = {}
    let publicConfig = {}
    try {
        config = require('./config.json')
    } catch {
        try {
            config = require('./dist/config.json')
        } catch {}
    }
    try {
        publicConfig = require('./public/config.json')
    } catch {}
    res.json({
        ...config,
        'defaultProxy': '', // use current url (this server)
        ...publicConfig,
    })
})
if (isProd) {
    // add headers to enable shared array buffer
    app.use((req, res, next) => {
        res.setHeader('Cross-Origin-Opener-Policy', 'same-origin')
        res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp')
        next()
    })

    // First serve from the override directory (volume mount)
    app.use(express.static(path.join(__dirname, './public')))

    // Then fallback to the original dist directory
    app.use(express.static(path.join(__dirname, './dist')))
}

const numArg = process.argv.find(x => x.match(/^\d+$/))
const httpPort = (require.main === module ? numArg : undefined) || 8080
const wsPort = httpPort + 1 // WebSocket server on the next port

// Start the HTTP server
const server = app.listen(httpPort, async function() {
    console.log('Proxy server listening on port ' + server.address().port)
    if (siModule && isProd) {
        const _interfaces = await siModule.networkInterfaces()
        const interfaces = Array.isArray(_interfaces) ? _interfaces : [_interfaces]
        let netInterface = interfaces.find(int => int.default)
        if (!netInterface) {
            netInterface = interfaces.find(int => !int.virtual) ?? interfaces[0]
            console.warn('Failed to get the default network interface, searching for fallback')
        }
        if (netInterface) {
            const address = netInterface.ip4
            console.log(`You can access the server on http://localhost:${httpPort} or http://${address}:${httpPort}`)
        }
    }
})

// Create separate HTTP server for WebSocket
const wsServer = http.createServer()
const botClients = new Set()
const mcpClients = new Set()
const pygameClients = new Set()

// Setup WebSocket command server on separate port
const wss = new WebSocket.Server({ server: wsServer })

console.log(`[WebSocket] WebSocket server initialized`)

wss.on('connection', (ws, req) => {
    console.log(`[WebSocket] New connection established. Total connections: ${wss.clients.size}`)
    console.log(`[WebSocket] Current bot clients: ${botClients.size}, MCP clients: ${mcpClients.size}, pygame clients: ${pygameClients.size}`)
    // logMessage('connect', req.socket.remoteAddress)
    ws.remoteAddress = req.socket.remoteAddress

    ws.on('message', data => {
        try {
            const dataStr = data.toString()
            // Filter raw message for console display
            const safeRawMessage = dataStr.includes('data:image/') || dataStr.length > 1000 ? 
                `[SCREENSHOT_DATA_FILTERED] - Raw message filtered (${dataStr.length} bytes)` : 
                dataStr
            console.log(`[WebSocket] Received raw message: ${safeRawMessage}`)
            // logMessage('incoming', dataStr)

            const msg = JSON.parse(dataStr)
            console.log(`[WebSocket] Parsed message:`, createSafeMessageForConsole(msg))

            // Handle client registration
            if (msg.init === 'bot') {
                botClients.add(ws)
                console.log(`[WebSocket] Bot client registered! Total bot clients: ${botClients.size}`)

                ws.on('close', () => {
                    botClients.delete(ws)
                    console.log(`[WebSocket] Bot client disconnected. Remaining bot clients: ${botClients.size}`)
                })
                return
            }

            if (msg.init === 'mcp') {
                mcpClients.add(ws)
                console.log(`[WebSocket] MCP client registered! Total MCP clients: ${mcpClients.size}`)

                ws.on('close', () => {
                    mcpClients.delete(ws)
                    console.log(`[WebSocket] MCP client disconnected. Remaining MCP clients: ${mcpClients.size}`)
                })
                return
            }

            if (msg.init === 'pygame') {
                pygameClients.add(ws)
                console.log(`[WebSocket] Pygame client registered! Total pygame clients: ${pygameClients.size}`)

                ws.on('close', () => {
                    pygameClients.delete(ws)
                    console.log(`[WebSocket] Pygame client disconnected. Remaining pygame clients: ${pygameClients.size}`)
                })
                return
            }

            // Route messages based on client type
            if (botClients.has(ws)) {
                // Message from bot client - forward to MCP clients
                console.log(`[WebSocket] Forwarding bot response to ${mcpClients.size} MCP client(s)`)
                const str = JSON.stringify(msg)
                let forwardedCount = 0

                // logMessage('outgoing', str)

                for (const client of mcpClients) {
                    if (client.readyState === WebSocket.OPEN) {
                        client.send(str)
                        forwardedCount++
                        console.log(`[WebSocket] Response forwarded to MCP client ${forwardedCount}`)
                    } else {
                        console.log(`[WebSocket] Skipping MCP client - connection not open (readyState: ${client.readyState})`)
                    }
                }

                console.log(`[WebSocket] Successfully forwarded response to ${forwardedCount}/${mcpClients.size} MCP clients`)

                if (forwardedCount === 0) {
                    console.warn(`[WebSocket] ⚠️  No MCP clients available to receive the response!`)
                }

            } else if (mcpClients.has(ws)) {
                // Check for movement summary messages first
                if (msg.type === 'gamepadJoystickMove') {
                    const processed = handleJoystickMove(msg, ws)
                    if (processed) {
                        console.log(`[WebSocket] Processed gamepadJoystickMove from MCP client for stick ${msg.stickIndex}`)
                    }
                    // Continue to forward to bot clients regardless
                }
                
                // Message from MCP client - forward to bot clients
                console.log(`[WebSocket] Forwarding MCP command to ${botClients.size} bot client(s)`)
                const str = JSON.stringify(msg)
                let forwardedCount = 0

                // logMessage('outgoing', str)

                for (const client of botClients) {
                    if (client.readyState === WebSocket.OPEN) {
                        client.send(str)
                        forwardedCount++
                        console.log(`[WebSocket] Command forwarded to bot client ${forwardedCount}`)
                    } else {
                        console.log(`[WebSocket] Skipping bot client - connection not open (readyState: ${client.readyState})`)
                    }
                }

                console.log(`[WebSocket] Successfully forwarded command to ${forwardedCount}/${botClients.size} bot clients`)

                if (forwardedCount === 0) {
                    console.warn(`[WebSocket] ⚠️  No bot clients available to receive the command!`)
                    console.warn(`[WebSocket] ⚠️  Make sure you have a mineflayer bot connected with {init: 'bot'}`)
                }

            } else if (pygameClients.has(ws)) {
                // Check for movement summary messages first
                if (msg.type === 'gamepadJoystickMove') {
                    const processed = handleJoystickMove(msg, ws)
                    if (processed) {
                        console.log(`[WebSocket] Processed gamepadJoystickMove from pygame client for stick ${msg.stickIndex}`)
                    }
                    // Continue to forward to bot clients regardless
                }
                
                // Message from pygame client - forward to bot clients (same as MCP clients)
                console.log(`[WebSocket] Forwarding pygame command to ${botClients.size} bot client(s)`)
                const str = JSON.stringify(msg)
                let forwardedCount = 0

                // logMessage('outgoing', str)

                for (const client of botClients) {
                    if (client.readyState === WebSocket.OPEN) {
                        client.send(str)
                        forwardedCount++
                        console.log(`[WebSocket] Pygame command forwarded to bot client ${forwardedCount}`)
                    } else {
                        console.log(`[WebSocket] Skipping bot client - connection not open (readyState: ${client.readyState})`)
                    }
                }

                console.log(`[WebSocket] Successfully forwarded pygame command to ${forwardedCount}/${botClients.size} bot clients`)

                if (forwardedCount === 0) {
                    console.warn(`[WebSocket] ⚠️  No bot clients available to receive the pygame command!`)
                    console.warn(`[WebSocket] ⚠️  Make sure you have a Minecraft web client connected`)
                }

            } else {
                console.warn(`[WebSocket] ⚠️  Unknown client type - message from unregistered client!`)
            }

        } catch (err) {
            console.error('[WebSocket] Error processing message:', err)
            const rawData = data.toString()
            const safeErrorData = rawData.includes('data:image/') || rawData.length > 1000 ? 
                `[SCREENSHOT_DATA_FILTERED] - Error data filtered (${rawData.length} bytes)` : 
                rawData
            console.error('[WebSocket] Raw data was:', safeErrorData)
        }
    })

    ws.on('close', () => {
        console.log(`[WebSocket] Connection closed. Remaining connections: ${wss.clients.size}`)
        // logMessage('disconnect', ws.remoteAddress)
    })

    ws.on('error', (err) => {
        console.error('[WebSocket] Connection error:', err)
    })
})

// Start the WebSocket server
wsServer.listen(wsPort, () => {
    console.log(`WebSocket server listening on port ${wsPort}`)
})

module.exports = { app }