import os
import sys
import time
import subprocess
import platform
import requests
import re
from pathlib import Path
from urllib.parse import urlparse, unquote, parse_qs

class Aria2Downloader:
    def __init__(self):
        self.start_time = None
        self.system = platform.system()
        self.aria2_installed = False
        # CivitAI Token untuk authentication
        self.civitai_token = "3bf797ec7a0b65f197ca426ccb8cf193"
        
    def format_bytes(self, bytes):
        """Format bytes ke human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"
    
    def format_time(self, seconds):
        """Format seconds ke readable time"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            mins = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds / 3600)
            mins = int((seconds % 3600) / 60)
            return f"{hours}h {mins}m"
    
    def check_aria2_installed(self):
        """Check if aria2 is installed"""
        try:
            subprocess.run(['aria2c', '--version'], capture_output=True, check=True)
            print("✅ aria2 sudah terinstall")
            self.aria2_installed = True
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ aria2 belum terinstall")
            self.aria2_installed = False
            return False
    
    def install_aria2(self):
        """Install aria2 berdasarkan OS"""
        if self.aria2_installed:
            return True
            
        print("📦 Menginstall aria2...")
        
        # Installation commands berdasarkan OS
        install_commands = {
            'Linux': [
                "sudo apt update && sudo apt install -y aria2",
                "sudo yum install -y aria2", 
                "sudo dnf install -y aria2",
                "sudo pacman -S --noconfirm aria2",
                "sudo zypper install -y aria2"
            ],
            'Darwin': [  # macOS
                "brew install aria2",
                "/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\" && brew install aria2"
            ],
            'Windows': [
                "winget install aria2.aria2",
                "choco install aria2",
                "scoop install aria2"
            ]
        }
        
        if self.system not in install_commands:
            print(f"❌ OS {self.system} tidak didukung untuk auto-install")
            return False
        
        commands = install_commands[self.system]
        
        for i, cmd in enumerate(commands, 1):
            try:
                print(f"🔄 Mencoba metode {i}/{len(commands)}: {cmd.split()[0]}...")
                
                if self.system == 'Windows':
                    # Untuk Windows, coba PowerShell dulu
                    result = subprocess.run(
                        ['powershell', '-Command', cmd],
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 menit timeout
                    )
                else:
                    # Untuk Linux/macOS
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                
                if result.returncode == 0:
                    print(f"✅ aria2 berhasil diinstall dengan {cmd.split()[0]}!")
                    
                    # Verify installation
                    if self.check_aria2_installed():
                        return True
                
                print(f"⚠️ Metode {i} gagal, mencoba metode berikutnya...")
                
            except subprocess.TimeoutExpired:
                print(f"⏰ Timeout pada metode {i}, mencoba metode berikutnya...")
                continue
            except Exception as e:
                print(f"❌ Error pada metode {i}: {e}")
                continue
        
        # Jika semua metode auto-install gagal
        print("\n❌ Auto-installation gagal. Silakan install aria2 secara manual:")
        self._show_manual_installation()
        return False
    
    def _show_manual_installation(self):
        """Tampilkan instruksi manual installation"""
        print("\n📖 INSTRUKSI MANUAL INSTALLATION:")
        print("="*50)
        
        if self.system == 'Linux':
            print("🐧 LINUX:")
            print("• Ubuntu/Debian: sudo apt install aria2")
            print("• CentOS/RHEL:   sudo yum install aria2") 
            print("• Fedora:        sudo dnf install aria2")
            print("• Arch Linux:    sudo pacman -S aria2")
            print("• openSUSE:      sudo zypper install aria2")
            
        elif self.system == 'Darwin':
            print("🍎 macOS:")
            print("1. Install Homebrew terlebih dahulu:")
            print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            print("2. Install aria2:")
            print("   brew install aria2")
            print("\nAlternatif: Download dari https://github.com/aria2/aria2/releases")
            
        elif self.system == 'Windows':
            print("🪟 WINDOWS:")
            print("1. Chocolatey: choco install aria2")
            print("2. Scoop:      scoop install aria2") 
            print("3. Winget:     winget install aria2.aria2")
            print("4. Manual:     Download dari https://github.com/aria2/aria2/releases")
        
        print("="*50)
    
    def setup_aria2(self):
        """Setup aria2 - check dan install jika perlu"""
        print("🔍 Memeriksa aria2...")
        
        if self.check_aria2_installed():
            return True
        
        # Auto-install
        install_choice = input("\n📥 aria2 belum terinstall. Install otomatis? (y/n): ")
        if install_choice.lower() == 'y':
            return self.install_aria2()
        else:
            print("❌ aria2 diperlukan untuk menjalankan program ini.")
            self._show_manual_installation()
            return False

    def get_comfyui_directory(self):
        """Pilih direktori ComfyUI dari menu"""
        directories = {
            "1": "/root/ComfyUI/models/diffusion_models",
            "2": "/root/ComfyUI/models/loras",
            "3": "/root/ComfyUI/models/vae",
            "4": "/root/ComfyUI/models/checkpoints",
            "5": "/root/ComfyUI/models/controlnet",
            "6": "/root",
            "7": "custom"
        }
        
        print("\n📁 Pilih direktori tujuan:")
        print("   1. Diffusion Models (/root/ComfyUI/models/diffusion_models)")
        print("   2. LoRAs (/root/ComfyUI/models/loras)")
        print("   3. VAE (/root/ComfyUI/models/vae)")
        print("   4. Checkpoints (/root/ComfyUI/models/checkpoints)")
        print("   5. ControlNet (/root/ComfyUI/models/controlnet)")
        print("   6. Root (/root)")
        print("   7. Direktori lain (input manual)")
        
        while True:
            choice = input("\nPilih direktori (1-7): ").strip()
            
            if choice in directories:
                if choice == "7":
                    # Input manual untuk direktori custom
                    custom_dir = input("📝 Masukkan path direktori custom: ").strip()
                    if custom_dir:
                        return custom_dir
                    else:
                        print("❌ Direktori tidak boleh kosong!")
                        continue
                else:
                    return directories[choice]
            else:
                print("❌ Pilihan tidak valid! Masukkan angka 1-7.")

    def is_civitai_url(self, url):
        """Check apakah URL dari CivitAI"""
        return 'civitai.com' in url.lower()

    def get_civitai_filename(self, url):
        """
        Ambil nama file dari CivitAI menggunakan API atau header response
        """
        try:
            print("🔍 Mendeteksi nama file dari CivitAI...")
            
            # Method 1: HEAD request untuk ambil Content-Disposition
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/octet-stream, */*',
                'Referer': 'https://civitai.com/'
            }
            
            # Pastikan URL sudah memiliki token
            prepared_url = self.prepare_civitai_url(url)
            
            response = requests.head(prepared_url, headers=headers, allow_redirects=True, timeout=15)
            
            # Cek Content-Disposition header
            if 'Content-Disposition' in response.headers:
                content_disp = response.headers['Content-Disposition']
                filename_match = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';\r\n]+)', content_disp)
                if filename_match:
                    filename = unquote(filename_match.group(1))
                    print(f"✅ Nama file terdeteksi dari header: {filename}")
                    return filename
            
            # Method 2: Coba ambil dari API CivitAI jika ada model ID
            model_id = self.extract_civitai_model_id(url)
            if model_id:
                api_filename = self.get_filename_from_civitai_api(model_id)
                if api_filename:
                    print(f"✅ Nama file terdeteksi dari API: {api_filename}")
                    return api_filename
            
            # Method 3: Parse dari URL
            parsed_url = urlparse(url)
            url_filename = unquote(os.path.basename(parsed_url.path))
            if url_filename and '.' in url_filename:
                print(f"✅ Nama file terdeteksi dari URL: {url_filename}")
                return url_filename
                
            print("⚠️ Nama file tidak terdeteksi, menggunakan fallback")
            return None
            
        except Exception as e:
            print(f"⚠️ Error mendeteksi nama file: {e}")
            return None

    def extract_civitai_model_id(self, url):
        """Extract model ID dari URL CivitAI"""
        try:
            # Pattern untuk berbagai format URL CivitAI
            patterns = [
                r'civitai\.com/models/(\d+)',
                r'civitai\.com/api/download/models/(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            return None
        except:
            return None

    def get_filename_from_civitai_api(self, model_id):
        """Ambil filename dari CivitAI API"""
        try:
            api_url = f"https://civitai.com/api/v1/models/{model_id}"
            headers = {}
            if self.civitai_token:
                headers['Authorization'] = f'Bearer {self.civitai_token}'
                
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Ambil filename dari model version pertama
                if 'modelVersions' in data and data['modelVersions']:
                    files = data['modelVersions'][0].get('files', [])
                    if files:
                        return files[0].get('name')
            return None
        except:
            return None

    def prepare_civitai_url(self, url):
        """Prepare URL CivitAI dengan token jika diperlukan"""
        if not self.is_civitai_url(url):
            return url
        
        print("🎨 URL CivitAI terdeteksi, memproses authentication...")
        
        # Jika token sudah ada di URL, gunakan apa adanya
        if 'token=' in url:
            print("✅ Token sudah ada di URL")
            return url
        
        # Tambahkan token ke URL jika belum ada
        if self.civitai_token:
            separator = '&' if '?' in url else '?'
            url_with_token = f"{url}{separator}token={self.civitai_token}"
            print("✅ Token authentication ditambahkan ke URL")
            return url_with_token
        
        return url
    
    def download_with_aria2(self, url, filepath):
        """Download menggunakan aria2 dengan konfigurasi optimal"""
        if not self.aria2_installed:
            print("❌ aria2 tidak tersedia!")
            return False, "aria2 tidak terinstall"
        
        try:
            print("🚀 Memulai download dengan aria2 (kecepatan maksimum)...")
            
            # Get directory dan filename
            directory = os.path.dirname(filepath)
            filename = os.path.basename(filepath)
            
            # Pastikan direktori ada
            Path(directory).mkdir(parents=True, exist_ok=True)
            
            # Prepare URL untuk CivitAI
            prepared_url = self.prepare_civitai_url(url)
            
            # Headers untuk CivitAI (gunakan User-Agent yang lebih baik)
            headers = []
            if self.is_civitai_url(url):
                headers = [
                    '--header=User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    '--header=Accept: application/octet-stream, */*',
                    '--header=Referer: https://civitai.com/'
                ]
            
            # Konfigurasi aria2 untuk kecepatan maksimum
            cmd = [
                'aria2c',
                '--file-allocation=none',           # Alokasi file cepat
                '--max-connection-per-server=4',    # Kurangi koneksi untuk CivitAI
                '--split=4',                        # Split lebih kecil
                '--min-split-size=1M',              # Min size per split
                '--max-concurrent-downloads=1',     # Satu download untuk stability
                '--continue=true',                  # Resume support
                '--allow-overwrite=true',           # Allow overwrite
                '--auto-file-renaming=false',       # Tidak auto rename
                '--disable-ipv6=true',              # Matikan IPv6 untuk speed
                '--console-log-level=notice',       # Log level
                '--summary-interval=1',             # Update tiap 1 detik
                '--human-readable=true',            # Human readable sizes
                '--show-console-readout=true',      # Show progress
                '--check-certificate=false',        # Skip SSL check untuk speed
                '--timeout=60',                     # Connection timeout lebih lama
                '--retry-wait=5',                   # Retry delay lebih lama
                '--max-tries=10',                   # Max retry lebih banyak
                '--follow-metalink=mem',            # Follow metalink
                '--metalink-enable-unique-protocol=false',
                '--dir=' + directory,               # Output directory  
                '--out=' + filename,                # Output filename
            ] + headers + [prepared_url]            # Add headers dan URL
            
            # Jalankan aria2c dengan real-time output
            print(f"📁 Menyimpan ke: {filepath}")
            print("🔄 Progress download:\n")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Parse dan display output real-time
            for line in process.stdout:
                line = line.strip()
                if line:
                    # Progress line dengan download info
                    if '[' in line and ']' in line and ('DL:' in line or 'CN:' in line):
                        # Progress bar aria2
                        sys.stdout.write('\r' + line)
                        sys.stdout.flush()
                    elif 'Download complete' in line:
                        print('\n✅ ' + line)
                    elif 'STATUS' in line and 'OK' in line:
                        print('\n✅ Download selesai!')
                    elif 'ERROR' in line or 'WARN' in line:
                        print('\n⚠️  ' + line)
                    elif line.startswith('[') and ('file(s) downloaded' in line):
                        print('\n' + line)
            
            process.wait()
            
            if process.returncode == 0:
                return True, "Download berhasil dengan aria2!"
            else:
                return False, f"aria2 gagal dengan kode: {process.returncode}"
                
        except Exception as e:
            return False, f"Error aria2: {str(e)}"
    
    def download_file(self, url, directory=".", filename=None):
        """Main download function"""
        
        # Auto-generate filename jika tidak ada
        if filename is None:
            # Untuk CivitAI, coba deteksi nama file otomatis
            if self.is_civitai_url(url):
                detected_filename = self.get_civitai_filename(url)
                if detected_filename:
                    filename = detected_filename
                else:
                    # Fallback untuk CivitAI
                    filename = f"civitai_model_{int(time.time())}.safetensors"
            else:
                # Untuk URL lain
                parsed_url = urlparse(url)
                filename = unquote(os.path.basename(parsed_url.path))
                if not filename:
                    filename = f"download_{int(time.time())}"
            
            print(f"📝 Menggunakan filename: {filename}")
        
        # Full path untuk file
        filepath = os.path.join(directory, filename)
        
        # Check existing file
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"⚠️  File {filename} sudah ada ({self.format_bytes(file_size)})")
            overwrite = input("Timpa file? (y/n): ")
            if overwrite.lower() != 'y':
                print("❌ Download dibatalkan.")
                return False
        
        print(f"\n📥 DOWNLOAD INFO:")
        print(f"🔗 URL: {url}")
        print(f"📁 Direktori: {os.path.abspath(directory)}")
        print(f"📄 Filename: {filename}")
        if self.is_civitai_url(url):
            print(f"🎨 Platform: CivitAI (dengan authentication)")
        print("-" * 60)
        
        # Download dengan aria2
        self.start_time = time.time()
        success, message = self.download_with_aria2(url, filepath)
        end_time = time.time()
        
        if success and os.path.exists(filepath):
            # Statistik download
            file_size = os.path.getsize(filepath)
            download_time = end_time - self.start_time
            
            print(f"\n🎉 DOWNLOAD BERHASIL!")
            print(f"📊 Ukuran file: {self.format_bytes(file_size)}")
            print(f"⏱️  Waktu download: {self.format_time(download_time)}")
            print(f"🚄 Kecepatan rata-rata: {self.format_bytes(file_size/max(download_time, 0.1))}/s")
            print(f"📍 Lokasi file: {os.path.abspath(filepath)}")
            return True
        else:
            print(f"\n❌ DOWNLOAD GAGAL: {message}")
            # Cleanup partial file
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print("🗑️  File tidak lengkap telah dihapus")
                except:
                    pass
            return False

