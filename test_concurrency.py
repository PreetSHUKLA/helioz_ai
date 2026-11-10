import time
import requests
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://127.0.0.1:5000"

def send_slow_request(request_id):
    start = time.time()
    print(f"[{time.strftime('%X')}] --> Request {request_id} SENT (Waiting on simulated 3s API)...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/test-slow?id={request_id}", timeout=10)
        elapsed = time.time() - start
        
        if response.status_code == 404:
            print(f"[{time.strftime('%X')}] [!] Request {request_id} returned HTTP 404 NOT FOUND (Server needs to be restarted!)")
            return 0
        elif response.status_code == 200:
            print(f"[{time.strftime('%X')}] <-- Request {request_id} FINISHED in {elapsed:.2f}s! (Status: 200 OK)")
            return elapsed
        else:
            print(f"[{time.strftime('%X')}] <-- Request {request_id} returned HTTP {response.status_code} in {elapsed:.2f}s")
            return elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"[{time.strftime('%X')}] [!] Request {request_id} FAILED ({e}) in {elapsed:.2f}s")
        return 0

def main():
    print("=" * 60)
    print("TESTING 3 CONCURRENT REQUESTS (EACH WAITING 3 SECONDS)")
    print("=" * 60)
    
    start_total = time.time()
    
    # Send 3 requests simultaneously
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(send_slow_request, [1, 2, 3]))
        
    total_time = time.time() - start_total
    print("=" * 60)
    print(f"TOTAL TIME ELAPSED: {total_time:.2f} seconds")
    
    if any(r == 0 for r in results):
        print("[!] NOTICE: The server returned an error (likely 404).")
        print("[!] You must STOP the server with Ctrl+C and restart it with:")
        print("    python app.py")
        print("[!] so that it loads the new '/api/test-slow' endpoint!")
    elif total_time < 5.0:
        print("[SUCCESS] MULTITHREADING 100% CONFIRMED!")
        print("All 3 requests waited 3 seconds simultaneously across separate threads.")
        print(f"Processed 3 x 3s requests in {total_time:.2f}s total (instead of 9.0s sequential).")
    else:
        print("[FAIL] Requests were queued sequentially.")
    print("=" * 60)

if __name__ == '__main__':
    main()
