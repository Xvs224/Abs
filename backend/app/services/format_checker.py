"""
论文格式检测引擎 — 基于 python-docx 真实解析 Word 文档

检测维度参考国标 GB/T 7713.1-2006 学位论文编写规则，
涵盖标题格式、摘要、关键词、章节结构、参考文献、字体、页面布局等。
"""
import os
import re
from typing import Dict, Any, List

from app.core.exceptions import BusinessException


def _safe_extract_docx(file_path: str):
    """安全加载 docx，失败时返回 None"""
    try:
        from docx import Document
        return Document(file_path)
    except ImportError:
        raise BusinessException(500, "python-docx 未安装，无法执行格式检测")
    except Exception:
        return None


def _count_words(text: str) -> int:
    """统计中英文混合字数"""
    if not text:
        return 0
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    english = len(re.findall(r"[a-zA-Z]+", text))
    return chinese + english


def _extract_all_text(doc) -> str:
    """提取文档全部段落文本"""
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_pdf_text(file_path: str) -> str:
    """从 PDF 文件提取全部文本"""
    try:
        import pymupdf as fitz  # PyMuPDF
    except ImportError:
        try:
            import fitz  # 兼容旧版 PyMuPDF
        except ImportError:
            return ""
    try:
        text_parts = []
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text_parts.append(page.get_text())
        return "\n".join(text_parts)
    except Exception:
        return ""


def count_words_from_file(file_path: str) -> int:
    """
    统计文档字数（支持 .docx / .pdf）

    :param file_path: 文件物理路径
    :return: 字数（中文字符数 + 英文单词数），失败返回 0
    """
    if not file_path or not os.path.exists(file_path):
        return 0

    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".docx":
        doc = _safe_extract_docx(file_path)
        if doc is not None:
            text = _extract_all_text(doc)
    elif ext == ".pdf":
        text = _extract_pdf_text(file_path)
    # .doc 格式暂不支持，返回 0

    return _count_words(text)


def _check_title_format(doc) -> Dict[str, Any]:
    """检测标题格式"""
    passed = True
    message = "标题格式正确"
    score = 10

    if not doc.paragraphs:
        return {"passed": False, "message": "文档为空", "score": 0, "max_score": 10}

    first_heading = None
    for p in doc.paragraphs:
        if p.style and p.style.name and "Heading" in p.style.name:
            first_heading = p
            break

    if not first_heading:
        passed = False
        message = "未找到标题样式段落，建议使用标题样式排版"
        score = 5
    else:
        text = first_heading.text.strip()
        if len(text) < 5:
            passed = False
            message = "标题过短，建议不少于5个字"
            score = 6

    return {"passed": passed, "message": message, "score": score, "max_score": 10}


def _check_abstract_format(doc, all_text: str) -> Dict[str, Any]:
    """检测摘要格式"""
    passed = True
    message = "摘要格式规范"
    score = 10

    has_abstract = bool(re.search(r"摘\s*要", all_text[:3000]))
    if not has_abstract:
        passed = False
        message = "未检测到摘要部分"
        score = 0
    else:
        abstract_match = re.search(r"摘\s*要[：:.\s]*(.*?)(?:关键词|Key\s*words)", all_text[:5000], re.DOTALL)
        if abstract_match:
            abstract_text = abstract_match.group(1).strip()
            word_count = _count_words(abstract_text)
            if word_count < 200:
                passed = False
                message = f"摘要字数不足（约{word_count}字），建议不少于200字"
                score = 5
            elif word_count > 1000:
                passed = False
                message = f"摘要字数过多（约{word_count}字），建议不超过1000字"
                score = 7

    return {"passed": passed, "message": message, "score": score, "max_score": 10}


