const API_URL = "http://localhost:5000/api";

/* =========================================
   BUKU (tambah, tampil, edit, hapus)
========================================= */

let daftarBukuCache = []; // nyimpen data buku terakhir biar bisa difilter tanpa fetch ulang

async function loadBuku() {
  const res = await fetch(`${API_URL}/buku`);
  daftarBukuCache = await res.json();
  renderTabelBuku(daftarBukuCache);
}

function renderTabelBuku(data) {
  const tbody = document.querySelector("#tabel-buku tbody");
  tbody.innerHTML = "";

  data.forEach((buku) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${buku.judul}</td>
      <td>${buku.penulis}</td>
      <td>${buku.nama_kategori ?? "-"}</td>
      <td>${buku.stok}</td>
      <td>
        <button onclick='mulaiEditBuku(${JSON.stringify(buku)})'>Edit</button>
        <button class="btn-hapus" onclick="hapusBuku(${buku.id_buku})">Hapus</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

document.querySelector("#search-buku").addEventListener("input", (e) => {
  const kata = e.target.value.toLowerCase();
  const hasil = daftarBukuCache.filter(
    (b) => b.judul.toLowerCase().includes(kata) || b.penulis.toLowerCase().includes(kata)
  );
  renderTabelBuku(hasil);
});

async function loadKategori() {
  const res = await fetch(`${API_URL}/kategori`);
  const data = await res.json();
  const select = document.querySelector("#id_kategori");
  select.innerHTML = data
    .map((k) => `<option value="${k.id_kategori}">${k.nama_kategori}</option>`)
    .join("");
}

// Isi form dengan data buku yang mau diedit, ganti mode form jadi "edit"
function mulaiEditBuku(buku) {
  document.querySelector("#edit-id-buku").value = buku.id_buku;
  document.querySelector("#judul").value = buku.judul;
  document.querySelector("#penulis").value = buku.penulis;
  document.querySelector("#stok").value = buku.stok;

  document.querySelector("#judul-form-buku").textContent = "Edit Buku";
  document.querySelector("#btn-submit-buku").textContent = "Simpan Perubahan";
  document.querySelector("#btn-batal-edit").style.display = "inline-block";

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Balikin form ke mode "tambah" lagi
function batalEdit() {
  document.querySelector("#form-buku").reset();
  document.querySelector("#edit-id-buku").value = "";
  document.querySelector("#judul-form-buku").textContent = "Tambah Buku";
  document.querySelector("#btn-submit-buku").textContent = "Tambah";
  document.querySelector("#btn-batal-edit").style.display = "none";
}

document.querySelector("#btn-batal-edit").addEventListener("click", batalEdit);

document.querySelector("#form-buku").addEventListener("submit", async (e) => {
  e.preventDefault();

  const editId = document.querySelector("#edit-id-buku").value;
  const body = {
    judul: document.querySelector("#judul").value,
    penulis: document.querySelector("#penulis").value,
    id_kategori: document.querySelector("#id_kategori").value,
    stok: Number(document.querySelector("#stok").value),
  };

  if (editId) {
    // Mode edit -> panggil PUT ke buku yang lagi diedit
    await fetch(`${API_URL}/buku/${editId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    batalEdit();
  } else {
    // Mode tambah -> POST buku baru
    await fetch(`${API_URL}/buku`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    e.target.reset();
  }

  loadBuku();
});

async function hapusBuku(id) {
  if (!confirm("Yakin mau hapus buku ini?")) return;
  await fetch(`${API_URL}/buku/${id}`, { method: "DELETE" });
  loadBuku();
}

/* =========================================
   ANGGOTA (tambah & tampil)
========================================= */

async function loadAnggota() {
  const res = await fetch(`${API_URL}/anggota`);
  const data = await res.json();

  const tbody = document.querySelector("#tabel-anggota tbody");
  tbody.innerHTML = "";
  data.forEach((a) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${a.nama_anggota}</td><td>${a.alamat ?? "-"}</td><td>${a.no_hp ?? "-"}</td>`;
    tbody.appendChild(tr);
  });

  // Dropdown anggota di form peminjaman juga diisi dari data yang sama
  const select = document.querySelector("#pinjam_id_anggota");
  select.innerHTML = data
    .map((a) => `<option value="${a.id_anggota}">${a.nama_anggota}</option>`)
    .join("");
}

document.querySelector("#form-anggota").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    nama_anggota: document.querySelector("#nama_anggota").value,
    alamat: document.querySelector("#alamat").value,
    no_hp: document.querySelector("#no_hp").value,
  };
  await fetch(`${API_URL}/anggota`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  e.target.reset();
  loadAnggota();
});

/* =========================================
   PEMINJAMAN (pinjam, tampil, kembalikan)
========================================= */

// Dropdown buku di form peminjaman, diisi dari data buku yang sama kayak tabel buku
async function loadDropdownBuku() {
  const res = await fetch(`${API_URL}/buku`);
  const data = await res.json();
  const select = document.querySelector("#pinjam_id_buku");
  select.innerHTML = data
    .map((b) => `<option value="${b.id_buku}" ${b.stok === 0 ? "disabled" : ""}>${b.judul} (stok: ${b.stok})</option>`)
    .join("");
  cekStokTombolPinjam();
}

// Nonaktifkan tombol "Pinjamkan" kalau opsi yang lagi kepilih di dropdown stoknya 0
function cekStokTombolPinjam() {
  const select = document.querySelector("#pinjam_id_buku");
  const opsiTerpilih = select.options[select.selectedIndex];
  document.querySelector("#btn-pinjam").disabled = !opsiTerpilih || opsiTerpilih.disabled;
}

document.querySelector("#pinjam_id_buku").addEventListener("change", cekStokTombolPinjam);

async function loadPeminjaman() {
  const res = await fetch(`${API_URL}/peminjaman`);
  const data = await res.json();

  const tbody = document.querySelector("#tabel-peminjaman tbody");
  tbody.innerHTML = "";

  data.forEach((p) => {
    const tr = document.createElement("tr");
    const aksi = p.status === "Dipinjam"
      ? `<button onclick="kembalikanBuku(${p.id_peminjaman})">Kembalikan</button>`
      : "-";
    tr.innerHTML = `
      <td>${p.judul}</td>
      <td>${p.nama_anggota}</td>
      <td>${p.tanggal_peminjaman}</td>
      <td>${p.tanggal_kembali ?? "-"}</td>
      <td>${p.status}</td>
      <td>${aksi}</td>
    `;
    tbody.appendChild(tr);
  });
}

document.querySelector("#form-peminjaman").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    id_buku: document.querySelector("#pinjam_id_buku").value,
    id_anggota: document.querySelector("#pinjam_id_anggota").value,
  };

  const res = await fetch(`${API_URL}/peminjaman`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json();
    alert(err.error || "Gagal meminjamkan buku");
    return;
  }

  // Refresh semua yang berkaitan sama stok buku
  loadBuku();
  loadDropdownBuku();
  loadPeminjaman();
});

async function kembalikanBuku(id) {
  await fetch(`${API_URL}/peminjaman/${id}/kembali`, { method: "PUT" });
  loadBuku();
  loadDropdownBuku();
  loadPeminjaman();
}

/* =========================================
   INISIALISASI: jalan pertama kali halaman dibuka
========================================= */

loadKategori();
loadBuku();
loadAnggota();
loadDropdownBuku();
loadPeminjaman();
