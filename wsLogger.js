const fs = require('fs')
const path = require('path')
const { EventEmitter } = require('events')

let sqlite3
let db
let enabled = false
let flushTimer = null
let fallbackStream = null
let consecutiveErrors = 0
const MAX_ERRORS_BEFORE_FALLBACK = 3
let shuttingDown = false

const defaultOptions = {
    batchSize: parseInt(process.env.WS_LOGGER_BATCH_SIZE, 10) || 50,
    flushIntervalMs: parseInt(process.env.WS_LOGGER_FLUSH_INTERVAL_MS, 10) || 1000,
    maxQueueSize: parseInt(process.env.WS_LOGGER_MAX_QUEUE_SIZE, 10) || 1000,
    dbPath: process.env.WS_LOGGER_DB_PATH || path.join(__dirname, 'ws_logs.db'),
    fallbackFile: process.env.WS_LOGGER_FALLBACK_FILE || path.join(__dirname, 'ws_logs.fallback.log'),
    enabled: process.env.WS_LOGGER_ENABLED !== 'false',
    useFileLogging: process.env.WS_LOGGER_USE_FILE_ONLY === 'true' || true, // Default to file logging for now
    filterScreenshots: process.env.WS_LOGGER_FILTER_SCREENSHOTS !== 'false', // Default to filtering screenshots
}

let options = {...defaultOptions }

const pendingLogs = []
const events = new EventEmitter()

function initWsLogger(userOptions = {}) {
    if (enabled) return true
    options = {...defaultOptions, ...userOptions }
    if (!options.enabled) {
        console.warn('[wsLogger] Logging disabled via configuration')
        return false
    }
    // basic validation
    for (const key of['batchSize', 'flushIntervalMs', 'maxQueueSize']) {
        if (typeof options[key] !== 'number' || Number.isNaN(options[key]) || options[key] <= 0) {
            console.warn(`[wsLogger] Invalid ${key}, using default`)
            options[key] = defaultOptions[key]
        }
    }

    // Ensure boolean options are properly set
    if (typeof options.filterScreenshots !== 'boolean') {
        options.filterScreenshots = defaultOptions.filterScreenshots
    }

    // If file logging is explicitly requested or SQLite fails, use file logging
    if (options.useFileLogging) {
        console.log('[wsLogger] Using file-based logging (SQLite disabled)')
        console.log(`[wsLogger] Screenshot filtering: ${options.filterScreenshots ? 'enabled' : 'disabled'}`)
        fallbackStream = fs.createWriteStream(options.fallbackFile, { flags: 'a' })
        enabled = true
        return true
    }

    try {
        sqlite3 = require('sqlite3').verbose()
    } catch (err) {
        console.warn('[wsLogger] SQLite3 module not available, switching to file logging')
        fallbackStream = fs.createWriteStream(options.fallbackFile, { flags: 'a' })
        enabled = true
        return true
    }
    try {
        db = new sqlite3.Database(options.dbPath)
        db.serialize(() => {
            db.run(`CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER,
        direction TEXT,
        message TEXT
      )`)
        })
        console.log('[wsLogger] SQLite database initialized successfully')
        console.log(`[wsLogger] Screenshot filtering: ${options.filterScreenshots ? 'enabled' : 'disabled'}`)
    } catch (err) {
        console.error('[wsLogger] Failed to initialize database:', err)
        events.emit('error', err)
        db = null
            // switch to file logging
        console.log('[wsLogger] Falling back to file logging')
        fallbackStream = fs.createWriteStream(options.fallbackFile, { flags: 'a' })
        enabled = true
        return true
    }
    process.on('SIGINT', gracefulShutdown)
    process.on('SIGTERM', gracefulShutdown)
    process.on('SIGQUIT', gracefulShutdown)
    process.on('beforeExit', gracefulShutdown)
    enabled = true
    return true
}

function gracefulShutdown() {
    if (shuttingDown) return
    shuttingDown = true
    process.off('SIGINT', gracefulShutdown)
    process.off('SIGTERM', gracefulShutdown)
    process.off('SIGQUIT', gracefulShutdown)
    process.off('beforeExit', gracefulShutdown)
    flushLogs(() => {
        if (db) db.close()
        if (fallbackStream) fallbackStream.end()
    })
}

