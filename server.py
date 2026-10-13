import os
import asyncio
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, LikeEvent, ViewCountUpdateEvent

app = Flask(__name__)
CORS(app)  # Memungkinkan request dari browser dashboard

# Data state global
active_bot_client = None
bot_thread = None
is_running = False

def start_tiktok_client(target_username, proxy_list=None):
    global active_bot_client, is_running
    
    clean_username = target_username.replace('@', '').strip()
    print(f"\n[ENGINE] Connecting to TikTok Live: @{clean_username}...")
    
    # Initialize TikTokLive Client
    active_bot_client = TikTokLiveClient(unique_id=clean_username)

    @active_bot_client.on(ConnectEvent)
    async def on_connect(event: ConnectEvent):
        print(f"[SUCCESS] Connected to room ID: {event.room_id} (@{clean_username})")

    @active_bot_client.on(CommentEvent)
    async def on_comment(event: CommentEvent):
        print(f"💬 [{event.user.nickname}]: {event.comment}")

    @active_bot_client.on(LikeEvent)
    async def on_like(event: LikeEvent):
        print(f"❤️ {event.user.nickname} sent {event.count} likes!")

    @active_bot_client.on(ViewCountUpdateEvent)
    async def on_view_count(event: ViewCountUpdateEvent):
        print(f"👁️ Live Viewers Update: {event.view_count}")

    try:
        is_running = True
        active_bot_client.run()
    except Exception as e:
        print(f"[ERROR] Engine stopped: {e}")
        is_running = False

@app.route('/api/dispatch-bot', methods=['POST'])
def dispatch_bot():
    global bot_thread, is_running
    
    data = request.json or {}
    target = data.get('target', '@g4l_tech_official')
    viewers = data.get('viewers', 5000)
    proxies = data.get('proxies', [])
    ai_comments = data.get('ai_comments', [])

    print(f"\n==========================================")
    print(f"🚀 [DISPATCH RECEIVED FROM DASHBOARD]")
    print(f"• Target Username: {target}")
    print(f"• Target Viewers : {viewers}")
    print(f"• Active Proxies : {len(proxies)} loaded")
    print(f"• AI Comments Queue: {len(ai_comments)} items")
    print(f"==========================================")

    # Jalankan client dalam background thread terpisah
    if not is_running:
        bot_thread = threading.Thread(target=start_tiktok_client, args=(target, proxies), daemon=True)
        bot_thread.start()
        status_msg = f"Engine launched for target {target}"
    else:
        status_msg = f"Engine updated payload for {target}"

    return jsonify({
        "status": "success",
        "message": status_msg,
        "payload_received": {
            "target": target,
            "target_viewers": viewers,
            "proxies_count": len(proxies),
            "comments_count": len(ai_comments)
        }
    }), 200

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "status": "online",
        "is_bot_running": is_running
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