# =============================================
# MAIN PROGRAM - Interactive Download
# =============================================

def main():
    """Main function untuk interactive download"""
    
    print("=" * 70)
    print("    🚀 ARIA2 HIGH-SPEED DOWNLOADER 🚀")  
    print("    Optimized untuk CivitAI & kecepatan maksimum")
    print("=" * 70)
    
    # Setup aria2
    downloader = Aria2Downloader()
    if not downloader.setup_aria2():
        print("❌ Setup gagal. Program dihentikan.")
        return
    
    download_count = 0
    
    try:
        while True:
            print(f"\n📥 DOWNLOAD #{download_count + 1}")
            print("-" * 40)
            
            # Input URL
            url = input("🔗 Masukkan URL download (CivitAI/others): ").strip()
            if not url:
                print("❌ URL tidak boleh kosong!")
                continue
            
            # Pilih directory dari menu ComfyUI
            directory = downloader.get_comfyui_directory()
            
            # Input filename (optional, akan auto-detect untuk CivitAI)
            if downloader.is_civitai_url(url):
                print("🎨 CivitAI URL terdeteksi - nama file akan dideteksi otomatis")
                filename = input("📝 Nama file custom (Enter=auto-detect): ").strip()
                if not filename:
                    filename = None
            else:
                filename = input("📝 Nama file (Enter=auto): ").strip()
                if not filename:
                    filename = None
            
            print("\n🚀 Memulai download...")
            
            # Download file
            success = downloader.download_file(url, directory, filename)
            
            if success:
                download_count += 1
                print(f"\n📊 Total download berhasil: {download_count}")
            
            # Continue?
            print("\n" + "="*50)
            continue_choice = input("🔄 Download file lain? (y/n, Enter=yes): ").strip().lower()
            if continue_choice in ['n', 'no', 'tidak']:
                break
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Program dihentikan oleh user.")
        print(f"📊 Total download berhasil: {download_count}")
    
    print("👋 Terima kasih telah menggunakan Aria2 Downloader!")

