#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合式佛典文本處理工具 v7.0 (最終版)

此腳本實現了從原始 MarkDown 檔案到結構化、已標記、已分類、並最終歸檔的
完整自動化流程。

功能流程:
  1. 讀取、清洗、分割、標記原始文本。
  2. 根據檔名中的卷數，自動建立一個 mpps.{卷數} 的目標資料夾。
  3. 將提取並格式化後的 jin/lun/kp 檔案儲存至目標資料夾。
  4. 將轉換為 Obsidian 連結格式的主檔案及註釋檔案也儲存至目標資料夾。

使用方法:
  python process_sutra_v7.py -i <輸入檔案或目錄> -o <輸出目錄>
  python process_sutra_v7.py -i <輸入檔案或目錄> --inplace
"""
import argparse
import re
import sys
from pathlib import Path

def clean_text(text: str) -> str:
    """執行初步的文字清洗，移除文件頭和 Markdown 格式符號。"""
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
        print(f"警告：未找到標頭標誌 '釋厚觀'。將直接處理原始文本。")
        current_text = text

    replacements = {'\\^': '', '\\$': '$', '**': '', '^^': '', '>': ''}
    for old, new in replacements.items():
        current_text = current_text.replace(old, new)
    
    cleaned_text = re.sub(r'^[ \t]+', '', current_text, flags=re.MULTILINE)
    return cleaned_text

def split_notes(text: str) -> tuple[str, str]:
    """從文本中分割出主要內容和註釋。"""
    match = re.search(r"\n(\[\^\d+\]:.*)", text, re.DOTALL)
    if match:
        main_content = text[:match.start()].strip()
        notes_content = match.group(1).strip()
        return main_content, notes_content
    return text.strip(), ""

def annotate_text(text: str, prefix: str) -> str:
    """根據上下文和符號為文本行添加標記。"""
    kp_pat = re.compile(r'^\s*\$')
    tagged_pat = re.compile(r'\s*\^(?:jin|lun|kp)-\S+-\d+\s*$')
    mode = None
    jin_idx, lun_idx, kp_idx = 0, 0, 0
    out_lines = []

    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip('\n')
        stripped = line.strip()

        if tagged_pat.search(line) or not stripped:
            out_lines.append(raw_line)
            continue
        
        if '【經】' in line: mode = 'jin'
        if '【論】' in line: mode = 'lun'
        
        if kp_pat.match(stripped):
            kp_idx += 1
            suffix = f' ^kp-{prefix}-{kp_idx}'
            out_lines.append(line + suffix + '\n')
        elif stripped == '【論】':
            out_lines.append(raw_line)
        elif mode == 'jin':
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

def extract_and_format_files(main_content: str, notes_content: str, stem: str, output_dir: Path):
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

        formatted_body = '\n\n'.join(lines)
        final_content = formatted_body
        if notes_content:
            final_content += f"\n\n---\n\n{notes_content}"
        
        path = output_dir / f"{tag_name}-{stem}.md"
        path.write_text(final_content, encoding='utf-8')
        print(f"    -> 已格式化並儲存 {tag_name.upper()} 內容至: {path}")

    format_and_write(jin_lines, 'jin')
    format_and_write(lun_lines, 'lun')
    format_and_write(kp_lines, 'kp')

def transform_to_obsidian_links(text: str) -> str:
    """將帶有標籤的行轉換為 Obsidian 連結格式。"""
    print("  - 開始將主要檔案內容轉換為 Obsidian 連結格式...")
    
    pattern = re.compile(r'^\S.* \^(\w+)-(\d+)-(\d+)$', re.MULTILINE)
    
    def repl(m: re.Match) -> str:
        tag, num1, num2 = m.groups()
        return f"![[mpps.{num1}/{tag}-00{num1}#^{tag}-{num1}-{num2}]]"

    transformed_text = pattern.sub(repl, text)
    return transformed_text

def process_file(src_path: Path, base_output_dir: Path, is_inplace: bool):
    """對單一檔案執行完整的處理流程，並將所有輸出歸檔。"""
    print(f"處理中: {src_path.name}...")
    try:
        filename_stem = src_path.stem
        match = re.search(r'\d+', filename_stem)
        prefix = str(int(match.group(0))) if match else filename_stem
        print(f"  - 使用前綴 (卷數): '{prefix}'")
        
        # 步驟 1-5: 核心處理流程
        original_text = src_path.read_text(encoding='utf-8')
        cleaned_text = clean_text(original_text)
        main_content, notes_content = split_notes(cleaned_text)
        annotated_main = annotate_text(main_content, prefix)
        final_main = remove_lun_marker(annotated_main)

        # 步驟 6: 建立 mpps.{卷數} 目標資料夾
        if is_inplace:
            final_output_dir_root = src_path.parent
        else:
            final_output_dir_root = base_output_dir
        
        mpps_output_dir = final_output_dir_root / f"mpps.{prefix}"
        mpps_output_dir.mkdir(parents=True, exist_ok=True)
        print(f"  - 所有輸出將定向至: {mpps_output_dir}")

        # 步驟 7: 提取、格式化並儲存 jin/lun/kp 檔案至 mpps 資料夾
        extract_and_format_files(final_main, notes_content, filename_stem, mpps_output_dir)
        
        # 步驟 8: 轉換主文件內容為 Obsidian 連結
        transformed_content = transform_to_obsidian_links(final_main)

        # 步驟 9: 儲存最終檔案至 mpps 資料夾
        main_output_path = mpps_output_dir / src_path.name
        main_output_path.write_text(transformed_content, encoding='utf-8')
        print(f"  -> 已儲存轉換後的主要內容至: {main_output_path}")

        if notes_content:
            note_output_path = mpps_output_dir / f"note-{src_path.name}"
            note_output_path.write_text(notes_content, encoding='utf-8')
            print(f"  -> 已儲存註釋至: {note_output_path}")

    except Exception as e:
        print(f"處理檔案 {src_path.name} 時發生嚴重錯誤: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description='整合式佛典文本處理工具 v7.0 (最終版)')
    parser.add_argument('-i', '--input', required=True, help='輸入的來源檔案或目錄。')
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument('-o', '--output', help='輸出的目標目錄。')
    output_group.add_argument('--inplace', action='store_true', help='在來源檔案相同目錄下生成 mpps.{卷數} 資料夾。')
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
            # 傳遞根輸出目錄，讓 process_file 內部建立 mpps 子目錄
            process_file(src_file, dest_root, args.inplace)
        
        print(f"\n處理完成！共處理了 {len(process_list)} 個檔案。")

if __name__ == '__main__':
    main()
