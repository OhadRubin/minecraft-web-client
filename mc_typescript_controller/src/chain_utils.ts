/**
 * @file chain_utils.ts
 * Utilities for handling multimodal content, data encoding, and potentially
 * for more complex chain operations in the future.
 */

import axios from 'axios';
import *_fs from 'fs'; // Renamed to avoid conflict with fs namespace if any
import _path from 'path'; // Renamed
import *mime from 'mime-types'; // For guessing MIME types

const fs = _fs.promises; // Use promises API for async file operations

/**
 * Asynchronously fetches content from a URL and encodes it in base64.
 * @param content_url - The URL to fetch content from.
 * @returns A Promise that resolves to the base64 encoded string.
 */
export async function encode_base64_content_from_url(content_url: string): Promise<string> {
    try {
        const response = await axios.get(content_url, { responseType: 'arraybuffer' });
        if (response.status !== 200) {
            throw new Error(`Failed to fetch URL: ${content_url}, status: ${response.status}`);
        }
        return Buffer.from(response.data).toString('base64');
    } catch (error: any) {
        console.error(`Error fetching or encoding URL ${content_url}: ${error.message}`);
        throw error;
    }
}

/**
 * Recursively processes arguments: if a string value starts with "http",
 * it's treated as a URL and its content is fetched and base64 encoded.
 * Lists of strings are also processed.
 * @param args - The arguments object to resolve.
 * @returns A Promise that resolves to the arguments object with URLs replaced by base64 content.
 */
export async function _resolve_multimodal_args(args: Record<string, any>): Promise<Record<string, any>> {
    const resolved: Record<string, any> = {};
    for (const key in args) {
        if (Object.prototype.hasOwnProperty.call(args, key)) {
            const value = args[key];
            if (Array.isArray(value)) {
                resolved[key] = await Promise.all(
                    value.map(async (v) => {
                        if (typeof v === 'string' && (v.startsWith("http://") || v.startsWith("https://"))) {
                            return encode_base64_content_from_url(v);
                        }
                        return v;
                    })
                );
            } else if (typeof value === 'string' && (value.startsWith("http://") || value.startsWith("https://"))) {
                resolved[key] = await encode_base64_content_from_url(value);
            } else {
                resolved[key] = value;
            }
        }
    }
    return resolved;
}

/**
 * Encodes a local file or remote URL to a base64 data URI.
 * @param source - The path to a local file or an HTTP(S) URL.
 * @param explicit_mime_type - Optional explicit MIME type to use. If not provided, it's guessed.
 * @returns A Promise that resolves to the base64 data URI.
 */
export async function _encode_to_data_uri(source: string, explicit_mime_type?: string): Promise<string> {
    let content: Buffer;
    let mime_type = explicit_mime_type;

    if (source.startsWith("http://") || source.startsWith("https://")) {
        try {
            const response = await axios.get(source, { responseType: 'arraybuffer' });
            if (response.status !== 200) {
                throw new Error(`Failed to fetch URL: ${source}, status: ${response.status}`);
            }
            content = Buffer.from(response.data);
            if (!mime_type) {
                mime_type = response.headers['content-type']?.split(';')[0]; // Get content type, remove parameters like charset
            }
        } catch (error: any) {
            console.error(`Error fetching URL ${source}: ${error.message}`);
            throw error;
        }
    } else {
        try {
            if (!_fs.existsSync(source)) { // Use synchronous existsSync for quick check before async read
                 throw new Error(`File not found: ${source}`);
            }
            content = await fs.readFile(source);
            if (!mime_type) {
                mime_type = _mime.lookup(source) || undefined;
            }
        } catch (error: any) {
            console.error(`Error reading file ${source}: ${error.message}`);
            throw error;
        }
    }

    mime_type = mime_type || "application/octet-stream"; // Default MIME type
    const encoded = content.toString('base64');
    return `data:${mime_type};base64,${encoded}`;
}


/**
 * Resolves multimodal output content. If the output is an MCP-style multimodal content
 * structure, it converts image data to data URIs for OpenAI compatibility.
 * If output is a string URL or local path, it's encoded to a data URI.
 * Handles nested structures (lists, dicts/objects).
 * @param output - The output data to resolve.
 * @returns A Promise that resolves to the processed output.
 */
export async function _resolve_multimodal_output(output: any): Promise<any> {
    if (typeof output === 'string') {
        if (output.startsWith("http://") || output.startsWith("https://") || _fs.existsSync(output)) {
             try {
                return await _encode_to_data_uri(output);
             } catch(e: any) {
                console.warn(`Could not encode string source "${output}" to data URI: ${e.message}. Returning as is.`);
                return output; // Return original string if encoding fails
             }
        }
        return output; // Return other strings as is
    } else if (Array.isArray(output)) {
        return Promise.all(output.map(item => _resolve_multimodal_output(item)));
    } else if (output && typeof output === 'object' && output !== null) {
        if (output.content && Array.isArray(output.content)) { // MCP multimodal structure
            const new_content_items: any[] = [];
            for (const item of output.content) {
                if (item && item.type === "text" && typeof item.text === 'string') {
                    new_content_items.push({ type: "text", text: item.text });
                } else if (item && item.type === "image" && typeof item.data === 'string') {
                    const mimeType = item.mimeType || "image/png"; // Default to PNG if not specified
                    const dataUri = `data:${mimeType};base64,${item.data}`;
                    new_content_items.push({ type: "image_url", image_url: { url: dataUri } });
                } else {
                    new_content_items.push(item); // Pass through unknown items
                }
            }
            // If only text, simplify to string, otherwise return OpenAI structure
            if (new_content_items.length === 1 && new_content_items[0].type === "text") {
                return new_content_items[0].text;
            }
            return { multimodal_content: new_content_items }; // Retain this structure for OpenAI tools
        } else { // Generic object, recurse
            const resolved_obj: Record<string, any> = {};
            for (const key in output) {
                if (Object.prototype.hasOwnProperty.call(output, key)) {
                    resolved_obj[key] = await _resolve_multimodal_output(output[key]);
                }
            }
            return resolved_obj;
        }
    }
    return output; // Return primitives and null/undefined as is
}


/**
 * Higher-order function to wrap a method, ensuring it can be used in a fluent chaining style.
 * This is a simplified interpretation of the Python `chain_method` decorator.
 * It doesn't fully replicate Python decorator behavior but provides basic async/sync wrapping.
 *
 * @param func - The function to wrap.
 * @returns The wrapped function.
 */
export function chainMethod<T extends (...args: any[]) => any>(func: T): T {
    // This HOF doesn't modify 'this' or automatically return 'this'.
    // The original Python decorator's implicit 'return self' is not replicated here.
    // The calling code would need to ensure it returns 'this' if that's the desired chaining behavior.

    // Check if it's an async function
    const isAsync = func.constructor.name === "AsyncFunction";

    if (isAsync) {
        return (async function(this: any, ...args: Parameters<T>): Promise<ReturnType<T>> {
            // 'this' context is preserved by arrow function or by how it's called
            return await func.apply(this, args);
        } as T);
    } else {
        return (function(this: any, ...args: Parameters<T>): ReturnType<T> {
            return func.apply(this, args);
        } as T);
    }
}

// Example of how it might be used (conceptual):
// class MyChain {
//     @chainMethod // If using TS decorators and the decorator is defined for that
//     myMethod(value: string) {
//         console.log(value);
//         return this; // Explicitly return this for chaining
//     }
//
//     // Or without decorators:
//     myOtherMethod = chainMethod(function(this: MyChain, value: number) {
//         console.log(value);
//         return this;
//     });
// }
