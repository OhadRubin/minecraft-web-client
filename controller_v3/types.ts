// TypeScript types and interfaces for gamepad controller project

// ========================================
// WebSocket Command Types
// ========================================

export interface GamepadConnectCommand {
  type: "gamepadConnect";
}

export interface GamepadDestroyCommand {
  type: "gamepadDestroy";
}

export interface GamepadButtonPressDownCommand {
  type: "gamepadButtonPressDown";
  buttonIndex: number;
}

export interface GamepadButtonPressUpCommand {
  type: "gamepadButtonPressUp";
  buttonIndex: number;
}

export interface GamepadJoystickMoveCommand {
  type: "gamepadJoystickMove";
  stickIndex: number;
  x: number;
  y: number;
}

export interface GamepadJoystickCenterCommand {
  type: "gamepadJoystickCenter";
  stickIndex: number;
}

export interface GetBotStatusCommand {
  type: "getBotStatus";
}

export interface GetScreenshotCommand {
  type: "getScreenshot";
}

export interface WebSocketInitMessage {
  init: "pygame";
}

export type WebSocketCommand = 
  | GamepadConnectCommand
  | GamepadDestroyCommand
  | GamepadButtonPressDownCommand
  | GamepadButtonPressUpCommand
  | GamepadJoystickMoveCommand
  | GamepadJoystickCenterCommand
  | GetBotStatusCommand
  | GetScreenshotCommand;

// ========================================
// Position and Coordinate Types
// ========================================

export interface Position2D {
  x: number;
  y: number;
}

export interface MousePosition extends Position2D {
  // Inherits x, y from Position2D
}

export interface TouchPosition extends Position2D {
  // Inherits x, y from Position2D  
}

export interface JoystickPosition {
  x: number; // Normalized -1 to 1
  y: number; // Normalized -1 to 1
}

export interface VisualPosition extends Position2D {
  // Actual pixel coordinates for drawing
}

// ========================================
// Gamepad Button Mapping
// ========================================

export interface ButtonMapping {
  [physicalButtonIndex: number]: number; // Maps physical button to logical button
}

export const XBOX_BUTTON_MAPPING: ButtonMapping = {
  0: 0,   // A button
  1: 1,   // B button
  2: 2,   // X button
  3: 3,   // Y button
  4: 4,   // Left shoulder (L1)
  5: 5,   // Right shoulder (R1)
  6: 6,   // Left trigger (L2)
  7: 7,   // Right trigger (R2)
  8: 8,   // Back/Select
  9: 9,   // Start
  10: 10, // Left stick click
  11: 11, // Right stick click
  12: 15, // D-pad up
  13: 13, // D-pad down
  14: 14, // D-pad left
  15: 12  // D-pad right
};

// ========================================
// Button and Joystick Configuration
// ========================================

export interface GamepadButtonConfig {
  x: number;
  y: number;
  radius: number;
  buttonId: number;
  label: string;
  pressed: boolean;
  hover: boolean;
}

export interface GamepadJoystickConfig {
  centerX: number;
  centerY: number;
  radius: number;
  stickId: number;
  label: string;
  xPos: number; // Normalized position -1 to 1
  yPos: number; // Normalized position -1 to 1
  stickX: number; // Visual position
  stickY: number; // Visual position
  dragging: boolean;
  maxDistance: number;
}

// ========================================
// Button and Connection States
// ========================================

export enum ButtonState {
  IDLE = "idle",
  HOVER = "hover", 
  PRESSED = "pressed"
}

export enum ConnectionStatus {
  Connected = "connected",
  Disconnected = "disconnected",
  Connecting = "connecting",
  Error = "error"
}

export enum GamepadInputType {
  BUTTON_PRESS = "button_press",
  BUTTON_RELEASE = "button_release",
  JOYSTICK_MOVE = "joystick_move",
  JOYSTICK_CENTER = "joystick_center"
}

// ========================================
// Canvas and HTML Element Types
// ========================================

export type GamepadCanvasElement = HTMLCanvasElement;
export type GamepadCanvasContext = CanvasRenderingContext2D;

export interface CanvasContext extends CanvasRenderingContext2D {
  // Extends standard Canvas 2D context
}

export interface GamepadCanvas extends HTMLCanvasElement {
  // Extends standard HTMLCanvasElement
}

export interface GamepadControlElement extends HTMLElement {
  // For trigger control inputs and status displays
}


// ========================================
// Gamepad Settings and Configuration
// ========================================

