# Panduan Push AIOps Lab ke GitHub

Repo ini aman dijadikan **Public**: semua datanya sintetis dan tidak ada data pribadi.

## 0. Cek jalan dulu

```bash
python -m venv .venv
.venv\Scripts\activate            # Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt
python -m unittest discover tests  # harus: Ran 10 tests ... OK
python run.py
```

## 1. Buat repo kosong

https://github.com/new → nama `aiops-lab` → deskripsi `Explainable AIOps pipeline on synthetic network data: normalize, detect, correlate, root cause` → **Public** → jangan centang apa pun → Create.

## 2. Dua belas commit

```bash
git init

git add .gitignore LICENSE
git commit -m "chore: inisialisasi proyek dengan gitignore dan lisensi MIT"

git add requirements.txt
git commit -m "build: tambah dependensi numpy, pandas, dan scikit-learn"

git add aiops_lab/__init__.py aiops_lab/topology.py
git commit -m "feat: tambah topologi jaringan core, aggregation, dan access"

git add aiops_lab/simulate.py
git commit -m "feat: tambah simulator metrik dan tiga skenario gangguan"

git add aiops_lab/adapters.py
git commit -m "feat: tambah adapter tiga vendor ke canonical data model"

git add aiops_lab/detect.py
git commit -m "feat: tambah deteksi anomali z-score dan pembanding isolation forest"

git add aiops_lab/correlate.py
git commit -m "feat: tambah korelasi alarm berbasis waktu dan topologi"

git add aiops_lab/pipeline.py
git commit -m "feat: gabungkan pipeline dan evaluasi precision recall"

git add run.py
git commit -m "feat: tambah CLI laporan insiden dan runbook"

git add tests/
git commit -m "test: tambah 10 tes adapter, deteksi, korelasi, dan pipeline"

git add web/ .nojekyll
git commit -m "feat: tambah versi web interaktif dengan grafik dan topologi"

git add README.md PANDUAN_GITHUB.md
git commit -m "docs: tambah README dan panduan push"

git log --oneline
git remote add origin https://github.com/muhamadivan1/aiops-lab.git
git push -u origin main
```

## 3. Aktifkan demo web

Settings → Pages → Deploy from a branch → `main` / `(root)` → Save. Demo tampil di
https://muhamadivan1.github.io/aiops-lab/web/

Tambahkan topics di bagian About: `aiops`, `anomaly-detection`, `python`, `scikit-learn`, `observability`.
