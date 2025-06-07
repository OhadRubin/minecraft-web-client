// src/interface.ts

import { ConversationPanel } from './conversation';
import { Message } from './types';

/**
 * Port of mc_pygame_controller/interface.py
 * Contains the interface that connects the UI to the demonstration capture logic.
 */

export class TrajectoryStorage {
    private currentSession: any | null = null;

    startSession(sessionName: string) {
        this.currentSession = {
            session_name: sessionName,
            timestamp: Date.now(),
            messages: [],
        };
        console.log(`🎬 Started trajectory recording: ${sessionName}`);
    }

    addStep(userContext: string, mockResponse: any) {
        if (!this.currentSession) return;

        const userMessage = {
            role: "user",
            content: userContext,
            timestamp: Date.now(),
        };
        const assistantMessage = {
            role: "assistant",
            content: mockResponse.content,
            tool_calls: mockResponse.tool_calls,
            timestamp: Date.now(),
        };
        this.currentSession.messages.push(userMessage, assistantMessage);

        if (mockResponse.tool_calls) {
            for (const toolCall of mockResponse.tool_calls) {
                const toolResult = {
                    role: "tool",
                    content: `Executed ${toolCall.function.name} successfully`,
                    tool_call_id: toolCall.id,
                    name: toolCall.function.name,
                    timestamp: Date.now(),
                };
                this.currentSession.messages.push(toolResult);
            }
        }
    }

    endSession(finalResponse?: any): any | null {
        if (!this.currentSession) return null;

        if (finalResponse && finalResponse.tool_calls) {
            this.addStep("final actions", finalResponse);
        }

        const filename = `trajectories/${this.currentSession.session_name}_${this.currentSession.timestamp}.json`;
        const trajectory = { ...this.currentSession };
        this.currentSession = null;

        // In the browser, we trigger a download instead of writing to a file.
        const blob = new Blob([JSON.stringify(trajectory, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log(`💾 Saved trajectory to ${filename} (download prompted)`);
        return trajectory;
    }
}

export class MinecraftControllerInterface {
    public convPanel: ConversationPanel;
    public toolsMapping: { [key: string]: Function } = {};
    private trajectoryStorage: TrajectoryStorage;
    public controller: any | null = null; // Should be MinecraftController, but causes circular dependency

    constructor(mode: "mcp" = "mcp") {
        this.convPanel = new ConversationPanel();
        this.trajectoryStorage = new TrajectoryStorage();

        if (mode === 'mcp') {
            this.convPanel.humanDemoMode = true;
            console.log(`🎮 MinecraftControllerInterface initialized in ${mode} mode`);
        }
    }

    setController(controller: any) {
        this.controller = controller;
        controller.setMcpExecutor(this);
        console.log("🔗 Controller connected to interface");
    }

    captureCommand(mcpCommand: { tool: string; parameters: any }) {
        this.convPanel.captureMcpAction(mcpCommand);
        // Don't wait for execution to keep UI responsive
        this.executeCommand(mcpCommand);
    }

    async executeCommand(action: { tool: string; parameters: any }): Promise<any> {
        const { tool: toolName, parameters: params } = action;
        console.log(`🎮 Executing: ${toolName}(${JSON.stringify(params)})`);
        
        if (toolName in this.toolsMapping) {
            try {
                const result = await this.toolsMapping[toolName](params);
                console.log(`✅ Executed ${toolName} successfully`);
                return result;
            } catch (e: any) {
                console.error(`❌ Error executing ${toolName}: ${e.message}`);
                return null;
            }
        } else {
            console.warn(`⚠️ Tool ${toolName} not found in tools_mapping. Available:`, Object.keys(this.toolsMapping));
            return null;
        }
    }
    
    startTrajectoryRecording(sessionName: string) {
        this.trajectoryStorage.startSession(sessionName);
    }
    
    stopTrajectoryRecording() {
        const mockResponse = this.convPanel.convertActionsToMockResponse();
        const trajectory = this.trajectoryStorage.endSession(mockResponse);
        console.log(`🎬 Stopped recording. Trajectory has ${trajectory?.messages.length || 0} messages.`);
        return trajectory;
    }
    
    saveDemonstrationStep(userContext: string): boolean {
        if (this.convPanel.capturedActions.length > 0) {
            const mockResponse = this.convPanel.convertActionsToMockResponse();
            this.trajectoryStorage.addStep(userContext, mockResponse);
            console.log(`💾 Saved demonstration step: ${userContext}`);
            return true;
        }
        return false;
    }
}
