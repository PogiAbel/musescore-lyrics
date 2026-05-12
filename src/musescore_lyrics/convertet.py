import os
import shutil
import subprocess
from pathlib import Path

SUPPORTED_EXTS = ('.ppt', '.pps', '.pptx', '.ppsx')

def find_soffice():
    # try PATH first
    soffice = shutil.which("soffice") or shutil.which("soffice.exe")
    if soffice:
        return soffice
    # common Windows install locations for LibreOffice
    common = [
        r"C:\\Program Files\\LibreOffice\\program\soffice.exe",
        r"C:\\Program Files (x86)\\LibreOffice\\program\soffice.exe",
    ]
    for p in common:
        if Path(p).exists():
            return p
    return None

def convert_with_libreoffice(input_path, out_dir, out_format="ppt"):
    """
    Convert a presentation using LibreOffice (soffice).
    out_format: 'ppt', 'pptx', 'pdf', etc.
    Returns path to the converted file or raises RuntimeError.
    """
    soffice =  "C:\\Program Files\\LibreOffice\\program\soffice.exe"
    if not soffice:
        raise RuntimeError("LibreOffice (soffice) not found. Install LibreOffice or add soffice to PATH.")

    cmd = [
        soffice,
        "--headless",
        "--convert-to", out_format,
        "--outdir", str(out_dir),
        str(input_path)
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Conversion failed: {proc.stderr.strip() or proc.stdout.strip()}")


def main():
    i_folder = Path(r"D:\\ppt_imahaz\\ZV")
    o_folder = Path(r"D:\\ppt_imahaz\\ZV_ppt")
    o_folder.mkdir(parents=True, exist_ok=True)

    for filename in os.listdir(i_folder):
        if not filename.lower().endswith(SUPPORTED_EXTS):
            continue
        input_path = i_folder / filename
        try:
            # convert all to .ppt (change out_format to 'pptx' if you prefer)
            converted = convert_with_libreoffice(input_path, o_folder, out_format="pptx")
            print(f"Converted: {input_path} -> {converted}")
        except Exception as e:
            print(f"Failed to convert {input_path}: {e}")
            exit(1)

if __name__ == "__main__":
    main()