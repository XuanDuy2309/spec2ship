"""Regenerate binary BA fixtures (DOCX, PDF) deterministically with the stdlib.

Run: python tests/fixtures/build_fixtures.py
"""
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent / "ba"

DOCX_CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""
DOCX_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.com/glossary" TargetMode="External"/>
</Relationships>"""
STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:outlineLvl w:val="0"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:outlineLvl w:val="1"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/></w:style>
</w:styles>"""


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _p(text, style=None, page_break_before=False):
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    br = "<w:r><w:lastRenderedPageBreak/></w:r>" if page_break_before else ""
    return f'<w:p>{ppr}{br}<w:r><w:t xml:space="preserve">{_esc(text)}</w:t></w:r></w:p>'


def _tbl(rows):
    out = ["<w:tbl>"]
    for r in rows:
        out.append("<w:tr>" + "".join(f"<w:tc>{_p(c)}</w:tc>" for c in r) + "</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


def build_docx():
    body = [
        _p("Quản lý khách hàng — Yêu cầu nghiệp vụ", "Heading1"),
        _p("Tài liệu mô tả phân hệ quản lý khách hàng cho người dùng nội bộ."),
        _p("1 Tìm kiếm khách hàng", "Heading1"),
        _p("1.1 Tìm theo tên hoặc số điện thoại", "Heading2"),
        _p("Nhân viên bán hàng có thể tìm kiếm khách hàng theo tên hoặc số điện thoại. Tìm kiếm không phân biệt chữ hoa chữ thường."),
        _p("Kết quả hiển thị tối đa 20 khách hàng mỗi trang.", "ListParagraph"),
        _tbl([["Trường", "Quy tắc"], ["Tên", "Khớp một phần"], ["Số điện thoại", "Khớp chính xác"]]),
        _p("2 Tạo khách hàng", "Heading1", page_break_before=True),
        _p("Quản lý bán hàng có thể tạo khách hàng mới với tên, số điện thoại và email. Số điện thoại không được trùng."),
        '<w:p><w:hyperlink r:id="rId9" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:r><w:t>Bảng thuật ngữ</w:t></w:r></w:hyperlink></w:p>',
    ]
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
           'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:body>'
           + "".join(body) + "</w:body></w:document>")
    out = HERE / "quan-ly-khach-hang.docx"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in (("[Content_Types].xml", DOCX_CT), ("_rels/.rels", DOCX_RELS),
                           ("word/_rels/document.xml.rels", DOC_RELS), ("word/styles.xml", STYLES),
                           ("word/document.xml", doc)):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    return out


def _pdf(pages_ops, path):
    """pages_ops: list of content-stream byte strings, one per page."""
    objs = []
    n_pages = len(pages_ops)
    font_id = 3
    first_page = 4
    kids = " ".join(f"{first_page + 2 * i} 0 R" for i in range(n_pages))
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(f"<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>".encode())
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    for i, ops in enumerate(pages_ops):
        content_id = first_page + 2 * i + 1
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode())
        objs.append(b"<< /Length " + str(len(ops)).encode() + b" >>\nstream\n" + ops + b"\nendstream")
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, o in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(bytes(out))
    return path


def _text_ops(lines):
    parts = [b"BT /F1 11 Tf 72 740 Td 14 TL"]
    for ln in lines:
        esc = ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        parts.append(b"(" + esc.encode("cp1252") + b") Tj T*")
        if ln == "":
            pass
    parts.append(b"ET")
    return b"\n".join(parts)


def build_pdf():
    p1 = ["Customer Management - Business Requirements", "", "1 Introduction", "",
          "This document describes the customer management module.", ""]
    p2 = ["3 Functional Requirements", "", "3.1 Search customer", "",
          "Sales staff can search customers by name or phone number.",
          "Search is case-insensitive. Results are paginated, 20 per page.", ""]
    p3 = ["3.2 Create customer", "", "A sales manager can create a customer with name, phone and email.",
          "Phone must be unique.", "", "4 Non-functional Requirements", "",
          "- Search results must return within 1 second."]
    return _pdf([_text_ops(p1), _text_ops(p2), _text_ops(p3)], HERE / "customer-management.pdf")


def build_scanned_pdf():
    draw = b"q 0.8 g 72 72 468 648 re f Q"
    return _pdf([draw, draw], HERE / "scanned.pdf")


if __name__ == "__main__":
    HERE.mkdir(parents=True, exist_ok=True)
    for f in (build_docx(), build_pdf(), build_scanned_pdf()):
        print("wrote", f)
