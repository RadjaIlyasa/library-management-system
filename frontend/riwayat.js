const API_URL = "http://localhost:5000/api";

// Guard yang sama kayak index.html — halaman ini juga cuma boleh diakses kalau udah login
if (!sessionStorage.getItem("token")) {
  window.location.href = "login.html";
}

async function loadDropdownAnggota() {
  const res = await fetch(`${API_URL}/anggota`);
  const data = await res.json();
  const select = document.querySelector("#pilih-anggota");
  select.innerHTML = data
    .map((a) => `<option value="${a.id_anggota}">${a.nama_anggota}</option>`)
    .join("");

  // Begitu dropdown keisi, langsung tampilin riwayat anggota pertama
  if (data.length > 0) {
    loadRiwayat(data[0].id_anggota, data[0].nama_anggota);
  }
}

async function loadRiwayat(idAnggota, namaAnggota) {
  document.querySelector("#judul-riwayat").textContent = `Riwayat Peminjaman — ${namaAnggota}`;

  const res = await fetch(`${API_URL}/peminjaman/anggota/${idAnggota}`);
  const data = await res.json();

  const tbody = document.querySelector("#tabel-riwayat tbody");
  tbody.innerHTML = "";

  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4">Belum ada riwayat peminjaman</td></tr>`;
    return;
  }

  data.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.judul}</td>
      <td>${r.tanggal_peminjaman}</td>
      <td>${r.tanggal_kembali ?? "-"}</td>
      <td>${r.status}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Setiap kali pilihan dropdown berubah, ambil ulang riwayat sesuai anggota yang dipilih
document.querySelector("#pilih-anggota").addEventListener("change", (e) => {
  const namaTerpilih = e.target.options[e.target.selectedIndex].textContent;
  loadRiwayat(e.target.value, namaTerpilih);
});

loadDropdownAnggota();