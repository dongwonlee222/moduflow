#!/usr/bin/env python3
import asyncio
import json
import os
import sys
import urllib.parse
import urllib.request

# Zero-dependency Telegram Bot Client
class TelegramBot:
    def __init__(self, token, allowed_chat_id):
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.allowed_chat_id = int(allowed_chat_id)
        self.offset = 0

    def _api_call(self, method, data=None):
        url = f"{self.base_url}/{method}"
        req_data = None
        if data:
            req_data = urllib.parse.urlencode(data).encode("utf-8")
        
        try:
            req = urllib.request.Request(url, data=req_data)
            with urllib.request.urlopen(req, timeout=35) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            print(f"Telegram API Error ({method}): {e}", file=sys.stderr)
            return None

    def send_message(self, chat_id, text, reply_markup=None):
        data = {"chat_id": chat_id, "text": text}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        return self._api_call("sendMessage", data)

    def get_updates(self):
        data = {"offset": self.offset, "timeout": 30}
        res = self._api_call("getUpdates", data)
        if res and res.get("ok"):
            return res.get("result", [])
        return []

async def handle_agent_chat(prompt):
    # Dynamically import google-antigravity SDK when needed
    try:
        from google.antigravity import Agent, LocalAgentConfig
    except ImportError:
        return "Error: google-antigravity SDK is not installed in the python environment. Please run: pip install google-antigravity"

    try:
        config = LocalAgentConfig()
        async with Agent(config) as agent:
            response = await agent.chat(prompt)
            return await response.text()
    except Exception as e:
        return f"Antigravity Agent Error: {e}"

async def main():
    # Load configuration from environment or prompt
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    allowed_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not allowed_chat_id:
        print("Error: Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.", file=sys.stderr)
        print("Example:", file=sys.stderr)
        print("  export TELEGRAM_BOT_TOKEN='your-bot-token'", file=sys.stderr)
        print("  export TELEGRAM_CHAT_ID='your-chat-id'", file=sys.stderr)
        sys.exit(1)

    bot = TelegramBot(token, allowed_chat_id)
    print(f"🤖 Antigravity Telegram Bridge started. Listening for updates (Allowed Chat ID: {allowed_chat_id})...")

    # Send startup notification
    bot.send_message(allowed_chat_id, "🟢 Antigravity 원격 브릿지가 연결되었습니다. 명령을 입력해 주세요.")

    while True:
        try:
            updates = bot.get_updates()
            for update in updates:
                # Update offset to confirm receipt
                bot.offset = update["update_id"] + 1

                message = update.get("message")
                if not message:
                    continue

                chat_id = message["chat"]["id"]
                user_id = message["from"]["id"]
                text = message.get("text")

                # Safety Check: only respond to the authorized user
                if chat_id != bot.allowed_chat_id:
                    print(f"Unauthorized chat attempt blocked from Chat ID: {chat_id}")
                    bot.send_message(chat_id, "⚠️ 권한이 없는 사용자입니다.")
                    continue

                if not text:
                    continue

                print(f"Received prompt: {text}")
                bot.send_message(chat_id, "⏳ 안티그라비티 에이전트가 실행 중입니다...")

                # Process the message through the Antigravity Agent
                response_text = await handle_agent_chat(text)
                
                # Send the response back to Telegram
                bot.send_message(chat_id, response_text)

        except KeyboardInterrupt:
            print("\nShutting down bridge...")
            break
        except Exception as e:
            print(f"Loop error: {e}", file=sys.stderr)
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