def _check_keywords_format(doc, all_text: str) -> Dict[str, Any]:
    """检测关键词格式"""
    passed = True
    message = "关键词格式正确"
    score = 5

    kw_match = re.search(r"关键词[：:.\s]*(.*?)(?:\n\n|\n[^\s]|Abstract|abstract|目\s*录)", all_text[:5000])
    if not kw_match:
        passed = False
        message = "未检测到关键词"
        score = 0
    else:
        keywords_text = kw_match.group(1).strip()
        keywords = re.split(r"[；;,，]", keywords_text)
        keywords = [k.strip() for k in keywords if k.strip()]
        if len(keywords) < 3:
            passed = False
            message = f"关键词数量不足（{len(keywords)}个），建议3-5个"
            score = 2
        elif len(keywords) > 6:
            passed = False
            message = f"关键词过多（{len(keywords)}个），建议不超过5个"
            score = 3

    return {"passed": passed, "message": message, "score": score, "max_score": 5}


def _check_chapter_structure(doc) -> Dict[str, Any]:
    """检测章节结构完整性"""
    passed = True
    message = "章节结构完整"
    score = 15

    headings = []
    for p in doc.paragraphs:
        if p.style and p.style.name:
            style_name = p.style.name
            if "Heading" in style_name or "heading" in style_name:
                headings.append((style_name, p.text.strip()))

    if len(headings) < 3:
        passed = False
        message = f"章节结构不完整（仅{len(headings)}个标题），建议至少包含绪论、正文、结论"
        score = 5
    else:
        heading_texts = [h[1] for h in headings]
        has_intro = any(re.search(r"(绪\s*论|引\s*言|前\s*言)", t) for t in heading_texts)
        has_conclusion = any(re.search(r"(结\s*论|总\s*结)", t) for t in heading_texts)

        if not has_intro:
            passed = False
            message = "缺少绪论/引言部分"
            score = 10
        if not has_conclusion:
            if not passed:
                message = "缺少绪论/引言和结论部分"
                score = 5
            else:
                passed = False
                message = "缺少结论部分"
                score = 10

    return {"passed": passed, "message": message, "score": score, "max_score": 15}


def _extract_reference_text(all_text: str) -> str:
    """提取参考文献部分的文本（截截至致谢/附录/声明等后续章节）"""
    # 参考文献标题必须独立成行（前面是换行/开头，后面是换行/冒号/句号/空白）
    # 避免匹配到正文中"参考文献格式"等词语
    ref_section = re.search(
        r"(?:^|\n)\s*(?:[一二三四五六七八九十]+[、.．]\s*)?参\s*考\s*文\s*献\s*[:：.\n]*(.*)",
        all_text, re.DOTALL
    )
    if not ref_section:
        return ""
    ref_text = ref_section.group(1)
    # 截截至后续章节标题（致谢、附录、声明、攻读期间成果等）
    cut_patterns = [
        r"\n\s*致\s*谢\s*\n",
        r"\n\s*附\s*录\s*\n",
        r"\n\s*声\s*明\s*\n",
        r"\n\s*攻读(?:学位|硕士|博士)期间(?:发表|取得|成果)",
        r"\n\s*作者简介",
    ]
    cut_pos = len(ref_text)
    for pat in cut_patterns:
        m = re.search(pat, ref_text)
        if m and m.start() < cut_pos:
            cut_pos = m.start()
    return ref_text[:cut_pos].strip()


def _check_references(doc, all_text: str) -> Dict[str, Any]:
    """检测参考文献格式"""
    passed = True
    message = "参考文献格式正确"
    score = 15

    ref_text = _extract_reference_text(all_text)
    if not ref_text:
        passed = False
        message = "未检测到参考文献部分"
        score = 0
    else:
        # 严格匹配参考文献条目：[1] xxx 或 1. xxx 或 [1]xxx 等
        ref_line_pattern = re.compile(r"^\s*\[?\s*\d+\s*\]?[\.\s、]+")
        ref_lines = [
            l.strip() for l in ref_text.split("\n")
            if l.strip() and ref_line_pattern.match(l.strip())
        ]
        ref_count = len(ref_lines)

        if ref_count < 10:
            passed = False
            message = f"参考文献数量不足（{ref_count}篇），建议不少于10篇"
            score = 8
        else:
            gbt_pattern = re.compile(r"\[\d+\]\s*.+?\.(.+?)[\.,]")
            matched = sum(1 for l in ref_lines if gbt_pattern.search(l))
            if matched < ref_count * 0.7:
                passed = False
                message = f"部分参考文献格式不符合GB/T 7714标准（{matched}/{ref_count}篇符合）"
                score = 10

    return {"passed": passed, "message": message, "score": score, "max_score": 15}


