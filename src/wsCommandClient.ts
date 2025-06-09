// Legacy import for backwards compatibility
// The wsCommandClient has been refactored into separate modules for better maintainability
// All functionality is now available through the wsCommand module

export { setupWsCommandClient } from './wsCommand'
export type { MouseCommand } from './wsCommand/types'
