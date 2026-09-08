from database import test_connection
ok, message = test_connection()
print("SUCCESS:" if ok else "FAILED:", message)