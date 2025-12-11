# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import webbrowser
import struct
import json
import sys
import os
import re
import subprocess
from datetime import datetime

# ==========================================
# 核心解析逻辑 (UniversalMP4Parser) - 保持不变
# ==========================================
class UniversalMP4Parser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)
        self.result = {
            "filename": os.path.basename(file_path),
            "full_path": file_path,
            "has_gps": False,
            "source": "unknown",
            "latitude": None,
            "longitude": None,
            "altitude": 0,
            "creation_date": None,
            "message": ""
        }

    def parse(self):
        if self._parse_binary_atoms(): return self.result
        if self._parse_with_ffprobe(): return self.result
        self.result["message"] = "未发现可识别的 GPS 信息"
        return self.result

    def _bytes_to_int(self, b):
        return int.from_bytes(b, byteorder='big')

    def _parse_binary_atoms(self):
        try:
            with open(self.file_path, "rb") as f:
                offset = 0
                while offset < self.file_size:
                    f.seek(offset)
                    header = f.read(8)
                    if len(header) < 8: break
                    atom_size = self._bytes_to_int(header[0:4])
                    atom_type = header[4:8].decode('latin1', errors='ignore')
                    if atom_size == 0: break 
                    if atom_size == 1: 
                        header_large = f.read(8)
                        atom_size = int.from_bytes(header_large, 'big')
                        data_start_offset = 16
                    else: data_start_offset = 8

                    if atom_type == 'moov':
                        read_size = min(atom_size - data_start_offset, 50 * 1024 * 1024)
                        moov_data = f.read(read_size)
                        self._analyze_moov_content(moov_data)
                        return self.result["has_gps"] or self.result["creation_date"]
                    offset += atom_size
                    if offset > 50 * 1024 * 1024 and offset < self.file_size - 10 * 1024 * 1024: pass 
        except Exception as e: self.result["message"] = f"Binary parse error: {str(e)}"
        return False

    def _analyze_moov_content(self, data):
        mvhd_pos = data.find(b'mvhd')
        if mvhd_pos != -1:
            try:
                ver = data[mvhd_pos+4]
                if ver == 0: ts = struct.unpack(">I", data[mvhd_pos+8:mvhd_pos+12])[0]
                else: ts = struct.unpack(">Q", data[mvhd_pos+8:mvhd_pos+16])[0]
                if ts > 2082844800:
                    unix_ts = ts - 2082844800
                    self.result["creation_date"] = datetime.fromtimestamp(unix_ts).strftime('%Y-%m-%d %H:%M:%S')
            except: pass

        loci_pos = data.find(b'loci')
        if loci_pos != -1:
            try:
                cursor = loci_pos + 10 
                while cursor < len(data) and data[cursor] != 0: cursor += 1
                cursor += 2 
                if cursor + 12 <= len(data):
                    lon_raw = struct.unpack(">i", data[cursor:cursor+4])[0]
                    lat_raw = struct.unpack(">i", data[cursor+4:cursor+8])[0]
                    alt_raw = struct.unpack(">i", data[cursor+8:cursor+12])[0]
                    self.result["latitude"] = lat_raw / 65536.0
                    self.result["longitude"] = lon_raw / 65536.0
                    self.result["altitude"] = alt_raw / 65536.0
                    self.result["has_gps"] = True
                    self.result["source"] = "loci (OMA Binary)"
                    return
            except: pass

        xyz_pos = data.find(b'\xa9xyz')
        if xyz_pos == -1: xyz_pos = data.find(b'location')
        if xyz_pos != -1:
            try:
                search_window = data[xyz_pos:xyz_pos+100].decode('utf-8', errors='ignore')
                self._extract_iso6709(search_window)
                if self.result["has_gps"]:
                    self.result["source"] = "ISO-6709 Metadata"
                    return
            except: pass

    def _extract_iso6709(self, text):
        pattern = r"([+-]\d+\.?\d*)([+-]\d+\.?\d*)([+-]\d+\.?\d*)?\/?"
        match = re.search(pattern, text)
        if match:
            self.result["latitude"] = float(match.group(1))
            self.result["longitude"] = float(match.group(2))
            if match.group(3): self.result["altitude"] = float(match.group(3))
            self.result["has_gps"] = True

    def _parse_with_ffprobe(self):
        try:
            cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", self.file_path]
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')
            data = json.loads(out)
            tags = data.get("format", {}).get("tags", {})
            if not self.result["creation_date"]: self.result["creation_date"] = tags.get("creation_time")
            for key, val in tags.items():
                if key in ["location", "com.apple.quicktime.location.ISO6709", "xyz"]:
                    self._extract_iso6709(val)
                    if self.result["has_gps"]: 
                        self.result["source"] = "FFprobe"
                        return True
        except: pass
        return self.result["has_gps"]

