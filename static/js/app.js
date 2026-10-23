function confirmDelete(message) {
  return window.confirm(message || 'Hapus data ini?');
}

function handleWeightMethodChange() {
  const method = document.getElementById('weightMethodSelect');
  if (!method) return;
  const inputs = document.getElementsByName('weights[]');
  for (let i = 0; i < inputs.length; i++) {
    if (method.value === 'equal') {
      inputs[i].value = (100 / inputs.length).toFixed(2);
      inputs[i].readOnly = true;
    } else if (method.value === 'roc') {
      inputs[i].readOnly = false;
      inputs[i].min = '1';
      inputs[i].max = inputs.length.toString();
      if (!inputs[i].value || Number(inputs[i].value) < 1) inputs[i].value = (i + 1).toString();
    } else {
      inputs[i].readOnly = false;
      inputs[i].min = '0';
      inputs[i].max = '';
    }
  }
}

function addCriterion() {
  const headerRow = document.getElementById('headerRow');
  const actionHeader = document.getElementById('actionHeader');
  if (!headerRow || !actionHeader) return;
  const index = headerRow.cells.length - 1;
  const newTh = document.createElement('th');
  newTh.className = 'criterion-box';
  newTh.innerHTML = `
    <div class="d-flex justify-content-between align-items-center mb-2"><span class="criterion-code">C${index}</span><button type="button" class="btn btn-sm btn-link text-danger p-0" onclick="deleteCriterion(this)">Hapus</button></div>
    <input type="text" name="criteria[]" value="Kriteria Baru" class="form-control form-control-sm mb-2" required>
    <select name="types[]" class="form-select form-select-sm mb-2"><option value="benefit">Benefit</option><option value="cost">Cost</option></select>
    <input type="number" name="weights[]" value="10" step="any" class="form-control form-control-sm" required>
  `;
  headerRow.insertBefore(newTh, actionHeader);
  document.querySelectorAll('#matrixBody tr').forEach(row => {
    const td = document.createElement('td');
    td.innerHTML = '<input type="number" name="perf[]" value="0" step="any" class="form-control form-control-sm text-end" required>';
    row.insertBefore(td, row.cells[row.cells.length - 1]);
  });
  handleWeightMethodChange();
}

function addAlternative() {
  const tbody = document.getElementById('matrixBody');
  const headerRow = document.getElementById('headerRow');
  if (!tbody || !headerRow) return;
  const criteriaCount = headerRow.cells.length - 2;
  const row = document.createElement('tr');
  let html = '<td class="alt-cell"><input type="text" name="alternatives[]" value="Alternatif Baru" class="form-control form-control-sm" required></td>';
  for (let i = 0; i < criteriaCount; i++) html += '<td><input type="number" name="perf[]" value="0" step="any" class="form-control form-control-sm text-end" required></td>';
  html += '<td class="text-center"><button type="button" class="btn btn-sm btn-outline-danger" onclick="deleteAlternative(this)">Hapus</button></td>';
  row.innerHTML = html;
  tbody.appendChild(row);
}

function deleteCriterion(btn) {
  const headerRow = document.getElementById('headerRow');
  if (headerRow.cells.length <= 4) return alert('Minimal dua kriteria harus dipertahankan.');
  if (!confirm('Hapus kriteria ini beserta seluruh nilainya?')) return;
  const th = btn.closest('th');
  const index = th.cellIndex;
  th.remove();
  document.querySelectorAll('#matrixBody tr').forEach(row => row.cells[index] && row.cells[index].remove());
  handleWeightMethodChange();
}

function deleteAlternative(btn) {
  const tbody = document.getElementById('matrixBody');
  if (tbody.rows.length <= 2) return alert('Minimal dua alternatif harus dipertahankan.');
  if (confirm('Hapus alternatif ini?')) btn.closest('tr').remove();
}

document.addEventListener('DOMContentLoaded', handleWeightMethodChange);