export interface GamepadSettings {
  deadzone: number;
  triggerDuration: number;  // Duration in milliseconds
  triggerInterval: number;  // Interval in milliseconds (for continuous press)
}

export interface TriggerSettings {
  duration: number; // Default duration in ms
  interval: number; // Default interval in ms (60fps = 16ms)
  minDuration: number;
  maxDuration: number;
  minInterval: number;
  maxInterval: number;
}

// ========================================
// Physical Gamepad State
// ========================================

export interface PhysicalGamepadState {
  gamepad: Gamepad;
  previousButtonStates: boolean[];
  previousAxisValues: number[];
}

export interface GamepadInputState {
  physicalGamepads: Gamepad[];
  virtualButtons: GamepadButtonConfig[];
  virtualJoysticks: GamepadJoystickConfig[];
  draggingJoystick: GamepadJoystickConfig | null;
  buttonIntervals: Map<number, boolean>;
}


// ========================================
// Event Handler Types
// ========================================

export type MouseEventHandler = (event: MouseEvent) => Promise<void> | void;
export type TouchEventHandler = (event: TouchEvent) => Promise<void> | void;
export type GamepadEventHandler = (event: GamepadEvent) => void;

export interface GamepadEventHandlers {
  onMouseDown: MouseEventHandler;
  onMouseMove: MouseEventHandler;
  onMouseUp: MouseEventHandler;
  onGamepadConnected: GamepadEventHandler;
  onGamepadDisconnected: GamepadEventHandler;
}

// ========================================
// WebSocket Connection Types
// ========================================

export interface WebSocketConnection {
  websocket: WebSocket | null;
  connected: boolean;
  reconnectAttempts: number;
  maxReconnectAttempts: number;
}

export interface WebSocketStatus {
  connected: boolean;
  reconnectAttempts: number;
  readyState: number;
}

export interface WebSocketEventHandlers {
  onOpen: () => Promise<void>;
  onClose: () => void;
  onError: (error: Event) => void;
  onMessage: (event: MessageEvent) => void;
}

// ========================================
// Color and Drawing Types
// ========================================

export interface ColorScheme {
  idle: string;
  hover: string;
  pressed: string;
  background: string;
  border: string;
  text: string;
}

export const DEFAULT_COLOR_SCHEME: ColorScheme = {
  idle: '#808080',
  hover: '#c8c8c8',
  pressed: '#ff6464',
  background: '#ffffff',
  border: '#000',
  text: '#000'
};

// ========================================
// Layout and Positioning Types
// ========================================

export interface GamepadLayout {
  faceButtons: {
    centerX: number;
    centerY: number;
    spacing: number;
  };
  dpad: {
    centerX: number;
    centerY: number;
    spacing: number;
  };
  shoulderButtons: {
    leftTop: Position2D;
    leftTrigger: Position2D;
    rightTop: Position2D;
    rightTrigger: Position2D;
  };
  centerButtons: {
    select: Position2D; 
    start: Position2D;
    home: Position2D;
  };
  joysticks: {
    left: Position2D & { radius: number };
    right: Position2D & { radius: number };
  };
}

// ========================================
// Utility Types
// ========================================

export type ButtonId = number;
export type StickId = 0 | 1; // Left stick = 0, Right stick = 1
export type AxisValue = number; // -1 to 1 normalized
export type ButtonValue = boolean;