def _check_font_format(doc) -> Dict[str, Any]:
    """检测字体格式"""
    passed = True
    message = "字体字号符合要求"
    score = 10

    body_fonts = set()
    for p in doc.paragraphs[:50]:
        if p.text.strip() and not (p.style and "Heading" in (p.style.name or "")):
            for run in p.runs:
                if run.font.name:
                    body_fonts.add(run.font.name)

    common_fonts = {"宋体", "SimSun", "Times New Roman", "Microsoft YaHei", "微软雅黑"}
    unknown_fonts = body_fonts - common_fonts
    if unknown_fonts and len(unknown_fonts) > 2:
        passed = False
        message = f"检测到非常规正文字体: {', '.join(unknown_fonts)}"
        score = 6

    return {"passed": passed, "message": message, "score": score, "max_score": 10}


def _check_page_layout(doc) -> Dict[str, Any]:
    """检测页面布局（页边距）"""
    passed = True
    message = "页面布局规范"
    score = 10

    try:
        sections = doc.sections
        if sections:
            section = sections[0]
            top_cm = section.top_margin.cm if section.top_margin else 0
            bottom_cm = section.bottom_margin.cm if section.bottom_margin else 0
            left_cm = section.left_margin.cm if section.left_margin else 0
            right_cm = section.right_margin.cm if section.right_margin else 0

            if top_cm < 2.0 or bottom_cm < 2.0:
                passed = False
                message = f"上下页边距偏小（上{top_cm:.1f}cm, 下{bottom_cm:.1f}cm），建议不小于2.5cm"
                score = 6
            elif left_cm < 2.5 or right_cm < 2.0:
                passed = False
                message = f"左右页边距偏小（左{left_cm:.1f}cm, 右{right_cm:.1f}cm），建议左侧不小于3cm"
                score = 6
    except Exception:
        message = "页面布局检测完成（部分信息不可读取）"

    return {"passed": passed, "message": message, "score": score, "max_score": 10}


def _check_citation_format(doc, all_text: str) -> Dict[str, Any]:
    """检测引文标注格式"""
    passed = True
    message = "引文标注格式正确"
    score = 10

    citations = re.findall(r"\[\d+\]", all_text)
    if len(citations) == 0:
        passed = False
        message = "正文中未检测到引文标注（如[1]格式）"
        score = 3
    elif len(citations) < 3:
        passed = False
        message = f"引文标注数量过少（{len(citations)}处），建议在论述中标注引用来源"
        score = 6

    return {"passed": passed, "message": message, "score": score, "max_score": 10}


def _check_figure_table_format(doc, all_text: str) -> Dict[str, Any]:
    """检测图表标注格式"""
    passed = True
    message = "图表格式正确"
    score = 10

    fig_count = len(re.findall(r"图\s*\d+", all_text))
    table_count = len(re.findall(r"表\s*\d+", all_text))

    if fig_count == 0 and table_count == 0:
        message = "未检测到图表标注"
        score = 10
    else:
        issues = []
        if fig_count > 0:
            fig_labels = re.findall(r"图\s*(\d+)", all_text)
            fig_nums = [int(n) for n in fig_labels]
            if fig_nums != sorted(fig_nums):
                issues.append("图编号不连续")
        if table_count > 0:
            table_labels = re.findall(r"表\s*(\d+)", all_text)
            table_nums = [int(n) for n in table_labels]
            if table_nums != sorted(table_nums):
                issues.append("表编号不连续")

        if issues:
            passed = False
            message = "；".join(issues)
            score = 6

    return {"passed": passed, "message": message, "score": score, "max_score": 10}


def _check_appendix_format(all_text: str) -> Dict[str, Any]:
    """检测附录格式"""
    passed = True
    message = "附录格式正确"
    score = 5

    has_appendix = bool(re.search(r"附\s*录", all_text))
    if not has_appendix:
        message = "未检测到附录（可选）"
        score = 5

    return {"passed": passed, "message": message, "score": score, "max_score": 5}


