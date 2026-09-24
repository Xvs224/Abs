"""
中期检查全流程集成测试
覆盖：学生提交检查表 → 教师指导 → 学生提交PPT → 教师评审
"""
import requests
import json
import io

BASE = "http://localhost:8000/api"


def login(username):
    pwd = "student123" if username.startswith("student") else "teacher123"
    r = requests.post(f"{BASE}/auth/login", json={"username": username, "password": pwd})
    d = r.json()
    return d["data"]["access_token"]


def api_data(resp):
    """统一提取响应 data 字段"""
    body = resp.json()
    if resp.status_code >= 400:
        print(f"  [ERROR] {resp.status_code}: {body.get('message')}")
        return None
    return body.get("data")


student_token = login("student02")
teacher_token = login("teacher01")
s_h = {"Authorization": f"Bearer {student_token}"}
t_h = {"Authorization": f"Bearer {teacher_token}"}

print("=" * 60)
print("【阶段1】学生提交中期检查表")
print("=" * 60)

# 获取学生课题
r = requests.get(f"{BASE}/topics", headers=s_h, params={"page": 1, "page_size": 1})
topics_data = api_data(r)
topic_id = topics_data["items"][0]["id"]
print(f"课题ID: {topic_id}")

# 先上传检查表文件
fake_docx = io.BytesIO(b"PK fake docx content for midterm check")
r = requests.post(
    f"{BASE}/files/upload",
    headers=s_h,
    files={"file": ("中期检查表.docx", fake_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    data={"category": "midterm"}
)
file_data = api_data(r)
file_id = file_data["id"]
file_path = file_data.get("file_path", "")
file_name = file_data.get("file_name", "中期检查表.docx")
print(f"上传检查表: file_id={file_id}")

# 创建中期检查（关联文件）
r = requests.post(f"{BASE}/midterm", headers=s_h, json={
    "topic_id": topic_id,
    "file_id": file_id,
    "file_path": file_path,
    "file_name": file_name
})
my_midterm = api_data(r)
midterm_id = my_midterm["id"]
print(f"中期检查ID: {midterm_id}, 当前状态: {my_midterm.get('status')}")

# 提交中期检查表
r = requests.post(
    f"{BASE}/midterm/{midterm_id}/submit",
    headers=s_h,
    json={
        "completed_work": "已完成开题报告和文献综述，正在进行需求分析",
        "existing_problems": "技术选型还需要进一步确认",
        "next_plan": "完成系统设计和编码",
        "progress_percentage": 40,
        "file_id": file_id,
        "file_path": file_path,
        "file_name": file_name
    }
)
submitted = api_data(r)
print(f"提交后状态: {submitted.get('status')}, stage: {submitted.get('stage')}")

print()
print("=" * 60)
print("【阶段2】教师指导")
print("=" * 60)

r = requests.post(
    f"{BASE}/midterm/{midterm_id}/guidance",
    headers=t_h,
    json={"teacher_guidance": "建议尽快确定技术栈，注意时间节点，按计划推进。"}
)
guided = api_data(r)
print(f"指导后状态: {guided.get('status')}, stage: {guided.get('stage')}")
print(f"指导意见: {guided.get('teacher_guidance')}")

print()
print("=" * 60)
print("【阶段3】学生提交PPT")
print("=" * 60)

fake_ppt = io.BytesIO(b"PK fake pptx content")
r = requests.post(
    f"{BASE}/files/upload",
    headers=s_h,
    files={"file": ("中期答辩.pptx", fake_ppt, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
    data={"category": "midterm"}
)
ppt_data = api_data(r)
ppt_file_id = ppt_data["id"]

r = requests.post(
    f"{BASE}/midterm/{midterm_id}/submit-ppt",
    headers=s_h,
    json={
        "ppt_file_id": ppt_file_id,
        "ppt_file_path": ppt_data.get("file_path", ""),
        "ppt_file_name": ppt_data.get("file_name", "中期答辩.pptx")
    }
)
ppt_submitted = api_data(r)
print(f"提交PPT后状态: {ppt_submitted.get('status')}, stage: {ppt_submitted.get('stage')}")

print()
print("=" * 60)
print("【阶段4】教师评审")
print("=" * 60)

r = requests.post(
    f"{BASE}/midterm/{midterm_id}/review",
    headers=t_h,
    json={"status": "passed", "teacher_opinion": "中期进展良好，同意通过。", "teacher_score": 85}
)
reviewed = api_data(r)
print(f"评审后状态: {reviewed.get('status')}")

print()
print("=" * 60)
print("【完成】完整中期检查流程测试通过！")
print("=" * 60)
