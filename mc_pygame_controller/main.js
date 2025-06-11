import { MinecraftController } from './minecraft_controller.js';

window.addEventListener('DOMContentLoaded', () => {
    const controller = new MinecraftController({
        mode: 'pygame',
        enable_logging: true,
        data_collection_enabled: true,
    });
    controller.run();
});