def run_format_check(file_path: str) -> Dict[str, Any]:
    """
    执行完整的格式检测

    :param file_path: 文件物理路径
    :return: {"check_items": {...}, "stats": {...}, "document_stats": {...}}
    """
    if not os.path.exists(file_path):
        raise BusinessException(400, "论文文件不存在，无法执行格式检测")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".docx":
        doc = _safe_extract_docx(file_path)
        if doc is None:
            raise BusinessException(400, "无法解析Word文档，文件可能已损坏")
    elif ext == ".doc":
        raise BusinessException(400, "暂不支持 .doc 格式，请转换为 .docx 后重试")
    elif ext == ".pdf":
        raise BusinessException(400, "暂不支持 PDF 格式检测，请上传 .docx 格式文件")
    else:
        raise BusinessException(400, f"不支持的文件格式: {ext}，请上传 .docx 文件")

    all_text = _extract_all_text(doc)

    # 执行全部检测项
    check_items = {
        "title_format": _check_title_format(doc),
        "abstract_format": _check_abstract_format(doc, all_text),
        "keywords_format": _check_keywords_format(doc, all_text),
        "chapter_structure": _check_chapter_structure(doc),
        "references_format": _check_references(doc, all_text),
        "citation_format": _check_citation_format(doc, all_text),
        "figure_table_format": _check_figure_table_format(doc, all_text),
        "font_format": _check_font_format(doc),
        "page_layout": _check_page_layout(doc),
        "appendix_format": _check_appendix_format(all_text),
    }

    total_score = sum(item["score"] for item in check_items.values())
    max_score = sum(item["max_score"] for item in check_items.values())
    passed_count = sum(1 for item in check_items.values() if item["passed"])
    failed_count = sum(1 for item in check_items.values() if not item["passed"])
    total_items = len(check_items)
    overall_result = "pass" if (total_score / max_score) >= 0.7 else "fail"

    problems = [item["message"] for item in check_items.values() if not item["passed"]]
    problems_summary = "; ".join(problems) if problems else "无"

    suggestions_list = []
    if not check_items["references_format"]["passed"]:
        suggestions_list.append("建议检查参考文献格式，统一使用GB/T 7714标准")
    if not check_items["figure_table_format"]["passed"]:
        suggestions_list.append("建议检查图表编号，确保连续且格式统一")
    if not check_items["abstract_format"]["passed"]:
        suggestions_list.append("建议检查摘要字数，控制在200-1000字之间")
    if not check_items["chapter_structure"]["passed"]:
        suggestions_list.append("建议补充完整的章节结构，至少包含绪论、正文和结论")
    if not check_items["font_format"]["passed"]:
        suggestions_list.append("建议使用标准正文字体（中文宋体、英文Times New Roman）")
    if not check_items["page_layout"]["passed"]:
        suggestions_list.append("建议调整页边距：上2.5cm 下2.5cm 左3cm 右2.5cm")
    if not suggestions_list:
        suggestions_list.append("格式整体良好，请继续保持")
    suggestions = "\n".join(suggestions_list)

    # 提取文档统计信息
    word_count = _count_words(all_text)
    page_count = max(1, word_count // 800)
    chapter_count = sum(1 for p in doc.paragraphs if p.style and "Heading" in (p.style.name or "") and p.text.strip())
    # 参考文献数量：仅统计参考文献部分的条目，而非全文引用
    ref_text_for_stats = _extract_reference_text(all_text)
    ref_line_pattern = re.compile(r"^\s*\[?\s*\d+\s*\]?[\.\s、]+")
    ref_count = sum(
        1 for l in ref_text_for_stats.split("\n")
        if l.strip() and ref_line_pattern.match(l.strip())
    )

    return {
        "check_items": check_items,
        "total_score": total_score,
        "max_score": max_score,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "total_items": total_items,
        "overall_result": overall_result,
        "problems_summary": problems_summary,
        "suggestions": suggestions,
        "document_stats": {
            "word_count": word_count,
            "page_count": page_count,
            "chapter_count": chapter_count,
            "reference_count": ref_count,
        },
    }
