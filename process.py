#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合式佛典文本處理工具 v10.0 (最終完美版)

此腳本實現了從原始 MarkDown 檔案到結構化、已標記、已分類、並最終轉換格式的
完整自動化流程。此版本新增了強大的預處理模組，以應對更複雜的科判格式。

功能流程:
  1. 讀取原始檔案。
  2. 預處理 (新)：移除反斜線，並為含 [No.***] 的行添加 '$' 前綴。
  3. 初步清洗：移除文件頭資訊及特定格式符號。
  4. 標記內容：使用優先級判斷（先科判，後經/論）進行標記。
  5. 最終清洗：從已標記的文本中移除所有的 "【論】" 字串。
  6. 建立目標資料夾：根據輸入檔名建立 mpps.*** 子目錄。
  7. 格式化提取與寫入：將 jin/lun/kp 內容格式化後儲存至 mpps.*** 子目錄。
  8. 轉換為 Obsidian 連結：將主要內容轉換為帶有三位數補零的連結格式。
  9. 儲存所有最終檔案至 mpps.*** 子目錄。

使用方法:
  python process_sutra_v10.py -i <輸入檔案或目錄> -o <輸出目錄>
  python process_sutra_v10.py -i <輸入檔案或目錄> --inplace
"""
import argparse
import re
import sys
from pathlib import Path

def preprocess_for_kp(text: str) -> str:
    """
    (新) 預處理文本：
    1. 移除所有反斜線。
    2. 為包含 [No.***] 標籤的行，在行首添加 '$' 符號。
    """
    print("  - 執行預處理（移除反斜線、標記新型科判）...")
    # 1. 移除所有反斜線
    text = text.replace('\\', '')
    
    # 2. 處理 [No.***] 標籤
    no_pattern = re.compile(r'\[No\.\d+[^\]]*\]')
    lines = text.splitlines()
    new_lines = []
    for line in lines:
        if no_pattern.search(line):
            # 如果行首不是$，則添加
            if not line.lstrip().startswith('$'):
                new_lines.append('$' + line)
            else:
                new_lines.append(line) # 保持原樣，避免重複添加
        else:
            new_lines.append(line)
            
    return '\n'.join(new_lines)

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

    # 注意：這裡的 '$' 不能移除，因為它是科判的標誌
    replacements = {'**': '', '^^': '', '>': ''}
    for old, new in replacements.items():
        current_text = current_text.replace(old, new)
    
    # 移除行首的空白，但保留 '$'
    cleaned_text = re.sub(r'^[ \t]+(?!\$)', '', current_text, flags=re.MULTILINE)
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
            processed_lines = [re.sub(r'^\s*\$', '', line).lstrip() for line in lines]
            print(f"    - 已移除 {tag_name.upper()} 內容中的 '$' 符號。")

        formatted_body = '\n\n'.join(processed_lines)
        final_content = formatted_body
        if notes_content:
            final_content += f"\n\n---\n\n{notes_content}"
        
        padded_prefix = prefix_num.zfill(3)
        path = output_dir / f"{tag_name}-{padded_prefix}.md"
        path.write_text(final_content, encoding='utf-8')
        print(f"    -> 已格式化並儲存 {tag_name.upper()} 內容至: {path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    format_and_write(jin_lines, 'jin')
    format_and_write(lun_lines, 'lun')
    format_and_write(kp_lines, 'kp')

def transform_to_obsidian_links(text: str) -> str:
    """將帶有標籤的行轉換為 Obsidian 連結格式，並修正數字補零。"""
    print("  - 開始將主要檔案內容轉換為 Obsidian 連結格式...")
    
    pattern = re.compile(r'^\S.* \^(\w+)-(\d+)-(\d+)$', re.MULTILINE)
    
    def repl(m: re.Match) -> str:
        tag, num1_str, num2 = m.groups()
        padded_num1 = num1_str.zfill(3)
        return f"![[mpps.{padded_num1}/{tag}-{padded_num1}#^{tag}-{num1_str}-{num2}]]"

    # 科判行前面可能有 '$'，需要特別處理
    kp_pattern = re.compile(r'^\$\S.* \^kp-(\d+)-(\d+)$', re.MULTILINE)
    
    def kp_repl(m: re.Match) -> str:
        num1_str, num2 = m.groups()
        padded_num1 = num1_str.zfill(3)
        return f"![[mpps.{padded_num1}/kp-{padded_num1}#^kp-{num1_str}-{num2}]]"

    # 先轉換一般行，再轉換科判行
    transformed_text = pattern.sub(repl, text)
    transformed_text = kp_pattern.sub(kp_repl, transformed_text)
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
        main_content, notes_content = split_notes(cleaned_text)
        annotated_main = annotate_text(main_content, prefix_num)
        final_main = remove_lun_marker(annotated_main)

        padded_prefix = prefix_num.zfill(3)
        output_subdir = dst_dir / f"mpps.{padded_prefix}"
        if is_inplace:
            output_subdir = src_path.parent / f"mpps.{padded_prefix}"
        
        output_subdir.mkdir(parents=True, exist_ok=True)
        print(f"  - 所有輸出將存於: {output_subdir}")

        extract_and_format_files(final_main, notes_content, filename_stem, prefix_num, output_subdir)
        
        transformed_content = transform_to_obsidian_links(final_main)

        main_output_path = output_subdir / src_path.name
        main_output_path.write_text(transformed_content, encoding='utf-8')
        print(f"  -> 已儲存轉換後的主要內容至: {main_output_path}")

        if notes_content:
            note_output_path = output_subdir / f"note-{src_path.name}"
            note_output_path.write_text(notes_content, encoding='utf-8')
            print(f"  -> 已分割註釋至: {note_output_path}")

    except Exception as e:
        print(f"處理檔案 {src_path.name} 時發生嚴重錯誤: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description='整合式佛典文本處理工具 v10.0 (最終完美版)')
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
