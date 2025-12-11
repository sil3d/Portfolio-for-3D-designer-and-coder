import requests
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_unauthorized_upload():
    print("[*] Testing Unauthorized Upload to /upload...")
    url = f"{BASE_URL}/upload"
    # No cookies/session
    files = {'glb_file': ('test.glb', b'fake glb content')}
    data = {'model_name': 'HackerModel', 'year': '2024'}
    
    try:
        response = requests.post(url, files=files, data=data, timeout=5)
        # Expecting 401 or 302 (redirect to login)
        if response.status_code == 401:
            print("[+] SUCCESS: Upload blocked (401 Unauthorized)")
        elif response.status_code == 302 and '/login' in response.headers.get('Location', ''):
             print(f"[+] SUCCESS: Upload redirected to login (302 Found) -> {response.headers['Location']}")
        elif response.status_code == 400:
             print("[+] SUCCESS: Upload blocked by CSRF (400 Bad Request) - Even before Auth check!")
        else:
            print(f"[-] FAILURE: Unexpected response code {response.status_code}")
            # print(response.text[:200])
    except Exception as e:
        print(f"[-] ERROR: {e}")

def test_failed_login():
    print("\n[*] Testing Failed Login Alert on /admin/login...")
    url = f"{BASE_URL}/admin/login"
    # CSRF token needed for this to reach the password check? 
    # Actually, if I don't send CSRF, it will trigger CSRF alert (which is also good).
    # To test login failure specifically, I would need to parse CSRF first.
    # For now, let's just trigger a CSRF alert on login, or if I can, try to bypass.
    # Simulating a "brute force" usually misses CSRF, so a CSRF alert is expected.
    # But let's try to hit the password check if possible, or just accept that CSRF blocks it first.
    
    # If I just send POST without token -> CSRF Alert.
    # If I send GET, parse token, then POST wrong password -> Failed Login Alert.
    
    s = requests.Session()
    try:
        # 1. Get CSRF token
        r = s.get(url, timeout=5)
        # Simple extraction (regex or just assume it's in meta/input)
        if 'name="csrf_token"' in r.text:
            import re
            csrf_token = re.search(r'value="([^"]+)"', r.text).group(1)
            
            # 2. Send Wrong Password
            data = {'username': 'admin', 'password': 'wrongpassword', 'csrf_token': csrf_token}
            r_post = s.post(url, data=data, timeout=5)
            
            if r_post.status_code == 200 and "unauthorized" in r_post.url: # Redirect follows to unauthorized
                 print("[+] SUCCESS: Login failed and redirected. Check server logs for 'Security Alert (Failed Admin Login)'.")
            elif "unauthorized" in r_post.text:
                 print("[+] SUCCESS: Login failed (Unauthorized page). Check server logs for 'Security Alert'.")
            else:
                 print(f"[-] INFO: Status: {r_post.status_code}")
                 
        else:
            print("[-] WARNING: Could not extract CSRF token to test login failure logic.")

    except Exception as e:
        print(f"[-] ERROR: {e}")

def test_csrf_protection():
    print("\n[*] Testing CSRF Protection on /comment...")
    url = f"{BASE_URL}/comment"
    # Valid data but NO CSRF token
    data = {'email': 'hacker@test.com', 'file_id': '1', 'comment': 'XSS Attempt <script>alert(1)</script>'}
    
    try:
        response = requests.post(url, data=data, timeout=5)
        if response.status_code == 400:
            print("[+] SUCCESS: Comment blocked (400 Bad Request) - CSRF Token missing")
        elif response.status_code == 200:
            print("[-] FAILURE: Comment accepted without CSRF token!")
        else:
            print(f"[-] INFO: Response code {response.status_code}")
    except Exception as e:
        print(f"[-] ERROR: {e}")

def test_sqli_resilience():
    print("\n[*] Testing SQL Injection Resilience on /image/...")
    # Trying to inject into ID
    payload = "1 OR 1=1"
    url = f"{BASE_URL}/image/{payload}"
    
    try:
        response = requests.get(url, timeout=5)
        # Flask router usually returns 404 for int converter failure, or 500 if it passes to DB
        # If int converter catches it, it's safe.
        if response.status_code == 404:
             print("[+] SUCCESS: SQLi blocked by Type Converter (404 Not Found)")
        elif response.status_code == 500:
             print("[-] WARNING: 500 Error - Check server logs (Likely DB syntax error, but should be handled)")
        else:
             print(f"[-] INFO: Response code {response.status_code}")
    except Exception as e:
        print(f"[-] ERROR: {e}")

if __name__ == "__main__":
    print(f"Running Penetration Tests on {BASE_URL}")
    print("Ensure server is running: .\\run_server.bat")
    print("="*40)
    
    test_unauthorized_upload()
    test_failed_login()
    test_csrf_protection()
    test_sqli_resilience()
    
    print("="*40)
    print("Tests Complete.")
