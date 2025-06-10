/**
 * @file bot_status_utils.ts
 * Utilities for processing and interpreting `getBotStatus` responses from an MCP server.
 * This centralizes parsing logic.
 */

// Define a more specific type for the tools_mapping if its structure is known,
// especially for getBotStatus. For now, Record<string, any> is used.
type ToolsMapping = Record<string, (...args: any[]) => Promise<any>>;

/**
 * Represents the parsed status data from getBotStatus.
 */
export interface ParsedBotStatus {
    position_line: string;
    looking_at_line: string | null;
    raw_status_text: string;
    lines: string[];
}

/**
 * Represents enhanced status data, including context and success indicators.
 */
export interface EnhancedBotStatus extends ParsedBotStatus {
    context: string;
    success: boolean;
    error?: string;
    raw_result: any; // The raw result from getBotStatus tool call
}


/**
 * Centralized processor for getBotStatus responses.
 */
export class BotStatusProcessor {
    /**
     * Executes `getBotStatus` tool and processes its response.
     * @param tools_mapping - A mapping of tool names to their callable functions.
     *                        Expected to contain `getBotStatus`.
     * @returns A Promise resolving to parsed status data, or null if processing fails.
     */
    public static async get_and_process_status(tools_mapping: ToolsMapping): Promise<ParsedBotStatus | null> {
        try {
            if (!tools_mapping || typeof tools_mapping.getBotStatus !== 'function') {
                console.warn("⚠️ getBotStatus tool is not available in tools_mapping.");
                return null;
            }
            console.log("👁️ Getting updated bot status...");
            const status_result = await tools_mapping.getBotStatus();

            if (status_result && typeof status_result === 'object' && 'content' in status_result) {
                const status_content = status_result.content;
                if (Array.isArray(status_content) && status_content.length > 0 && status_content[0] && typeof status_content[0].text === 'string') {
                    const status_text = status_content[0].text;
                    if (status_text) {
                        const lines = status_text.split("\n");
                        const position_line = lines[0] || "";
                        const looking_at_line_arr = lines.filter(line => line.includes("Looking at:"));

                        return {
                            position_line,
                            looking_at_line: looking_at_line_arr.length > 0 ? looking_at_line_arr[0] : null,
                            raw_status_text: status_text,
                            lines,
                        };
                    }
                }
            }
            console.warn("⚠️ getBotStatus result format unexpected or content missing.");
        } catch (e: any) {
            console.error(`⚠️ Could not get or process bot status: ${e.message}`);
        }
        return null;
    }

    /**
     * Prints formatted status information from parsed data.
     * @param status_data - Parsed status data from `get_and_process_status`.
     */
    public static print_status(status_data: ParsedBotStatus | null): void {
        if (status_data) {
            console.log(`🎯 ${status_data.position_line}`);
            if (status_data.looking_at_line) {
                console.log(`🎯 ${status_data.looking_at_line}`);
            }
        } else {
            console.log("ℹ️ No status data to print.");
        }
    }

    /**
     * Convenience method to get and print bot status, typically after a look action.
     * @param tools_mapping - Tool mapping containing `getBotStatus`.
     */
    public static async get_status_after_look(tools_mapping: ToolsMapping): Promise<void> {
        if (!tools_mapping || typeof tools_mapping.getBotStatus !== 'function') {
            // Warning already logged by get_and_process_status
            return;
        }
        const status_data = await BotStatusProcessor.get_and_process_status(tools_mapping);
        BotStatusProcessor.print_status(status_data);
    }

    /**
     * Extracts position-related information from raw status text.
     * @param status_text - Raw status text from `getBotStatus`.
     * @returns An object containing extracted position data.
     */
    public static extract_position_info(status_text: string | null | undefined): Partial<ParsedBotStatus & { looking_at_count: number }> {
        if (!status_text) {
            return {};
        }
        const lines = status_text.split("\n");
        const position_line = lines[0] || "";
        const looking_at_lines = lines.filter(line => line.includes("Looking at:"));

        return {
            position_line,
            looking_at_line: looking_at_lines.length > 0 ? looking_at_lines[0] : null,
            lines, // all_lines in Python, renamed to lines for consistency with ParsedBotStatus
            looking_at_count: looking_at_lines.length,
        };
    }

    /**
     * Performs an enhanced status check with additional context and error handling.
     * @param tools_mapping - Tool mapping with `getBotStatus`.
     * @param context - A string describing the context of the status check (e.g., "after look command").
     * @returns A Promise resolving to an enhanced status data object, or null if `getBotStatus` is unavailable.
     */
    public static async enhanced_status_check(
        tools_mapping: ToolsMapping,
        context: string = "generic check"
    ): Promise<EnhancedBotStatus | null> {
        if (!tools_mapping || typeof tools_mapping.getBotStatus !== 'function') {
            console.warn(`⚠️ getBotStatus not available for context: ${context}`);
            return null;
        }

        try {
            console.log(`👁️ Getting updated view after ${context}...`);
            const status_result_raw = await tools_mapping.getBotStatus(); // Raw result

            if (status_result_raw && typeof status_result_raw === 'object' && 'content' in status_result_raw) {
                const status_content = status_result_raw.content;
                 if (Array.isArray(status_content) && status_content.length > 0 && status_content[0] && typeof status_content[0].text === 'string') {
                    const status_text = status_content[0].text;
                    if (status_text) {
                        const extracted_info = BotStatusProcessor.extract_position_info(status_text);
                        return {
                            ...(extracted_info as ParsedBotStatus), // Assume extract_position_info provides necessary fields
                            raw_status_text: status_text, // Ensure this is included
                            lines: extracted_info.lines || [], // Ensure lines is always an array
                            context,
                            success: true,
                            raw_result: status_result_raw,
                        };
                    }
                }
            }
            // If parsing failed or structure was unexpected
            return {
                position_line: "", // Provide default values for required fields
                looking_at_line: null,
                raw_status_text: JSON.stringify(status_result_raw),
                lines: [],
                context,
                success: false,
                error: "Could not parse status result or result format unexpected.",
                raw_result: status_result_raw,
            };

        } catch (e: any) {
            console.error(`⚠️ Could not get updated status after ${context}: ${e.message}`);
            return {
                position_line: "",
                looking_at_line: null,
                raw_status_text: "",
                lines: [],
                context,
                success: false,
                error: e.message,
                raw_result: null,
            };
        }
    }
}
