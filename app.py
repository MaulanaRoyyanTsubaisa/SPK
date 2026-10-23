from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import os
import pandas as pd
import numpy as np
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import base64

from core.models import init_db, Project, SessionLocal
from core.engine import SMARTEngine, SMARTInput

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-smart-spk-2026")
engine = SMARTEngine()
init_db()


def default_study():
    return {
        "criteria": [
            "Kondisi Rumah",
            "Penghasilan Orang Tua",
            "Jumlah Tanggungan",
            "Jarak Rumah ke Sekolah",
            "Nilai Rata-rata Rapor",
        ],
        "types": ["benefit", "cost", "benefit", "benefit", "benefit"],
        "weights": [25.0, 20.0, 10.0, 25.0, 20.0],
        "weight_method": "direct",
        "alternatives": [
            "Muhammad Husnan Aris", "Irma Khairani", "Nur Alfajar", "Virly Fadiah Putri",
            "Nabila", "Ilyas Ramadhanu", "Adit Rahmazi", "Rizky Zulkarnain",
            "Dimas Dwi Andika", "Nico Tri Ramadhana", "Reza Prasetio", "Binar Sembiring",
            "Rinta Purba", "Reza Maulana", "Salsabilah Balqis",
        ],
        "performance": [
            [3, 600000, 4, 10.10, 88.41],
            [3, 400000, 3, 9.36, 88.03],
            [1, 1000000, 2, 8.09, 88.19],
            [2, 700000, 2, 10.73, 81.08],
            [3, 450000, 6, 6.88, 84.86],
            [1, 1200000, 5, 2.71, 91.49],
            [3, 1500000, 1, 4.08, 81.98],
            [3, 1000000, 4, 2.49, 88.89],
            [1, 800000, 6, 10.10, 85.29],
            [1, 1000000, 1, 7.51, 81.18],
            [3, 1200000, 2, 3.11, 85.19],
            [3, 550000, 1, 1.62, 84.92],
            [2, 1000000, 1, 5.96, 85.11],
            [3, 300000, 5, 8.42, 89.15],
            [2, 800000, 4, 10.26, 93.55],
        ],
        "units": ["Skor 1-3", "Rp/bulan", "Orang", "Km", "Nilai"],
        "source_title": "Sistem Pendukung Keputusan untuk Penentuan Penerima Bantuan Pendidikan di SMK Negeri 2 Binjai Menggunakan Metode WASPAS",
        "source_authors": "Zhya Anggraini, Yani Maulita, Kristina Annatasia Br Sitepu (2025)",
        "source_doi": "10.61132/merkurius.v3i6.1135",
        "source_note": "Data siswa SMKN 2 Binjai tahun 2024. Dataset dan proporsi bobot diadaptasi ke metode SMART sesuai tugas. Arah utilitas disesuaikan dengan tujuan prioritas bantuan.",
    }


def ensure_seed_project():
    with SessionLocal() as db:
        existing = db.query(Project).filter(Project.name == "Penerima Bantuan Sosial Pendidikan (PIP) Siswa SMK").first()
        if not existing:
            db.add(Project(
                name="Penerima Bantuan Sosial Pendidikan (PIP) Siswa SMK",
                description="Studi kasus SPK metode SMART untuk rekomendasi penerima Bantuan Sosial Pendidikan (PIP) siswa SMK.",
                data_json=default_study(),
            ))
            db.commit()


ensure_seed_project()


def load_project(project_id):
    with SessionLocal() as db:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            db.expunge(project)
        return project


@app.route("/")
def index():
    with SessionLocal() as db:
        projects = db.query(Project).order_by(Project.id.asc()).all()
    return render_template("index.html", projects=projects)


@app.route("/materi")
def view_materi():
    return render_template("materi.html")


@app.route("/project/create", methods=["POST"])
def create_project():
    name = (request.form.get("name") or "").strip()
    desc = (request.form.get("description") or "").strip()
    if not name:
        flash("Nama studi kasus wajib diisi.", "danger")
        return redirect(url_for("index"))

    with SessionLocal() as db:
        if db.query(Project).filter(Project.name == name).first():
            flash("Nama studi kasus sudah digunakan.", "danger")
        else:
            db.add(Project(name=name, description=desc, data_json=default_study()))
            db.commit()
            flash("Studi kasus baru berhasil dibuat dari template data Bantuan Sosial Pendidikan (PIP).", "success")
    return redirect(url_for("index"))


@app.route("/project/<int:id>")
def view_project(id):
    project = load_project(id)
    if not project:
        return "Studi kasus tidak ditemukan", 404
    return render_template("project.html", project=project, data=project.data_json)


