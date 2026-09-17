import os
import unittest
from pathlib import Path

from tools.pdf_reader import read_pdf_text


def _build_pdf_bytes(text: str) -> bytes:
    stream_text = f"BT /F1 24 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream_text)} >>\nstream\n{stream_text.decode('latin-1')}\nendstream".encode("latin-1"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_position = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_position}\n%%EOF\n".encode("latin-1"))
    return bytes(pdf)


class PdfReaderTests(unittest.TestCase):
    def test_read_valid_pdf(self):
        pdf_path = Path("data") / "sample.pdf"
        pdf_path.parent.mkdir(exist_ok=True)
        pdf_path.write_bytes(_build_pdf_bytes("BORO BHAI"))
        text = read_pdf_text(str(pdf_path))
        self.assertIn("BORO BHAI", text)


if __name__ == "__main__":
    unittest.main()
