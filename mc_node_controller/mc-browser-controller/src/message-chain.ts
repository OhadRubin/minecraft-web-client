// src/message-chain.ts

import { Message } from "./types";
import { MinecraftControllerInterface } from "./interface";
import { resolveMultimodalArgs, resolveMultimodalOutput } from './chain-utils';

/**
 * Port of mc_pygame_controller/chain.py
 * An immutable-style message chaining class to manage conversation state
 * and orchestrate the agent's think-act loop.
 */

interface MCPMessageChainOptions {
    messages?: readonly Message[];
    systemPrompt?: string | null;
    toolsList?: any[];
    toolsMapping?: { [key: string]: Function };
    persistentInterface?: MinecraftControllerInterface;
    maxTokens?: number;
    verbose?: boolean;
    metricList?: any[];
    responseList?: any[];
}

export class MCPMessageChain {
    public readonly messages: readonly Message[];
    public readonly systemPrompt: string | null;
    public readonly toolsList: any[];
    public readonly toolsMapping: { [key: string]: Function };
    public readonly persistentInterface: MinecraftControllerInterface | null;
    public readonly maxTokens: number;
    public readonly verbose: boolean;
    public readonly metricList: any[];
    public readonly responseList: any[];

    constructor(options: MCPMessageChainOptions = {}) {
        this.messages = options.messages || [];
        this.systemPrompt = options.systemPrompt || null;
        this.toolsList = options.toolsList || [];
        this.toolsMapping = options.toolsMapping || {};
        this.persistentInterface = options.persistentInterface || null;
        this.maxTokens = options.maxTokens || 4096;
        this.verbose = options.verbose ?? false;
        this.metricList = options.metricList || [];
        this.responseList = options.responseList || [];
    }
    
    private clone(newOptions: Partial<MCPMessageChainOptions>): MCPMessageChain {
        return new MCPMessageChain({ ...this, ...newOptions });
    }

    public quiet() { return this.clone({ verbose: false }); }
    public verbose() { return this.clone({ verbose: true }); }
    
    public withTools(toolsList: any[], toolsMapping: { [key: string]: Function }): MCPMessageChain {
        return this.clone({ toolsList, toolsMapping });
    }
    
    public system(content: string): MCPMessageChain {
        return this.clone({ systemPrompt: content });
    }

    public addMessage(msg: Message): MCPMessageChain {
        return this.clone({ messages: [...this.messages, msg] });
    }

    public user(content: Message['content']): MCPMessageChain {
        return this.addMessage({ role: 'user', content });
    }

    public bot(content: Message['content'], tool_calls: any[] | null = null): MCPMessageChain {
        return this.addMessage({ role: 'assistant', content, tool_calls });
    }

    public tool(content: string, tool_call_id: string, name: string): MCPMessageChain {
        return this.addMessage({ role: 'tool', content, tool_call_id, name });
    }

    private serialize(): Message[] {
        const output: Message[] = [];
        if (this.systemPrompt) {
            output.push({ role: 'system', content: this.systemPrompt });
        }
        output.push(...this.messages);
        return output;
    }

    private parseMetrics(resp: any): any {
        return {
            input_tokens: resp.usage?.prompt_tokens ?? 0,
            output_tokens: resp.usage?.completion_tokens ?? 0,
            total_tokens: resp.usage?.total_tokens ?? 0,
        };
    }

    public async generate(): Promise<MCPMessageChain> {
        let currentChain: MCPMessageChain = this;
        
        while (true) {
            const msgs = currentChain.serialize();
            if (!currentChain.persistentInterface) {
                throw new Error("persistentInterface is not set");
            }

            const interface_ = currentChain.persistentInterface;
            interface_.convPanel.messages = msgs;
            
            // This is the key part: it gets a mock response from human actions
            const response = await interface_.convPanel.renderMessages({});
            
            const msg = response.choices[0].message;
            const respContent = msg.content;
            
            currentChain = currentChain.clone({
                metricList: [...currentChain.metricList, currentChain.parseMetrics(response)],
                responseList: [...currentChain.responseList, respContent],
            });

            if (msg.tool_calls && msg.tool_calls.length > 0) {
                currentChain = currentChain.bot(msg.content, msg.tool_calls);
                if (currentChain.verbose) console.log(`🤖 Bot (thinking): ${msg.content}`);
                
                for (const tool_call of msg.tool_calls) {
                    if (currentChain.verbose) console.log(`Tool call:`, tool_call);
                    const tool_name = tool_call.function.name;
                    let tool_args = JSON.parse(tool_call.function.arguments);
                    
                    tool_args = await resolveMultimodalArgs(tool_args);

                    if (currentChain.toolsMapping && tool_name in currentChain.toolsMapping) {
                        const tool_response = await currentChain.toolsMapping[tool_name](tool_args);
                        const resolved_response = await resolveMultimodalOutput(tool_response);
                        
                        let tool_response_str = "";
                        if (typeof resolved_response === 'string') {
                            tool_response_str = resolved_response;
                        } else if (resolved_response && resolved_response.multimodal_content) {
                             const text_parts = resolved_response.multimodal_content.filter((item: any) => item.type === 'text');
                             tool_response_str = text_parts.map((p: any) => p.text).join(' ') || `Tool ${tool_name} executed successfully.`;
                        } else {
                            tool_response_str = JSON.stringify(resolved_response);
                        }
                        
                        if (currentChain.verbose) console.log(`Tool response: ${tool_response_str}`);
                        currentChain = currentChain.tool(tool_response_str, tool_call.id, tool_name);
                    } else {
                        const errorMsg = `Tool '${tool_name}' not found in tools_mapping`;
                        currentChain = currentChain.tool(errorMsg, tool_call.id, tool_name);
                    }
                }
            } else {
                break; // No more tool calls, exit loop
            }
        }
        return currentChain;
    }
}

/**
 * Port of mc_pygame_controller/chain_utils.py
 * Utilities for handling multimodal content in the message chain.
 */

async function encodeBase64ContentFromUrl(contentUrl: string): Promise<string> {
    const response = await fetch(contentUrl);
    if (!response.ok) throw new Error(`Failed to fetch ${contentUrl}`);
    const blob = await response.blob();
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

export async function resolveMultimodalArgs(args: { [key: string]: any }): Promise<{ [key: string]: any }> {
    const resolved: { [key: string]: any } = {};
    for (const key in args) {
        const value = args[key];
        if (typeof value === 'string' && value.startsWith('http')) {
            resolved[key] = await encodeBase64ContentFromUrl(value);
        } else if (Array.isArray(value)) {
            resolved[key] = await Promise.all(
                value.map(v => (typeof v === 'string' && v.startsWith('http')) ? encodeBase64ContentFromUrl(v) : v)
            );
        } else {
            resolved[key] = value;
        }
    }
    return resolved;
}

export async function resolveMultimodalOutput(output: any): Promise<any> {
    if (output && Array.isArray(output.content)) {
        const result: any[] = [];
        for (const item of output.content) {
            if (item.type === 'text' && item.text) {
                result.push({ type: 'text', text: item.text });
            } else if (item.type === 'image' && item.data) {
                const mimeType = item.mimeType || 'image/png';
                const dataUri = `data:${mimeType};base64,${item.data}`;
                result.push({ type: 'image_url', image_url: { url: dataUri } });
            }
        }
        if (result.length === 1 && result[0].type === 'text') {
            return result[0].text;
        }
        return { multimodal_content: result };
    }
    return output;
}
