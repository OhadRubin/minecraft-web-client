#!/usr/bin/env node

import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import { WebSocketServer } from 'ws';
import { MinecraftControllerBase } from './controller_base';

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .option('mcp', {
      alias: 'm',
      type: 'string',
      description: 'Path to the MCP server JAR file',
      demandOption: true,
    })
    .option('sensitivity', {
      alias: 's',
      type: 'number',
      description: 'Mouse sensitivity',
      default: 1.0,
    })
    .option('data-collection', {
      alias: 'd',
      type: 'boolean',
      description: 'Enable data collection',
      default: false,
    })
    .help()
    .argv;

  const controller = new MinecraftControllerBase(argv.mcp, argv.sensitivity, argv.dataCollection);
  await controller.run();

  const wss = new WebSocketServer({ port: 3001 });
  console.log('🎮 WebSocket UI Bridge listening on port 3001');

  wss.on('connection', ws => {
    console.log('🔌 UI client connected');

    ws.on('message', messageData => {
      try {
        const messageString = messageData.toString();
        const parsedAction = JSON.parse(messageString);
        console.log(`🎨 Received action from UI: ${parsedAction.action} - Value: ${parsedAction.value}`);
        // Ensure the action format matches what process_actions expects: [actionName, actionValue]
        // If parsedAction is an object like { action: "name", value: "val" }
        // then it should be controller.action_handler.process_actions([[parsedAction.action, parsedAction.value]]);
        // If parsedAction is already ["name", "val"], then use controller.action_handler.process_actions([parsedAction]);
        controller.action_handler.process_actions([[parsedAction.action, parsedAction.value]]);
      } catch (error) {
        console.error('💣 Error parsing message from UI:', error);
      }
    });

    ws.on('close', () => {
      console.log('🔌 UI client disconnected');
    });

    ws.on('error', error => {
      console.error('💣 WebSocket error with UI client:', error);
    });
  });

}

main().catch(console.error);