# ==========================================
# GUI 界面逻辑 (已移除所有 Emoji)
# ==========================================
class GPSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MP4 GPS Info")
        self.root.geometry("600x500")
        
        top_frame = tk.Frame(root, pady=10)
        top_frame.pack(fill="x", padx=10)
        
        # 修改点 1: 移除了文件夹 Emoji
        self.btn_select = tk.Button(top_frame, text="[+] 选择视频文件...", command=self.select_file, bg="#e1e1e1")
        self.btn_select.pack(side="left", padx=5)
        
        self.lbl_file = tk.Label(top_frame, text="未选择文件", fg="gray", anchor="w")
        self.lbl_file.pack(side="left", fill="x", expand=True)

        self.txt_output = scrolledtext.ScrolledText(root, height=15, font=("Consolas", 10))
        self.txt_output.pack(fill="both", expand=True, padx=10, pady=5)
        
        bottom_frame = tk.Frame(root, pady=10)
        bottom_frame.pack(fill="x", padx=10)

        # 修改点 2: 移除了地球 Emoji
        self.btn_map = tk.Button(bottom_frame, text="[Map] 在浏览器打开地图", command=self.open_map, state="disabled", bg="#4CAF50", fg="white")
        self.btn_map.pack(side="left", padx=5)

        # 修改点 3: 移除了剪贴板 Emoji
        self.btn_copy = tk.Button(bottom_frame, text="[JSON] 复制数据", command=self.copy_json, state="disabled")
        self.btn_copy.pack(side="right", padx=5)

        self.current_data = None

    def select_file(self):
        file_path = filedialog.askopenfilename(title="选择视频", filetypes=[("Video Files", "*.mp4 *.mov *.m4v *.3gp"), ("All Files", "*.*")])
        if not file_path: return
        self.lbl_file.config(text=os.path.basename(file_path), fg="black")
        self.process_file(file_path)

    def process_file(self, file_path):
        self.txt_output.delete(1.0, tk.END)
        self.txt_output.insert(tk.END, "正在分析...\n")
        self.root.update()
        parser = UniversalMP4Parser(file_path)
        self.current_data = parser.parse()
        self.display_result()

    def display_result(self):
        data = self.current_data
        self.txt_output.delete(1.0, tk.END)

        # 修改点 4: 移除了打钩和打叉的 Emoji
        if data["has_gps"]:
            status_symbol = "[OK]"
            self.btn_map.config(state="normal", bg="#4CAF50")
        else:
            status_symbol = "[NO GPS]"
            self.btn_map.config(state="disabled", bg="#cccccc")

        out_str = f"分析结果: {status_symbol}\n"
        out_str += "-" * 30 + "\n"
        out_str += f"文件名: {data['filename']}\n"
        out_str += f"时间:   {data.get('creation_date', '未知')}\n"
        
        if data["has_gps"]:
            out_str += f"\n[GPS 信息]\n"
            out_str += f"纬度: {data['latitude']}\n"
            out_str += f"经度: {data['longitude']}\n"
            out_str += f"海拔: {data['altitude']} m\n"
            out_str += f"来源: {data['source']}\n"
        else:
            out_str += f"\n[未找到 GPS]\n"
            out_str += f"原因: {data.get('message', '无数据')}\n"

        self.txt_output.insert(tk.END, out_str)
        self.txt_output.insert(tk.END, "\n\n" + "-" * 30 + "\n原始 JSON:\n")
        self.txt_output.insert(tk.END, json.dumps(data, indent=4, ensure_ascii=False))
        self.btn_copy.config(state="normal")

    def open_map(self):
        if self.current_data and self.current_data["has_gps"]:
            url = f"https://www.google.com/maps?q={self.current_data['latitude']},{self.current_data['longitude']}"
            webbrowser.open(url)

    def copy_json(self):
        if self.current_data:
            self.root.clipboard_clear()
            self.root.clipboard_append(json.dumps(self.current_data, indent=4, ensure_ascii=False))
            messagebox.showinfo("成功", "JSON 已复制")

if __name__ == "__main__":
    root = tk.Tk()
    app = GPSApp(root)
    root.mainloop()
