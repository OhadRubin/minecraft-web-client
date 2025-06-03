import asyncio
import json
import os
import base64
from io import BytesIO

import websockets
import openai
import re

try:
    from PIL import ImageGrab, Image
except Exception:
    ImageGrab = None
    Image = None


async def capture_screen_base64(scale: float) -> str:
    """Capture the screen and return base64 encoded PNG."""
    if ImageGrab:
        img = ImageGrab.grab()
        if scale != 1.0 and Image is not None:
            w, h = img.size
            img = img.resize((int(w * scale), int(h * scale)))
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return base64.b64encode(buf.getvalue()).decode("ascii")
    # Fallback to a static screenshot if ImageGrab is unavailable
    with open("screenshot.png", "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("ascii")


def parse_response(text: str):
    """Return (command_dict, explanation) from the model response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in response")
    command = json.loads(match.group(0))
    explanation = text[match.end() :].strip()
    return command, explanation


DEFAULT_SYSTEM_PROMPT = (
    "You control a Minecraft bot via JSON commands. "
    "Each message contains the latest screenshot encoded as a data URL. "
    "Reply with exactly one JSON object describing the next action, "
    "optionally followed by a short explanation after a blank line. "
    'Valid examples include {"type": "move", "x": 0, "z": 1} or {"type": "look", "movementX": 10, "movementY": 0}. '
    "Do not wrap the JSON in code fences."
)


def load_system_prompt() -> str:
    """Return the system prompt, optionally loaded from a file or env var."""
    prompt_file = os.environ.get("PROMPT_FILE")
    if prompt_file:
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as exc:
            print("Failed to read prompt file", exc)
    return os.environ.get("SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT)


async def main():
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    if not openai.api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    uri = os.environ.get("WEBSOCKET_URI", "ws://localhost:8081")
    step_interval = float(os.environ.get("STEP_INTERVAL", "0.5"))
    history_limit = int(os.environ.get("HISTORY_LIMIT", "6"))
    show_explanation = os.environ.get("SHOW_EXPLANATION", "1") != "0"
    screenshot_scale = float(os.environ.get("SCREENSHOT_SCALE", "0.5"))

    async with websockets.connect(uri) as ws:
        system_prompt = load_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]

        while True:
            screenshot_b64 = await capture_screen_base64(screenshot_scale)
            user_content = f"screenshot: data:image/png;base64,{screenshot_b64}"
            messages.append({"role": "user", "content": user_content})

            try:
                response = await openai.ChatCompletion.acreate(
                    model=model,
                    messages=messages,
                    temperature=0.2,
                )
            except Exception as exc:
                print("OpenAI API error", exc)
                await asyncio.sleep(step_interval)
                continue

            reply = response.choices[0].message["content"].strip()

            try:
                command, explanation = parse_response(reply)
            except Exception:
                print("Invalid response from model:", reply)
                messages.pop()  # remove last user message
                await asyncio.sleep(step_interval)
                continue

            await ws.send(json.dumps(command))
            messages.append({"role": "assistant", "content": reply})

            if show_explanation and explanation:
                print("Model explanation:", explanation)

            if len(messages) > 1 + history_limit * 2:
                messages = [messages[0]] + messages[-history_limit * 2 :]

            await asyncio.sleep(step_interval)


if __name__ == "__main__":
    asyncio.run(main())
