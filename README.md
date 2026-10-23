# SPK SMART - Penerima Bantuan Sosial Pendidikan (PIP) Siswa SMK

Adaptasi dari template dosen `AhmadFauzi0/Aplikasi_SPK_SMART` untuk tugas individu Sistem Pendukung Keputusan.

## Studi kasus
Rekomendasi penerima Bantuan Sosial Pendidikan (PIP) siswa SMK menggunakan metode SMART (Simple Multi Attribute Rating Technique).

## Dataset
Dataset awal memakai 15 siswa SMKN 2 Binjai tahun 2024 yang dipublikasikan pada:

Zhya Anggraini, Yani Maulita, Kristina Annatasia Br Sitepu (2025), **Sistem Pendukung Keputusan untuk Penentuan Penerima Bantuan Pendidikan di SMK Negeri 2 Binjai Menggunakan Metode WASPAS**, Merkurius: Jurnal Riset Sistem Informasi dan Teknik Informatika, Vol. 3 No. 6. DOI: `10.61132/merkurius.v3i6.1135`.

Raw data dan proporsi bobot diadaptasi dari jurnal tersebut, sedangkan perhitungan pada aplikasi ini menggunakan metode SMART sesuai tugas.

## Kriteria awal
| Kode | Kriteria | Bobot | Tipe SMART |
|---|---|---:|---|
| C1 | Kondisi Rumah | 25% | Benefit* |
| C2 | Penghasilan Orang Tua | 20% | Cost |
| C3 | Jumlah Tanggungan | 10% | Benefit |
| C4 | Jarak Rumah ke Sekolah | 25% | Benefit* |
| C5 | Nilai Rata-rata Rapor | 20% | Benefit |

`*` Arah utilitas C1 dan C4 disesuaikan dengan tujuan **prioritas bantuan**: kondisi tempat tinggal yang lebih tidak layak dan jarak yang lebih jauh dianggap meningkatkan kebutuhan bantuan. Penyesuaian ini dijelaskan transparan pada aplikasi dan manual book.

## Cara menjalankan
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Buka `http://127.0.0.1:5000`.

## Perhitungan SMART
1. Normalisasi bobot: `w_j = W_j / sum(W)`
2. Utility benefit: `u = (x - min) / (max - min)`
3. Utility cost: `u = (max - x) / (max - min)`
4. Skor akhir: `V_i = sum(w_j * u_ij)`
5. Alternatif dengan skor terbesar menjadi prioritas tertinggi.

## Contoh hitung manual A1 - Muhammad Husnan Aris
Bobot ternormalisasi = `[0.25, 0.20, 0.10, 0.25, 0.20]`.

Rentang data:
- C1 min 1, max 3 → A1 = 3 → utility = 1.0000
- C2 min 300.000, max 1.500.000 → A1 = 600.000 → utility cost = 0.7500
- C3 min 1, max 6 → A1 = 4 → utility = 0.6000
- C4 min 1,62, max 10,73 → A1 = 10,10 → utility = 0.9308
- C5 min 81,08, max 93,55 → A1 = 88,41 → utility = 0.5878

Skor akhir:
`V(A1) = (1×0.25) + (0.75×0.20) + (0.60×0.10) + (0.9308×0.25) + (0.5878×0.20)`
`V(A1) = 0.8103`

Angka ini bisa langsung dipakai untuk bagian **hitung manual satu alternatif** di lembar UTS.
