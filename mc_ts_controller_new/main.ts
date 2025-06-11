import { MinecraftController } from './minecraft_controller.js';

/**
 * Configuration options for MinecraftController initialization
 */
interface ControllerOptions {
    mode?: 'pygame' | 'mcp';
    enable_logging?: boolean;
    data_collection_enabled?: boolean;
    sensitivity?: number;
}

/**
 * Initialize the Minecraft Controller when the DOM is loaded
 */
window.addEventListener('DOMContentLoaded', (): void => {
    const controllerOptions: ControllerOptions = {
        mode: 'pygame',
        enable_logging: true,
        data_collection_enabled: true,
    };
    
    const controller = new MinecraftController(controllerOptions);
    controller.run();
});