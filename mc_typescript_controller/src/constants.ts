// It's good practice to initialize Pygame or similar libraries if needed,
// but in TypeScript, this would typically be handled by the specific library's setup.
// For now, we'll comment out the Pygame initialization.
// import pygame from 'pygame'; // This would be the equivalent if 'pygame' had a TS module
// pygame.init(); // Call to initialize, if necessary

// Window constants
// Note: These are Pygame-specific and might be handled differently in a web or Node.js context.
export const WINDOW_WIDTH: number = 1600;
export const WINDOW_HEIGHT: number = 900;
export const FPS: number = 60;

// Custom event constants
// Note: Event handling mechanisms differ significantly from Pygame in typical TS environments.
// These are translated as simple numeric constants for now.
export const CUSTOM_MCP_TASK_EVENT: number = 1; // pygame.USEREVENT + 1
export const CUSTOM_MCP_RESULT_EVENT: number = 2; // pygame.USEREVENT + 2

// Colors
// In TypeScript, colors are often represented as strings (e.g., hex codes) or objects.
// For direct translation, we'll keep them as tuples of numbers (RGB).
export const BLACK: [number, number, number] = [0, 0, 0];
export const WHITE: [number, number, number] = [255, 255, 255];
export const GRAY: [number, number, number] = [128, 128, 128];
export const LIGHT_GRAY: [number, number, number] = [200, 200, 200];
export const DARK_GRAY: [number, number, number] = [64, 64, 64];
export const BLUE: [number, number, number] = [0, 100, 255];
export const GREEN: [number, number, number] = [0, 255, 0];
export const RED: [number, number, number] = [255, 0, 0];
export const YELLOW: [number, number, number] = [255, 255, 0];
export const ORANGE: [number, number, number] = [255, 165, 0];
export const PURPLE: [number, number, number] = [128, 0, 128];
export const CYAN: [number, number, number] = [0, 255, 255];
export const PINK: [number, number, number] = [255, 192, 203];
