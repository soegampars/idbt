# Dataset Ketenagakerjaan

# Daftar Isi

  - [Deskripsi](#deskripsi)
  - [Isi Dataset](#isi-dataset)
    - [1. Pekerja per Provinsi dan 9 Sektor Industri (2010-2014)](#1-pekerja-per-provinsi-dan-9-sektor-industri-2010-2014)
    - [2. Pekerja per Provinsi dan 17 Sektor Industri (2015-2023)](#2-pekerja-per-provinsi-dan-17-sektor-industri-2015-2023)
    - [3. Angkatan Kerja per Kabupaten/Kota dan Tingkat Pendidikan (2011-2020)](#3-angkatan-kerja-per-kabupatenkota-dan-tingkat-pendidikan-2011-2020)
  - [Sumber Data](#sumber-data)
  - [Cara Menggunakan](#cara-menggunakan)
  - [Lisensi](#lisensi)
  - [Kontak](#kontak)
 
## Deskripsi
Halo! Selamat datang di repositori GitHub ini. Di sini, kamu akan menemukan dua dataset menarik tentang jumlah tenaga kerja di berbagai sektor industri dan provinsi di Indonesia. Dataset ini sangat berguna untuk memahami bagaimana tenaga kerja tersebar di berbagai bidang ekonomi dan wilayah di negara kita.

## Isi Dataset

### 1. Pekerja per Provinsi dan 9 Sektor Industri (2010-2014)
- **Nama File**: `bekerja_prov9sektor_2010_2014.xlsx`
- **Periode**: 2010-2014
- **Jumlah Sektor**: 9

| Variabel | Deskripsi |
|----------|-----------|
| `prov_kode` | Kode provinsi |
| `prov_nama` | Nama provinsi |
| `year` | Tahun data |
| `bekerja_agri` | Jumlah pekerja di sektor Pertanian, Kehutanan, Perburuan dan Perikanan |
| `bekerja_mining` | Jumlah pekerja di sektor Pertambangan dan Penggalian |
| `bekerja_manuf` | Jumlah pekerja di sektor Industri Pengolahan |
| `bekerja_util` | Jumlah pekerja di sektor Listrik, Gas dan Air |
| `bekerja_constr` | Jumlah pekerja di sektor Bangunan |
| `bekerja_trade` | Jumlah pekerja di sektor Perdagangan Besar, Eceran, Rumah Makan dan Hotel |
| `bekerja_trans` | Jumlah pekerja di sektor Angkutan, Pergudangan dan Komunikasi |
| `bekerja_finance` | Jumlah pekerja di sektor Keuangan, Asuransi, Usaha Persewaan Bangunan, Tanah dan Jasa Perusahaan |
| `bekerja_services` | Jumlah pekerja di sektor Jasa Kemasyarakatan, Sosial dan Perorangan |
| `bekerja_total` | Total jumlah pekerja |

### 2. Pekerja per Provinsi dan 17 Sektor Industri (2015-2023)
- **Nama File**: `bekerja_prov17sektor_2015_2023.xlsx`
- **Periode**: 2015-2023
- **Jumlah Sektor**: 17

| Variabel | Deskripsi |
|----------|-----------|
| `prov_kode` | Kode provinsi |
| `year` | Tahun data |
| `prov_nama` | Nama provinsi |
| `bekerja_agr` | Jumlah pekerja di sektor Pertanian, Kehutanan, dan Perikanan |
| `bekerja_min` | Jumlah pekerja di sektor Pertambangan dan Penggalian |
| `bekerja_mfg` | Jumlah pekerja di sektor Industri Pengolahan |
| `bekerja_util` | Jumlah pekerja di sektor Pengadaan Listrik, Gas, Uap/Air Panas, dan Udara Dingin |
| `bekerja_waste` | Jumlah pekerja di sektor Pengadaan Air, Treatment Air Limbah, Treatment dan Pemulihan Material Sampah, dan Aktivitas Remediasi |
| `bekerja_cons` | Jumlah pekerja di sektor Konstruksi |
| `bekerja_trade` | Jumlah pekerja di sektor Perdagangan Besar dan Eceran, Reparasi dan Perawatan Mobil dan Sepeda Motor |
| `bekerja_trans` | Jumlah pekerja di sektor Pengangkutan dan Pergudangan |
| `bekerja_hosp` | Jumlah pekerja di sektor Penyediaan Akomodasi dan Penyediaan Makan Minum |
| `bekerja_info` | Jumlah pekerja di sektor Informasi dan Komunikasi |
| `bekerja_fin` | Jumlah pekerja di sektor Aktivitas Keuangan dan Asuransi |
| `bekerja_real` | Jumlah pekerja di sektor Real Estat |
| `bekerja_biz` | Jumlah pekerja di sektor Aktivitas Profesional dan Perusahaan |
| `bekerja_gov` | Jumlah pekerja di sektor Administrasi Pemerintahan, Pertahanan, dan Jaminan Sosial Wajib |
| `bekerja_edu` | Jumlah pekerja di sektor Pendidikan |
| `bekerja_health` | Jumlah pekerja di sektor Aktivitas Kesehatan dan Kegiatan Sosial |
| `bekerja_other` | Jumlah pekerja di sektor Aktivitas Jasa Lainnya |
| `bekerja_total` | Total jumlah pekerja |

### 3. Angkatan Kerja per Kabupaten/Kota dan Tingkat Pendidikan (2011-2020)
- **Nama File**: `lf_dist_educ_2011-2020.csv`
- **Periode**: 2011-2020
- **Cakupan**: Tingkat pendidikan, tingkat kabupaten/kota

| Variabel | Deskripsi |
|----------|-----------|
| `kabkot` | Nama kabupaten/kota (Bahasa Indonesia) |
| `kabkot_kode` | Kode kabupaten/kota (BPS) |
| `prov` | Kode provinsi (BPS) |
| `year` | Tahun observasi |
| `lf_non` | Jumlah angkatan kerja tidak tamat SD |
| `lf_sd` | Jumlah angkatan kerja tamat SD |
| `lf_smp` | Jumlah angkatan kerja tamat SMP |
| `lf_sma` | Jumlah angkatan kerja tamat SMA/SMK |
| `lf_tert` | Jumlah angkatan kerja tamat pendidikan tinggi |
| `lf` | Total angkatan kerja |

## Sumber Data
Badan Pusat Statistik, n.d., "Keadaan Angkatan Kerja".

## Cara Menggunakan
Jangan khawatir jika kamu baru menggunakan GitHub! Berikut langkah-langkah sederhana untuk mengakses data:
1. Klik pada nama file yang ingin kamu unduh (`bekerja_prov9sektor_2010_2014.xlsx` atau `bekerja_prov17sektor_2015_2023.xlsx`).
2. Klik tombol "Download" untuk mengunduh file yang dipilih.
3. Buka file yang diunduh di komputermu menggunakan aplikasi spreadsheet.

## Lisensi
[Tentukan lisensi yang digunakan untuk data ini]

## Kontak
Punya pertanyaan atau butuh informasi lebih lanjut? Jangan ragu untuk menghubungi kami di [masukkan informasi kontak di sini].

Selamat mengeksplorasi data! 😊