# =============================================
# QUICK DOWNLOAD FUNCTIONS
# =============================================

def quick_download(url, directory="./downloads", filename=None):
    """
    Quick download function untuk penggunaan langsung
    
    Args:
        url: URL untuk didownload
        directory: Direktori tujuan (default: ./downloads)
        filename: Nama file (default: auto dari URL)
    
    Returns:
        bool: True jika berhasil, False jika gagal
    """
    downloader = Aria2Downloader()
    
    if not downloader.setup_aria2():
        return False
    
    return downloader.download_file(url, directory, filename)

def batch_download(urls, directory="./downloads"):
    """
    Download multiple files sekaligus
    
    Args:
        urls: List URLs atau dict {url: filename}
        directory: Direktori tujuan
    
    Returns:
        dict: {'success': count, 'failed': count, 'total': count}
    """
    downloader = Aria2Downloader()
    
    if not downloader.setup_aria2():
        return {'success': 0, 'failed': 0, 'total': 0}
    
    # Convert list ke dict jika perlu
    if isinstance(urls, list):
        url_dict = {url: None for url in urls}
    else:
        url_dict = urls
    
    total = len(url_dict)
    success_count = 0
    failed_count = 0
    
    print(f"📦 BATCH DOWNLOAD: {total} file(s)")
    print("=" * 60)
    
    for i, (url, filename) in enumerate(url_dict.items(), 1):
        print(f"\n[{i}/{total}] Processing: {filename or 'auto-filename'}")
        
        if downloader.download_file(url, directory, filename):
            success_count += 1
        else:
            failed_count += 1
        
        print("-" * 60)
    
    result = {
        'success': success_count,
        'failed': failed_count, 
        'total': total
    }
    
    print(f"\n📊 BATCH SELESAI:")
    print(f"✅ Berhasil: {success_count}")
    print(f"❌ Gagal: {failed_count}")
    print(f"📁 Total: {total}")
    
    return result

# =============================================
# RUN PROGRAM
# =============================================

if __name__ == "__main__":
    # Mode 1: Interactive (default)
    main()
    
    # Mode 2: Quick download single file
    # quick_download("https://civitai.com/api/download/models/123456", "/root/ComfyUI/models/loras", "custom_lora.safetensors")
    
    # Mode 3: Batch download  
    # batch_download([
    #     "https://civitai.com/api/download/models/123456",
    #     "https://example.com/file2.safetensors"  
    # ], "/root/ComfyUI/models/checkpoints")