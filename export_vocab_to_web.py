import os
import json

# Thư mục nguồn chứa cây từ vựng và file JSON đích
SOURCE_DIR = "AnkiCSVSource"
OUTPUT_JSON = "voca-data.json"

def parse_txt_vocab(file_path):
    """Đọc file .txt luyện gõ (hỗ trợ phân cách bằng Tab, ---, hoặc -)"""
    vocab_list = []
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            for line_idx, line in enumerate(f, start=1):
                line_str = line.strip()
                
                # Bỏ qua dòng trống hoặc dòng chú thích
                if not line_str or line_str.startswith('#'):
                    continue
                
                # Ưu tiên tách bằng Tab (chuẩn Anki export), sau đó mới đến các dấu khác
                if '\t' in line_str:
                    parts = line_str.split('\t', 1)
                elif ' --- ' in line_str:
                    parts = line_str.split(' --- ', 1)
                elif ' - ' in line_str:
                    parts = line_str.split(' - ', 1)
                elif ',' in line_str:
                    parts = line_str.split(',', 1)
                else:
                    parts = [line_str, "---"]
                
                word = parts[0].strip()
                meaning = parts[1].strip() if len(parts) > 1 else "---"
                
                if word and meaning != "IMG":
                    vocab_list.append({
                        "id": line_idx,
                        "word": word,
                        "meaning": meaning
                    })
    except Exception as e:
        print(f"Lỗi đọc file {file_path}: {e}")
    
    return vocab_list

def scan_directory(current_path):
    """
    Đệ quy duyệt cây thư mục:
    - Bỏ qua các file .csv
    - Nhận diện thư mục sâu nhất chứa file .txt trùng tên với thư mục để làm bài gõ.
    """
    node_name = os.path.basename(current_path)
    
    try:
        entries = sorted(os.listdir(current_path))
    except FileNotFoundError:
        return None

    # Lọc ra các thư mục con và file .txt có trong thư mục hiện tại
    subdirectories = []
    txt_files = {}

    for entry in entries:
        if entry.startswith('.'):
            continue
        full_path = os.path.join(current_path, entry)
        
        if os.path.isdir(full_path):
            subdirectories.append(full_path)
        elif os.path.isfile(full_path) and entry.endswith('.txt'):
            # Lưu lại tên file .txt (bỏ đuôi .txt) để đối chiếu
            file_base_name = os.path.splitext(entry)[0]
            txt_files[file_base_name] = full_path

    children = []
    
    # 1. Duyệt tiếp các thư mục con cấp sâu hơn
    for sub_dir in subdirectories:
        sub_node = scan_directory(sub_dir)
        if sub_node:
            children.append(sub_node)

    # 2. Kiểm tra xem thư mục hiện tại có phải là thư mục chứa file .txt trùng tên không
    # (Tên file .txt trùng với tên thư mục hiện tại, ví dụ thư mục A chứa A.txt)
    if node_name in txt_files:
        target_txt_path = txt_files[node_name]
        # Sửa ở đây: Lấy đường dẫn chuẩn tuyệt đối để chắc chắn mở được file
        abs_txt_path = os.path.abspath(target_txt_path)
        vocab_data = parse_txt_vocab(abs_txt_path)
        
        # Trả về node bài gõ (Deck leaf node)
        return {
            "name": node_name,
            "type": "deck", # Đánh dấu đây là bài gõ
            "path": target_txt_path,
            "vocab": vocab_data,
            "vocab_count": len(vocab_data)
        }

    # Nếu thư mục này chỉ chứa các thư mục con (chưa phải tầng sâu nhất chứa bài gõ)
    if children:
        return {
            "name": node_name,
            "type": "folder",
            "children": children
        }
    
    return None

def main():
    if not os.path.exists(SOURCE_DIR):
        print(f"Không tìm thấy thư mục gốc '{SOURCE_DIR}'!")
        return

    print(f"Đang quét cây thư mục từ '{SOURCE_DIR}' (Chỉ lấy bài gõ .txt trùng tên thư mục)...")
    
    tree_data = scan_directory(SOURCE_DIR)
    
    if not tree_data:
        print("Không tìm thấy cấu trúc thư mục hoặc bài gõ hợp lệ nào!")
        return

    # Gói kết quả vào cấu trúc gốc chuẩn
    output_data = {
        "name": SOURCE_DIR,
        "type": "folder",
        "children": tree_data.get("children", [tree_data]) if "children" in tree_data else [tree_data]
    }

    # Ghi ra file JSON đích để web sử dụng
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
        
    print(f"Thành công! Đã xuất cây thư mục và dữ liệu bài gõ ra file '{OUTPUT_JSON}'.")

if __name__ == "__main__":
    main()
