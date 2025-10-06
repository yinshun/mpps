#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合式佛典文本處理工具 v12.0 (最終完美版)

此版本修正了多行註腳（footnote）無法正確解析的問題，新增了註腳合併功能。
這是整個開發流程的最終穩定版本。

功能流程:
  1. 讀取原始檔案。
  2. 預處理：移除反斜線，並為含 [No.***] 的行添加 '$' 前綴。
  3. 初步清洗：移除文件頭資訊及特定格式符號。
  4. 分割內容與註腳。
  5. 註腳格式修正 (新)：將跨越多行的註腳內容合併為單行。
  6. 標記內容：使用優先級判斷進行標記。
  7. 最終清洗：移除內文中的 "【論】" 字串。
  8. 建立目標資料夾：建立 mpps.*** 子目錄。
  9. 格式化提取與寫入：將分類內容格式化後儲存，並附加修正後的註腳。
  10. 轉換為 Obsidian 連結。
  11. 儲存所有最終檔案。

使用方法:
  python process_sutra_v12.py -i <輸入檔案或目錄> -o <輸出目錄>
  python process_sutra_v12.py -i <輸入檔案或目錄> --inplace
"""
import argparse
import re
import sys
from pathlib import Path

def preprocess_for_kp(text: str) -> str:
    """預處理文本：移除反斜線，並為 [No.***] 行添加 '$' 前綴。"""
    print("  - 執行預處理（移除反斜線、標記新型科判）...")
    text = text.replace('\\', '')
    no_pattern = re.compile(r'\[No\.\d+[^\]]*\]')
    lines = text.splitlines()
    new_lines = []
    for line in lines:
        if no_pattern.search(line):
            if not line.lstrip().startswith('$'):
                new_lines.append('$' + line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    return '\n'.join(new_lines)

def clean_text(text: str) -> str:
    """執行初步的文字清洗。"""
    lines = text.splitlines(keepends=True)
    header_end_index = -1
    for i, line in enumerate(lines[:20]):
        if '釋厚觀' in line:
            header_end_index = i
            break
    
    if header_end_index != -1:
        content_lines = lines[header_end_index + 1:]
        while content_lines and not content_lines[0].strip():
            content_lines.pop(0)
        current_text = "".join(content_lines)
    else:
        print(f"警告：未找到標頭標誌 '釋厚觀'。")
        current_text = text

    replacements = {'**': '', '^^': '', '>': ''}
    for old, new in replacements.items():
        current_text = current_text.replace(old, new)
    
    cleaned_text = re.sub(r'^[ \t]+(?!\$)', '', current_text, flags=re.MULTILINE)
    return cleaned_text

def split_notes(text: str) -> tuple[str, str]:
    """從文本中分割出主要內容和註釋。"""
    # 搜尋註腳區塊的起始標記
    match = re.search(r"(\n\s*\[\^\d+\]:.*)", text, re.DOTALL)
    if match:
        main_content = text[:match.start()].strip()
        # 取得整個註腳區塊
        notes_content = match.group(1).strip()
        return main_content, notes_content
    return text.strip(), ""

def merge_multiline_footnotes(notes_text: str) -> str:
    """(新) 將多行註腳定義合併為單行，以符合 Markdown 標準。"""
    if not notes_text:
        return ""

    print("  - 修正多行註腳格式...")
    # 使用正規表達式來分割每個註腳定義
    # `(?=\[\^\d+\]:)` 是一個正向預查，它會匹配下一個註腳的開頭，但不會消耗它
    # 這使得我們可以按每個註腳塊來分割文本
    note_blocks = re.split(r'(?=\[\^\d+\]:)', notes_text)
    
    merged_notes = []
    for block in note_blocks:
        if block.strip():
            # 將塊內的換行符（和多個空格）替換為單個空格
            single_line_block = re.sub(r'\s+', ' ', block).strip()
            merged_notes.append(single_line_block)
            
    return '\n'.join(merged_notes)

def annotate_text(text: str, prefix: str) -> str:
    """根據優先級（先科判，後經/論）為文本行添加標記。"""
    print("  - 執行優先級標記（科判 > 經 > 論）...")
    kp_pat = re.compile(r'^\s*\$')
    tagged_pat = re.compile(r'\s*\^(?:jin|lun|kp)-\S+-\d+\s*$')
    
    mode = 'lun'
    jin_idx, lun_idx, kp_idx = 0, 0, 0
    out_lines = []

    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip('\n')
        stripped = line.strip()

        if tagged_pat.search(line) or not stripped:
            out_lines.append(raw_line)
            continue
        
        if kp_pat.match(stripped):
            kp_idx += 1
            suffix = f' ^kp-{prefix}-{kp_idx}'
            out_lines.append(line + suffix + '\n')
            continue

        if '【經】' in line: mode = 'jin'
        if '【論】' in line: mode = 'lun'

        if mode == 'jin':
            jin_idx += 1
            suffix = f' ^jin-{prefix}-{jin_idx}'
            out_lines.append(line + suffix + '\n')
        else:
            lun_idx += 1
            suffix = f' ^lun-{prefix}-{lun_idx}'
            out_lines.append(line + suffix + '\n')

    return ''.join(out_lines)

def remove_lun_marker(text: str) -> str:
    """從文本中移除所有的 "【論】" 字串。"""
    return text.replace('【論】', '')

def extract_and_format_files(main_content: str, notes_content: str, stem: str, prefix_num: str, output_dir: Path):
    """提取標籤行，格式化後，儲存到獨立檔案。"""
    print(f"  - 開始提取並格式化分類檔案...")
    jin_lines, lun_lines, kp_lines = [], [], []

    pattern = re.compile(r"^(.*)\s*\^((jin|lun|kp)-\S+-\d+)\s*$")

    for line in main_content.splitlines():
        match = pattern.match(line)
        if not match: continue
        
        tag_type = match.group(3)
        if tag_type == 'jin': jin_lines.append(line)
        elif tag_type == 'lun': lun_lines.append(line)
        elif tag_type == 'kp': kp_lines.append(line)

    def format_and_write(lines: list, tag_name: str):
        if not lines: return
        
        processed_lines = lines
        if tag_name == 'kp':
            processed_lines = [re.sub(r'^\s*\$+', '', line).lstrip() for line in lines]
            print(f"    - 已移除 {tag_name.upper()} 內容中的 '$' 符號。")

        formatted_body = '\n\n'.join(processed_lines)
        final_content = formatted_body
        if notes_content:
            final_content += f"\n\n---\n\n{notes_content}"
        
        padded_prefix = prefix_num.zfill(3)
        # 檔名也使用補零的數字
        stem_padded = padded_prefix
        path = output_dir / f"{tag_name}-{stem_padded}.md"
        path.write_text(final_content, encoding='utf-8')
        print(f"    -> 已格式化並儲存 {tag_name.upper()} 內容至: {path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    format_and_write(jin_lines, 'jin')
    format_and_write(lun_lines, 'lun')
    format_and_write(kp_lines, 'kp')

def transform_to_obsidian_links(text: str) -> str:
    """將所有帶有標籤的行統一轉換為 Obsidian 連結格式。"""
    print("  - 開始將主要檔案內容轉換為 Obsidian 連結格式...")
    pattern = re.compile(r'^(.*\S.*) \^(\w+)-(\d+)-(\d+)$', re.MULTILINE)
    
    def repl(m: re.Match) -> str:
        tag, num1_str, num2 = m.group(2), m.group(3), m.group(4)
        padded_num1 = num1_str.zfill(3)
        return f"![[mpps.{padded_num1}/{tag}-{padded_num1}#^{tag}-{num1_str}-{num2}]]"

    transformed_text = pattern.sub(repl, text)
    return transformed_text

def process_file(src_path: Path, dst_dir: Path, is_inplace: bool):
    """對單一檔案執行完整的處理流程。"""
    print(f"\n處理中: {src_path.name}...")
    try:
        filename_stem = src_path.stem
        match = re.search(r'(\d+)', filename_stem)
        if not match:
            print(f"錯誤：檔名 {filename_stem} 中未找到數字，無法處理。")
            return
            
        prefix_num = match.group(1)
        print(f"  - 使用前綴數字: '{prefix_num}'")
        
        original_text = src_path.read_text(encoding='utf-8')
        
        # 核心處理流程
        preprocessed_text = preprocess_for_kp(original_text)
        cleaned_text = clean_text(preprocessed_text)
        main_content, notes_content_raw = split_notes(cleaned_text)
        
        # (新) 修正註腳格式
        notes_content_merged = merge_multiline_footnotes(notes_content_raw)
        
        annotated_main = annotate_text(main_content, prefix_num)
        final_main = remove_lun_marker(annotated_main)

        padded_prefix = prefix_num.zfill(3)
        output_subdir = dst_dir / f"mpps.{padded_prefix}"
        if is_inplace:
            output_subdir = src_path.parent / f"mpps.{padded_prefix}"
        
        output_subdir.mkdir(parents=True, exist_ok=True)
        print(f"  - 所有輸出將存於: {output_subdir}")

        extract_and_format_files(final_main, notes_content_merged, filename_stem, prefix_num, output_subdir)
        
        transformed_content = transform_to_obsidian_links(final_main)

        main_output_path = output_subdir / src_path.name
        main_output_path.write_text(transformed_content, encoding='utf-8')
        print(f"  -> 已儲存轉換後的主要內容至: {main_output_path}")

        if notes_content_merged:
            note_output_path = output_subdir / f"note-{src_path.name}"
            note_output_path.write_text(notes_content_merged, encoding='utf-8')
            print(f"  -> 已儲存修正後的註釋至: {note_output_path}")

    except Exception as e:
        print(f"處理檔案 {src_path.name} 時發生嚴重錯誤: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description='整合式佛典文本處理工具 v12.0 (最終完美版)')
    parser.add_argument('-i', '--input', required=True, help='輸入的來源檔案或目錄。')
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument('-o', '--output', help='輸出的目標目錄。')
    output_group.add_argument('--inplace', action='store_true', help='原地修改檔案 (分類檔與註釋檔將建立於同目錄的 mpps.*** 子目錄中)。')
    parser.add_argument('--ext', nargs='*', default=['.md', '.txt'], help='目錄模式下要處理的副檔名 (預設: .md .txt)。')
    args = parser.parse_args()

    input_path = Path(args.input)
    
    if not input_path.exists():
        sys.exit(f"錯誤：輸入路徑不存在: {input_path}")

    if input_path.is_file():
        dest_dir = Path(args.output) if not args.inplace else input_path.parent
        process_file(input_path, dest_dir, args.inplace)
    elif input_path.is_dir():
        dest_root = Path(args.output) if not args.inplace else input_path
        
        file_list = [p for p in input_path.rglob('*') if p.is_file() and p.suffix.lower() in [e.lower() for e in args.ext]]
        process_list = [f for f in file_list if not f.name.startswith(('note-', 'jin-', 'lun-', 'kp-'))]
        
        if not process_list:
            print(f"在目錄 '{input_path}' 中找不到任何符合條件的檔案進行處理。")
            return
            
        for src_file in process_list:
            if args.inplace:
                process_file(src_file, src_file.parent, args.inplace)
            else:
                relative_path = src_file.relative_to(input_path)
                dest_dir = dest_root / relative_path.parent
                process_file(src_file, dest_dir, args.inplace)

        print(f"\n處理完成！共處理了 {len(process_list)} 個檔案。")

if __name__ == '__main__':
    main()