function scheduleFlush() {
    if (!flushTimer) {
        flushTimer = setTimeout(() => flushLogs(), options.flushIntervalMs)
    }
}

function writeToFallback(logs, cb) {
    try {
        if (!fallbackStream) fallbackStream = fs.createWriteStream(options.fallbackFile, { flags: 'a' })
        for (const { timestamp, direction, message }
            of logs) {
            fallbackStream.write(`${timestamp} ${direction} ${message}\n`)
        }
        consecutiveErrors = 0
    } catch (err) {
        console.error('[wsLogger] Fallback logging failed:', err)
        events.emit('error', err)
    } finally {
        if (flushTimer) {
            clearTimeout(flushTimer)
            flushTimer = null
        }
        if (cb) cb()
    }
}

function handleFlushError(logs, err, cb) {
    console.error('[wsLogger] Failed to flush logs:', err)
    events.emit('error', err)
    consecutiveErrors++
    pendingLogs.unshift(...logs)
    if (consecutiveErrors >= MAX_ERRORS_BEFORE_FALLBACK) {
        writeToFallback(pendingLogs.splice(0, pendingLogs.length), cb)
    } else {
        if (flushTimer) {
            clearTimeout(flushTimer)
            flushTimer = null
        }
        if (cb) cb()
    }
}

function flushLogs(callback) {
    if (!enabled || pendingLogs.length === 0) {
        if (flushTimer) {
            clearTimeout(flushTimer)
            flushTimer = null
        }
        if (callback) callback()
        return
    }
    const logs = pendingLogs.splice(0, pendingLogs.length)
    if (!db) {
        writeToFallback(logs, callback)
        return
    }
    try {
        db.serialize(() => {
            const stmt = db.prepare('INSERT INTO logs (timestamp, direction, message) VALUES (?, ?, ?)')
            for (const { timestamp, direction, message }
                of logs) {
                stmt.run(timestamp, direction, message)
            }
            stmt.finalize(err => {
                if (err) return handleFlushError(logs, err, callback)
                consecutiveErrors = 0
                if (flushTimer) {
                    clearTimeout(flushTimer)
                    flushTimer = null
                }
                if (pendingLogs.length > 0) scheduleFlush()
                if (callback) callback()
            })
        })
    } catch (err) {
        handleFlushError(logs, err, callback)
    }
}

function isScreenshotMessage(message) {
    try {
        // Check if message is a string and try to parse it as JSON
        if (typeof message === 'string') {
            const parsed = JSON.parse(message)
                // Check for screenshot-related message types
            if (parsed.type === 'screenshot' || parsed.type === 'getScreenshot') {
                return true
            }
            // Check if message contains screenshot data (base64 image data)
            if (parsed.data && typeof parsed.data === 'string' &&
                (parsed.data.startsWith('data:image/') || parsed.data.length > 10000)) {
                return true
            }
        }
    } catch (err) {
        // If parsing fails, check if the raw message looks like base64 image data
        if (typeof message === 'string' &&
            (message.includes('data:image/') ||
                (message.length > 10000 && message.includes('screenshot')))) {
            return true
        }
    }
    return false
}

function logMessage(direction, message) {
    if (!enabled) return

    // Skip logging screenshot messages to prevent large binary data in logs (if filtering is enabled)
    if (options.filterScreenshots && isScreenshotMessage(message)) {
        // Log a placeholder instead of the full screenshot data
        const placeholder = `[SCREENSHOT_DATA_FILTERED] ${direction} - Screenshot message blocked from logging (${message.length} bytes)`
        pendingLogs.push({ timestamp: Date.now(), direction, message: placeholder })
    } else {
        pendingLogs.push({ timestamp: Date.now(), direction, message })
    }

    if (pendingLogs.length >= options.maxQueueSize) {
        console.warn('[wsLogger] Pending log queue maxed out, flushing...')
        flushLogs()
    } else if (pendingLogs.length >= options.batchSize) {
        flushLogs()
    } else {
        scheduleFlush()
    }
}

function updateOptions(newOptions = {}) {
    options = {...options, ...newOptions }
}

module.exports = {
    initWsLogger,
    shutdownWsLogger: gracefulShutdown,
    logMessage,
    flushLogs,
    updateOptions,
    events,
}