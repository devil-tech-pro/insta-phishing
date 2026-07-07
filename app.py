import requests
from flask import Flask, render_template, request
import time
import hashlib

app = Flask(__name__)

def get_csrf_token():
    """Instagram se CSRF token aur cookies fetch karta hai."""
    session = requests.Session()
    try:
        # Pehla request se cookies aur CSRF token get karein
        response = session.get("https://www.instagram.com/")
        if response.status_code == 200:
            # CSRF token cookie se lena
            csrf_token = session.cookies.get('csrftoken')
            if not csrf_token:
                # Agar cookie nahi mila to try hidden input parsing
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                csrf_token = soup.find('meta', attrs={'name': 'csrfmiddlewaretoken'})['content']
            
            # Simple session return karein
            return session, csrf_token
    except Exception as e:
        print(f"Error fetching token: {e}")
    return None, None

def login_to_instagram(username, password):
    """Real Instagram API ko mock karke login check karta hai."""
    session, csrf_token = get_csrf_token()
    if not session:
        return False, "Server se connect nahi ho paaya."

    login_url = "https://www.instagram.com/accounts/login/ajax/"
    
    # Password hashing (Instagram jaisa format)
    timestamp = int(time.time())
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    enc_password = f"PWD{timestamp}#{hashed_password}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'X-CSRFToken': csrf_token,
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
    
    # FIX: Cookie ko Dictionary se String mein convert karna
    # Yeh error wala part fix karega
    cookies_dict = session.cookies.get_dict()
    cookie_header = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
    headers['Cookie'] = cookie_header

    data = {
        'username': username,
        'enc_password': enc_password,
        'queryParams': '{}',
        'optIntoOneTap': 'false',
        'stopDeletion': 'false',
        'trustedDevice': 'false'
    }

    try:
        # Login request bhejein
        response = session.post(login_url, headers=headers, data=data)
        
        # Debugging ke liye response text check karein
        print(f"Response Status: {response.status_code}")
        print(f"Response Text: {response.text[:500]}") # Pehla 500 characters print karein

        if response.status_code == 200:
            # Agar response mein 'authenticated' true hai ya 'ds_user_id' cookie set hai
            if 'ds_user_id' in session.cookies:
                return True, f"✅ SUCCESS: Password sahi hai! User ID: {session.cookies.get('ds_user_id')}"
            else:
                return False, "❌ FAILURE: Password galat hai."
        else:
            return False, f"❌ ERROR: Server Error (Status: {response.status_code})"
            
    except Exception as e:
        print(f"Exception: {e}")
        return False, f"❌ Exception: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username and password:
        print(f"Testing for: {username}")
        success, message = login_to_instagram(username, password)
        
        # Console mein result bhi print karega
        print(f"RESULT: {message}")
        
        return render_template('index.html', result=message, username=username)
    return render_template('index.html', result="⚠️ Please enter both username and password.")

if __name__ == '__main__':
    print("🚀 Server chal raha hai: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
