import sys
import inspect
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\arjun\OneDrive\Desktop\multidocument")
from backend.app.services.field_extractor import FieldExtractor

src = inspect.getsource(FieldExtractor._extract_amount_by_label)
print(src)
