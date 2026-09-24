"""认证与权限测试 - 全部 7 个用例"""
import requests
import json
import time

BASE = "http://localhost:8000/api"
results = []

def safe_request(method, url, **kwargs):
    """带重试的请求，应对连接重置和限流"""
    for attempt in range(4):
        try:
            time.sleep(0.8)
            r = requests.request(method, url, timeout=15, **kwargs)
            if r.status_code == 429:
                time.sleep(2)
                continue
            return r
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            time.sleep(2)
    return None

def safe_login(username, password):
    """登录，带重试应对限流"""
    r = safe_request("POST", f"{BASE}/auth/login", json={"username": username, "password": password})
    return r

def record(tc_id, tc_name, steps, expected, actual, passed, note=""):
    results.append({
        "id": tc_id, "name": tc_name, "steps": steps,
        "expected": expected, "actual": actual,
        "passed": passed, "note": note
    })
    print(f"[{tc_id}] {tc_name} -> {'PASS' if passed else 'FAIL'}")

# ========== TC-AUTH-01 正常登录 ==========
r = safe_login("admin", "admin123")
body = r.json()
has_token = "access_token" in (body.get("data") or {})
record("TC-AUTH-01", "登录-正常登录",
       f"POST /auth/login {{admin/admin123}}",
       "200, data含access_token和refresh_token",
       f"HTTP {r.status_code}, code={body.get('code')}, has_access_token={has_token}",
       r.status_code == 200 and has_token)

admin_token = body["data"]["access_token"] if has_token else None

# ========== TC-AUTH-02 错误密码 ==========
r = safe_login("admin", "wrongpwd")
body = r.json()
record("TC-AUTH-02", "登录-错误密码",
       f"POST /auth/login {{admin/wrongpwd}}",
       "401, '用户名或密码错误'",
       f"HTTP {r.status_code}, message={body.get('message')}",
       r.status_code == 401 and "用户名或密码错误" in str(body.get("message", "")))

# ========== TC-AUTH-03 不存在的用户 ==========
r = safe_login("nobody_xyz", "123456")
body = r.json()
record("TC-AUTH-03", "登录-不存在用户",
       f"POST /auth/login {{nobody_xyz/123456}}",
       "401",
       f"HTTP {r.status_code}, message={body.get('message')}",
       r.status_code == 401)

# ========== TC-AUTH-04 Token过期(使用无效token) ==========
fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjN9.invalid_signature"
r = safe_request("GET", f"{BASE}/auth/me", headers={"Authorization": f"Bearer {fake_token}"})
body = r.json()
record("TC-AUTH-04", "Token无效/过期",
       f"GET /auth/me with invalid token",
       "401, '未授权'",
       f"HTTP {r.status_code}, message={body.get('message')}",
       r.status_code == 401)

# ========== TC-AUTH-05 登出 ==========
# 先登录一个普通用户
r = safe_login("student02", "student123")
login_data = r.json()["data"]
stu_token = login_data["access_token"]
ref_token = login_data["refresh_token"]
r = safe_request("POST", f"{BASE}/auth/logout", json={"access_token": stu_token, "refresh_token": ref_token})
body = r.json()
logout_ok = r.status_code == 200
# 再次使用该token
r2 = safe_request("GET", f"{BASE}/auth/me", headers={"Authorization": f"Bearer {stu_token}"})
token_revoked = r2.status_code == 401
record("TC-AUTH-05", "登出",
       f"POST /auth/logout {{access_token, refresh_token}} then GET /auth/me with same token",
       "logout返回200; 同token再访问返回401",
       f"logout HTTP {r.status_code}; reuse HTTP {r2.status_code}",
       logout_ok and token_revoked,
       note=f"logout message={body.get('message')}; reuse message={r2.json().get('message')}")

# ========== TC-AUTH-06 学生访问管理员接口 ==========
r = safe_login("student02", "student123")
stu_token2 = r.json()["data"]["access_token"]
# POST /users (创建用户) 需要管理员权限
r = safe_request("POST", f"{BASE}/users", headers={"Authorization": f"Bearer {stu_token2}"},
                  json={"username": "hacker", "password": "123456", "real_name": "hack", "role": "admin"})
body = r.json()
record("TC-AUTH-06", "权限隔离-学生访问管理员接口",
       f"POST /users (创建用户) with student token",
       "403, 权限不足",
       f"HTTP {r.status_code}, message={body.get('message')}",
       r.status_code == 403)

# ========== TC-AUTH-07 教师访问管理员删除接口 ==========
r = safe_login("teacher01", "teacher123")
tch_token = r.json()["data"]["access_token"]
# 尝试删除一个不存在的用户id，主要验证权限拦截
r = safe_request("DELETE", f"{BASE}/users/99999", headers={"Authorization": f"Bearer {tch_token}"})
body = r.json()
record("TC-AUTH-07", "权限隔离-教师访问管理员删除接口",
       f"DELETE /users/99999 with teacher token",
       "403, '权限不足'",
       f"HTTP {r.status_code}, message={body.get('message')}",
       r.status_code == 403)

# ========== 汇总 ==========
print()
total = len(results)
passed = sum(1 for r in results if r["passed"])
print(f"总计: {total}, 通过: {passed}, 失败: {total - passed}")

# 输出JSON供后续生成md
with open("e:/Abs/docs/_auth_test_results.json", "w", encoding="utf-8") as f:
    json.dump({"total": total, "passed": passed, "results": results}, f, ensure_ascii=False, indent=2)
print("结果已保存到 docs/_auth_test_results.json")