@app.route("/project/<int:id>/update", methods=["POST"])
def update_data(id):
    project = load_project(id)
    if not project:
        return "Studi kasus tidak ditemukan", 404

    try:
        criteria = [x.strip() for x in request.form.getlist("criteria[]") if x.strip()]
        types = request.form.getlist("types[]")
        weights = [float(w) for w in request.form.getlist("weights[]")]
        alternatives = [x.strip() for x in request.form.getlist("alternatives[]") if x.strip()]
        weight_method = request.form.get("weight_method", "direct")
        perf_flat = [float(p) for p in request.form.getlist("perf[]")]

        if len(criteria) < 2 or len(alternatives) < 2:
            raise ValueError("Minimal 2 kriteria dan 2 alternatif diperlukan.")
        if len(types) != len(criteria) or len(weights) != len(criteria):
            raise ValueError("Struktur kriteria tidak valid.")
        expected = len(alternatives) * len(criteria)
        if len(perf_flat) != expected:
            raise ValueError("Jumlah nilai matriks tidak sesuai.")
        performance = np.array(perf_flat).reshape(len(alternatives), len(criteria)).tolist()

        old = project.data_json or {}
        updated_json = {
            **old,
            "criteria": criteria,
            "types": types,
            "weights": weights,
            "weight_method": weight_method,
            "alternatives": alternatives,
            "performance": performance,
            "units": old.get("units", ["" for _ in criteria])[:len(criteria)] + [""] * max(0, len(criteria) - len(old.get("units", []))),
        }
        with SessionLocal() as db:
            target = db.query(Project).filter(Project.id == id).first()
            target.data_json = updated_json
            db.commit()
        flash("Data dan konfigurasi SMART berhasil disimpan.", "success")
    except Exception as exc:
        flash(f"Data belum dapat disimpan: {exc}", "danger")
    return redirect(url_for("view_project", id=id))


@app.route("/project/<int:id>/upload", methods=["POST"])
def upload_file(id):
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Pilih file CSV atau Excel terlebih dahulu.", "danger")
        return redirect(url_for("view_project", id=id))

    try:
        df = pd.read_csv(file) if file.filename.lower().endswith(".csv") else pd.read_excel(file)
        if df.shape[1] < 3 or df.shape[0] < 2:
            raise ValueError("File harus memiliki kolom nama alternatif dan minimal dua kriteria.")
        alts = df.iloc[:, 0].astype(str).tolist()
        criteria = [str(c) for c in df.columns[1:]]
        performance = df.iloc[:, 1:].astype(float).values.tolist()

        with SessionLocal() as db:
            proj = db.query(Project).filter(Project.id == id).first()
            current = proj.data_json or {}
            current.update({
                "criteria": criteria,
                "types": ["benefit"] * len(criteria),
                "weights": [100.0 / len(criteria)] * len(criteria),
                "weight_method": "direct",
                "alternatives": alts,
                "performance": performance,
                "units": [""] * len(criteria),
            })
            proj.data_json = current
            db.commit()
        flash("Data berhasil diimpor. Periksa kembali tipe benefit/cost dan bobot sebelum menghitung.", "success")
    except Exception as exc:
        flash(f"Impor gagal: {exc}", "danger")
    return redirect(url_for("view_project", id=id))


@app.route("/project/<int:id>/calculate")
def calculate_project(id):
    project = load_project(id)
    if not project:
        return "Studi kasus tidak ditemukan", 404
    p_data = project.data_json

    try:
        inp = SMARTInput(
            alternatives=p_data["alternatives"],
            criteria=p_data["criteria"],
            performance=np.array(p_data["performance"], dtype=float),
            weights_raw=np.array(p_data["weights"], dtype=float),
            types=p_data["types"],
            weight_method=p_data.get("weight_method", "direct"),
        )
        results = engine.calculate(inp)
        target_idx = 0
        w_vals, scores_history = engine.run_oat_sensitivity(inp, target_idx)

        plt.figure(figsize=(9.2, 4.6))
        top_indices = results["ranking_indices"][:5]
        for i in top_indices:
            alt_scores = [step[i] for step in scores_history]
            plt.plot(w_vals, alt_scores, linewidth=2, label=p_data["alternatives"][i])
        plt.xlabel(f"Bobot {p_data['criteria'][target_idx]}")
        plt.ylabel("Skor Akhir SMART")
        plt.legend(fontsize=8, loc="best")
        plt.grid(True, alpha=0.18)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", transparent=False)
        buf.seek(0)
        plt.close()
        chart_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return render_template("results.html", project=project, data=p_data, res=results, chart=chart_base64)
    except Exception as exc:
        flash(f"Perhitungan gagal: {exc}", "danger")
        return redirect(url_for("view_project", id=id))


@app.route("/project/<int:id>/export")
def export_excel(id):
    project = load_project(id)
    if not project:
        return "Studi kasus tidak ditemukan", 404
    p_data = project.data_json
    df = pd.DataFrame(p_data["performance"], columns=p_data["criteria"])
    df.insert(0, "Alternatif", p_data["alternatives"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Data Alternatif", index=False)
        meta = pd.DataFrame({
            "Kriteria": p_data["criteria"],
            "Tipe": p_data["types"],
            "Bobot": p_data["weights"],
        })
        meta.to_excel(writer, sheet_name="Kriteria", index=False)
    output.seek(0)
    safe_name = project.name.replace(" ", "_")
    return send_file(output, as_attachment=True, download_name=f"SMART_{safe_name}.xlsx")


@app.route("/project/<int:id>/delete")
def delete_project(id):
    with SessionLocal() as db:
        proj = db.query(Project).filter(Project.id == id).first()
        if proj:
            db.delete(proj)
            db.commit()
            flash("Studi kasus berhasil dihapus.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
