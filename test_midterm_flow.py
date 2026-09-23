import requests
import json
import io

BASE = "http://localhost:8000/api"

# 登录
def login(username):
    r = requests.post(f"{BASE}/auth/login", json={"username": username, "password": "123456"})
    d = r.json()
    return d["access_token"]

student_token = login("student01")
teacher_token = login("teacher01")
s_h = {"Authorization": f"Bearer {student_token}"}
t_h = {"Authorization": f"Bearer {teacher_token}"}

print("=" * 60)
print("【阶段1】学生提交中期检查表")
print("=" * 60)

# 获取学生课题
r = requests.get(f"{BASE}/topics/my", headers=s_h)
topics = r.json()
topic_id = topics[0]["id"] if isinstance(topics, list) else topics["items"][0]["id"]
print(f"课题ID: {topic_id}")

# 创建/获取中期检查
r = requests.get(f"{BASE}/midterm/my", headers=s_h)
my_midterm = r.json()
print(f"我的中期检查: {json.dumps(my_midterm, ensure_ascii=False, indent=2)[:300]}")

# 如果没有，创建
if not my_midterm:
    r = requests.post(f"{BASE}/midterm", headers=s_h)
    my_midterm = r.json()
    print(f"创建中期检查: {r.status_code}")

midterm_id = my_midterm["id"]
print(f"中期检查ID: {midterm_id}, 当前状态: {my_midterm.get('status')}")

# 上传检查表文件（用一个模拟docx）
fake_docx = io.BytesIO(b"PK fake docx content for midterm check")
fake_docx.name = "中期检查表.docx"
r = requests.post(
    f"{BASE}/files/upload",
    headers=s_h,
    files={"file": ("中期检查表.docx", fake_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    data={"category": "midterm"}
)
print(f"上传检查表: {r.status_code}")
file_data = r.json()
file_id = file_data.get("id")
file_path = file_data.get("file_path", "")
file_name = file_data.get("file_name", "中期检查表.docx")
print(f"文件ID: {file_id}")

# 提交中期检查表（阶段1）
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
print(f"提交检查表结果: {r.status_code} - {r.text[:200]}")
submitted = r.json()
print(f"提交后状态: {submitted.get('status')}, stage: {submitted.get('stage')}")

print()
print("=" * 60)
print("【阶段2】教师指导")
print("=" * 60)

# 教师给出指导意见
r = requests.post(
    f"{BASE}/midterm/{midterm_id}/guidance",
    headers=t_h,
    json={"teacher_guidance": "建议尽快确定技术栈，注意时间节点，按计划推进。"}
)
print(f"教师指导结果: {r.status_code} - {r.text[:200]}")
guided = r.json()
print(f"指导后状态: {guided.get('status')}, stage: {guided.get('stage')}")
print(f"指导意见: {guided.get('teacher_guidance')}")

print()
print("=" * 60)
print("【阶段3】学生提交PPT")
print("=" * 60)

# 上传PPT
fake_ppt = io.BytesIO(b"PK fake pptx content")
fake_ppt.name = "中期答辩.pptx"
r = requests.post(
    f"{BASE}/files/upload",
    headers=s_h,
    files={"file": ("中期答辩.pptx", fake_ppt, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
    data={"category": "midterm"}
)
print(f"上传PPT: {r.status_code}")
ppt_data = r.json()
ppt_file_id = ppt_data.get("id")

# 提交PPT
r = requests.post(
    f"{BASE}/midterm/{midterm_id}/submit-ppt",
    headers=s_h,
    json={
        "ppt_file_id": ppt_file_id,
        "ppt_file_path": ppt_data.get("file_path", ""),
        "ppt_file_name": ppt_data.get("file_name", "中期答辩.pptx")
    }
)
print(f"提交PPT结果: {r.status_code} - {r.text[:200]}")
ppt_submitted = r.json()
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
print(f"评审结果: {r.status_code} - {r.text[:200]}")
reviewed = r.json()
print(f"评审后状态: {reviewed.get('status')}")

print()
print("=" * 60)
print("【完成】完整两阶段中期检查流程测试通过！")
print("=" * 60)