export interface Bounds {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

export interface Size {
  width: number;
  height: number;
}

// ========================================
// Animation and Timing Types
// ========================================

export interface AnimationState {
  lastFrameTime: number;
  deltaTime: number;
  frameCount: number;
}

export interface TimingConfig {
  pollInterval: number;
  animationFrameId: number | null;
  updateFrequency: number; // Hz
}

// ========================================
// Error and Status Types
// ========================================

export interface GamepadError {
  type: 'connection' | 'input' | 'websocket' | 'validation';
  message: string;
  timestamp: number;
  details?: any;
}

export interface StatusInfo {
  websocketStatus: ConnectionStatus;
  gamepadCount: number;
  activeButtons: number[];
  joystickValues: JoystickPosition[];
  lastUpdate: number;
}

// ========================================
// Validation Types
// ========================================

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export interface InputValidator {
  validateButtonId: (buttonId: number) => ValidationResult;
  validateStickId: (stickId: number) => ValidationResult;
  validateAxisValue: (value: number) => ValidationResult;
  validatePosition: (position: Position2D) => ValidationResult;
}

// ========================================
// Configuration Types
// ========================================

export interface GamepadControllerConfig {
  canvas: {
    width: number;
    height: number;
  };
  websocket: {
    url: string;
    reconnectInterval: number;
    maxReconnectAttempts: number;
  };
  gamepad: GamepadSettings;
  layout: GamepadLayout;
  colors: ColorScheme;
  timing: TimingConfig;
}

// ========================================
// Factory Types
// ========================================

export interface GamepadButtonFactory {
  createButton: (config: Partial<GamepadButtonConfig>) => GamepadButtonConfig;
  createJoystick: (config: Partial<GamepadJoystickConfig>) => GamepadJoystickConfig;
}

// ========================================
// Component State Types
// ========================================

export interface GamepadControllerState {
  websocket: WebSocket | null;
  connected: boolean;
  physicalGamepads: Gamepad[];
  buttons: IGamepadButton[];
  joysticks: IGamepadJoystick[];
  draggingJoystick: IGamepadJoystick | null;
  buttonIntervals: Map<number, boolean>;
  settings: GamepadSettings;
}

// ========================================
// HTML Element Types
// ========================================

export interface StatusElement extends HTMLElement {
  textContent: string | null;
  className: string;
}

export interface TriggerControlElement extends HTMLInputElement {
  value: string;
}

// ========================================
// WebSocket Status Type
// ========================================

export interface WebSocketStatus {
  connected: boolean;
  reconnectAttempts: number;
  readyState: number;
}

// ========================================
// Movement Tracking Types
// ========================================

export interface JoystickSession {
    stickIndex: number;
    startTime: number;
    lastUpdateTime: number;
    totalX: number;
    totalY: number;
    movementCount: number;
}

export interface MovementReport {
    stickIndex: number;
    sessionDuration: number;
    totalX: number;
    totalY: number;
    movementCount: number;
}

// ========================================
// Class Interface Types  
// ========================================

export interface IGamepadButton {
  x: number;
  y: number;
  radius: number;
  buttonId: number;
  label: string;
  pressed: boolean;
  hover: boolean;
  
  containsPoint(x: number, y: number): boolean;
  draw(ctx: CanvasRenderingContext2D): void;
}

export interface IGamepadJoystick {
  centerX: number;
  centerY: number;
  radius: number;
  stickId: number;
  label: string;
  xPos: number;
  yPos: number;
  stickX: number;
  stickY: number;
  dragging: boolean;
  maxDistance: number;
  
  containsPoint(x: number, y: number): boolean;
  updatePosition(mouseX: number, mouseY: number): void;
  resetPosition(): void;
  draw(ctx: CanvasRenderingContext2D): void;
}

// ========================================
// Bot Status and Screenshot Types
// ========================================

export interface BotStatusMessage {
  type: "botStatus";
  data: {
    position: [number, number, number]; // [x, y, z]
    yaw: number;
    pitch: number;
    health: number;
    food: number;
    selectedSlot: number;
    biome: string;
    dimension: string;
    gameTime: number;
    inventory: any[];
    lookingAt?: {
      name: string;
      position: [number, number, number];
      distance: number;
    };
    [key: string]: any; // Allow additional properties
  };
  timestamp: number;
}

export interface ScreenshotMessage {
  type: "screenshot";
  data: {
    image: string; // base64 encoded image
    timestamp: number;
    width: number;
    height: number;
  };
  timestamp: number;
  // Optional context and movement data for movement-triggered screenshots
  context?: string;
  movementData?: {
    stickIndex: number;
    totalDistance: number;
    worldDistance: number | null;
    duration: number;
    peakVelocity: number;
    startTime: number;
    endTime: number;
    startPosition: { x: number; y: number; z: number } | null;
    endPosition: { x: number; y: number; z: number } | null;
  };
}

export interface StoredScreenshot {
  image: string; // base64 encoded
  timestamp: number;
  width: number;
  height: number;
  botStatus?: BotStatusMessage['data']; // Associated bot status if available
}

export interface BotStatusData {
  position: [number, number, number];
  yaw: number;
  pitch: number;
  health: number;
  food: number;
  selectedSlot: number;
  biome: string;
  dimension: string;
  gameTime: number;
  inventory: any[];
  lookingAt?: {
    name: string;
    position: [number, number, number];
    distance: number;
  };
  [key: string]: any;
}

export interface BotStatusMessage {
  type: 'botStatus';
  data: BotStatusData;
  timestamp: number;
}

// ScreenshotMessage definition removed due to type conflicts

export type WebSocketMessage = 
  | BotStatusMessage
  | { type: string; [key: string]: any };

