import csv
from datetime import datetime

def SQL_Instruction(file_path, model, role, content=None):
    if model == "write":
        with open(file_path, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            with open(file_path, "r", encoding='utf-8') as g:
                reader = csv.reader(g)
                rows = list(reader)
                next_id = len(rows)
            writer.writerow([
                next_id,
                role,
                content if content is not None else "",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
        return next_id