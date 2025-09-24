# Smart package installation - install hanya jika belum ada
def install_packages():
    """Install packages yang diperlukan jika belum ada"""
    required_packages = {
        'hf_transfer': 'hf_transfer',
        'huggingface_hub': 'huggingface_hub', 
        'tqdm': 'tqdm',
        'requests': 'requests'
    }
    
    missing_packages = []
    
    print("🔍 Memeriksa dependencies...")
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name} sudah terinstall")
        except ImportError:
            print(f"❌ {package_name} belum terinstall")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n📦 Menginstall {len(missing_packages)} package yang missing...")
        import subprocess
        import sys
        
        for package in missing_packages:
            print(f"⏳ Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "uv","pip", "install", package, "-q"])
                print(f"✅ {package} berhasil diinstall")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error installing {package}: {e}")
                return False
    else:
        print("🎉 Semua dependencies sudah tersedia!")
    
    return True

# Install packages jika diperlukan
if not install_packages():
    print("❌ Gagal menginstall dependencies. Program dihentikan.")
    exit(1)

import os
import re
from huggingface_hub import hf_hub_download, login
from datetime import datetime
import time
from urllib.parse import urlparse
import requests

# Konfigurasi akun Hugging Face
HF_TOKEN = "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"
HF_USERNAME = "jekverse"

def setup_hf_transfer():
    """Setup hf_transfer dan login"""
    print("🚀 Mengaktifkan hf_transfer untuk kecepatan maksimal...")
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
    
    try:
        print(f"🔐 Login sebagai: {HF_USERNAME}")
        login(token=HF_TOKEN, add_to_git_credential=True)
        print("✅ Login berhasil!")
    except Exception as e:
        print(f"⚠️  Warning login: {e}")
        print("🔄 Melanjutkan tanpa authentication...")

def log_message(message, level="INFO"):
    """Log pesan dengan timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def parse_hf_url(url):
    """Parse URL Hugging Face untuk extract repo_id dan filename"""
    # Pattern: https://huggingface.co/{repo_id}/resolve/main/{filename}
    pattern = r'https://huggingface\.co/([^/]+/[^/]+)/resolve/main/(.+)'
    match = re.match(pattern, url)
    
    if match:
        repo_id = match.group(1)
        filename = match.group(2)
        return repo_id, filename
    else:
        raise ValueError("URL format tidak valid. Gunakan format: https://huggingface.co/USER/REPO/resolve/main/PATH")

def get_comfyui_directory():
    """Pilih direktori ComfyUI dari menu"""
    directories = {
        "1": "/root/ComfyUI/models/diffusion_models",
        "2": "/root/ComfyUI/models/text_encoders", 
        "3": "/root/ComfyUI/models/loras",
        "4": "/root/ComfyUI/models/vae",
        "5": "/root/ComfyUI/models/clip",
        "6": "/root/ComfyUI/models/clip_vision",
        "7": "/root/ComfyUI/models/checkpoints",
        "8": "/root/ComfyUI/models/audio_encoders",
        "9": "/root/ComfyUI/models/upscale_models",
        "10": "/root/ComfyUI/models/controlnet",
        "11": "custom"
    }
    
    print("\n📁 Pilih direktori tujuan:")
    print("   1. Diffusion Models (/root/ComfyUI/models/diffusion_models)")
    print("   2. Text Encoders (/root/ComfyUI/models/text_encoders)")
    print("   3. LoRAs (/root/ComfyUI/models/loras)")
    print("   4. VAE (/root/ComfyUI/models/vae)")
    print("   5. CLIP (/root/ComfyUI/models/clip)")
    print("   6. CLIP Vision (/root/ComfyUI/models/clip_vision)")
    print("   7. Checkpoints (/root/ComfyUI/models/checkpoints)")
    print("   8. Audio Encoders (/root/ComfyUI/models/audio_encoders)")
    print("   9. Upscale Models (/root/ComfyUI/models/upscale_models)")
    print("   10. ControlNet (/root/ComfyUI/models/controlnet)")
    print("   11. Direktori lain (input manual)")
    
    while True:
        choice = input("\nPilih direktori (1-11): ").strip()
        
        if choice in directories:
            if choice == "11":
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
            print("❌ Pilihan tidak valid! Masukkan angka 1-11.")

def get_user_input():
    """Ambil input URL dan direktori dari user"""
    print("\n" + "="*70)
    print("📥 HUGGING FACE DIRECT URL DOWNLOADER")
    print("="*70)
    
    # Input direct URL
    print("📝 Contoh URL:")
    print("   https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/model.safetensors")
    
    url = input("\n🔗 Masukkan direct URL Hugging Face: ").strip()
    if not url:
        return None, None
    
    # Pilih direktori dari menu
    local_dir = get_comfyui_directory()
    
    return url, local_dir

def download_from_url(url, local_dir):
    """Download model dari direct URL dengan hf_transfer (mode flat)"""
    try:
        # Parse URL untuk mendapatkan repo_id dan filename
        repo_id, filename = parse_hf_url(url)
        
        # Ekstrak nama file untuk display
        file_name = os.path.basename(filename)
        
        # Pastikan direktori ada
        os.makedirs(local_dir, exist_ok=True)
        
        log_message(f"📥 Parsing URL berhasil!")
        log_message(f"🏷️  Repo: {repo_id}")
        log_message(f"📄 File: {file_name}")
        log_message(f"📁 Tujuan: {local_dir}")
        
        start_time = time.time()
        
        # Download dengan hf_transfer (mode flat - langsung ke direktori tujuan)
        log_message("🚀 Memulai download dengan hf_transfer...")
        
        # Download ke cache dulu, kemudian move ke lokasi yang diinginkan
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            token=HF_TOKEN,
            resume_download=True
        )
        
        # Pindah file ke direktori yang diinginkan dengan nama flat
        import shutil
        final_filename = os.path.basename(filename)  # Ambil nama file saja
        final_path = os.path.join(local_dir, final_filename)
        
        # Pastikan direktori tujuan ada
        os.makedirs(local_dir, exist_ok=True)
        
        # Copy file ke lokasi final
        shutil.copy2(downloaded_path, final_path)
        downloaded_path = final_path
        
        log_message(f"📁 File disimpan dengan struktur flat: {final_filename}")
        
        end_time = time.time()
        download_time = end_time - start_time
        
        # Verifikasi dan log hasil
        if os.path.exists(downloaded_path):
            file_size = os.path.getsize(downloaded_path)
            file_size_gb = file_size / (1024**3)
            speed_mbps = (file_size / (1024**2)) / max(download_time, 0.1)
            
            log_message("🎉 DOWNLOAD BERHASIL!", "SUCCESS")
            log_message(f"📍 Lokasi: {downloaded_path}")
            log_message(f"📏 Ukuran: {file_size_gb:.2f} GB")
            log_message(f"⏱️  Waktu: {download_time:.1f} detik")
            log_message(f"🚄 Kecepatan: {speed_mbps:.1f} MB/s")
            
            return True
        else:
            log_message("❌ File tidak ditemukan setelah download", "ERROR")
            return False
            
    except ValueError as e:
        log_message(f"❌ URL Error: {str(e)}", "ERROR")
        return False
    except Exception as e:
        log_message(f"❌ Download Error: {str(e)}", "ERROR")
        return False

def main():
    """Main loop untuk download interaktif"""
    # Setup awal
    setup_hf_transfer()
    
    download_count = 0
    total_size = 0
    
    print("\n🎯 Direct URL Downloader siap! Tekan Ctrl+C untuk keluar.")
    
    try:
        while True:
            # Ambil input user
            url, local_dir = get_user_input()
            
            # Cek jika user ingin keluar (input kosong)
            if not url:
                print("❌ URL tidak boleh kosong. Coba lagi...")
                continue
            
            # Download model (selalu mode flat)
            success = download_from_url(url, local_dir)
            
            if success:
                download_count += 1
                log_message(f"📊 Total file berhasil: {download_count}")
            
            # Tanya apakah ingin melanjutkan
            print("\n" + "-"*50)
            continue_choice = input("🔄 Download file lain? (y/n, Enter=yes): ").strip().lower()
            if continue_choice in ['n', 'no', 'tidak']:
                break
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Download dihentikan oleh user.")
        log_message(f"Selesai! Total download berhasil: {download_count}")
    except Exception as e:
        log_message(f"Error tidak terduga: {str(e)}", "ERROR")

# Jalankan program
if __name__ == "__main__":
    main()