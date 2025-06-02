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
let siModule
try {
    siModule = require('systeminformation')
} catch (err) {}

// Create our app
const app = express()

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

// Setup WebSocket command server on separate port
const wss = new WebSocket.Server({ server: wsServer })

console.log(`[WebSocket] WebSocket server initialized`)

wss.on('connection', ws => {
    console.log(`[WebSocket] New connection established. Total connections: ${wss.clients.size}`)
    console.log(`[WebSocket] Current bot clients: ${botClients.size}`)
    
    ws.on('message', data => {
        try {
            const dataStr = data.toString()
            console.log(`[WebSocket] Received raw message: ${dataStr}`)
            
            const msg = JSON.parse(dataStr)
            console.log(`[WebSocket] Parsed message:`, msg)
            
            if (msg.init === 'bot') {
                botClients.add(ws)
                console.log(`[WebSocket] Bot client registered! Total bot clients: ${botClients.size}`)
                
                ws.on('close', () => {
                    botClients.delete(ws)
                    console.log(`[WebSocket] Bot client disconnected. Remaining bot clients: ${botClients.size}`)
                })
                return
            }
            
            console.log(`[WebSocket] Forwarding command to ${botClients.size} bot client(s)`)
            const str = JSON.stringify(msg)
            let forwardedCount = 0
            
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
            
        } catch (err) {
            console.error('[WebSocket] Error processing message:', err)
            console.error('[WebSocket] Raw data was:', data.toString())
        }
    })
    
    ws.on('close', () => {
        console.log(`[WebSocket] Connection closed. Remaining connections: ${wss.clients.size}`)
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