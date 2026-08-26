import zipfile, os, pathlib

exclude_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'dist', '.opencode', '.idea', '.next', '.pytest_cache'}
exclude_ext = {'.pyc', '.pyo'}
exclude_files = {'make_zip.py'}
src = pathlib.Path(r'C:\Users\DIMAS\Desktop\Programming\PythonPRO\InternetShop_PRO')
dst = pathlib.Path(r'C:\Users\DIMAS\Desktop\InternetShop_PRO.zip')

if dst.exists():
    dst.unlink()

count = 0
with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if any(f.endswith(ext) for ext in exclude_ext):
                continue
            if f in exclude_files:
                continue
            fp = pathlib.Path(root) / f
            arc = str(fp.relative_to(src.parent)).replace(os.sep, '/')
            try:
                info = zipfile.ZipInfo.from_file(str(fp), arc)
            except ValueError:
                info = zipfile.ZipInfo(arc)
                info.date_time = (2024, 1, 1, 0, 0, 0)
                with open(fp, 'rb') as src_f:
                    data = src_f.read()
                zf.writestr(info, data)
                count += 1
                continue
            with open(fp, 'rb') as src_f:
                data = src_f.read()
            zf.writestr(info, data)
            count += 1

size_mb = dst.stat().st_size / 1024 / 1024
print(f'Done: {count} files, {size_mb:.1f} MB -> {dst}')
