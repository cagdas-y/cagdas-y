#!/usr/bin/env python3
"""
CCTV Güvenlik Tarayıcısı (Örnek Uygulama)

Açıklama:
Bu script, verilen IP kamera listesini alır, RTSP akışlarını varsayılan
kullanıcı/şifre kombinasyonlarıyla test eder, erişim sonuçlarını kaydeder
ve bir CSV dosyasına yazar.

Özellikler:
- Argümanlarla IP listesi ve çıktı dosyası belirleme
- Çoklu iş parçacığıyla hızlı tarama
- Detaylı Türkçe açıklama ve loglama

Gereksinimler:
- opencv-python
- pandas
- tqdm

Kullanım:
    python3 cctv_scanner.py --input cameras.txt --output results.csv --threads 10
"""

import cv2
import pandas as pd
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Varsayılan kullanıcı/şifre kombinasyonları
default_creds = [
    ('admin', 'admin'),
    ('root', 'root'),
    ('user', 'user')
]


def check_camera(ip, port, creds):
    """
    Kamerayı test eder: RTSP akışına bağlanır, erişim durumunu döner.
    """
    for user, pwd in creds:
        rtsp_url = f"rtsp://{user}:{pwd}@{ip}:{port}/"
        cap = cv2.VideoCapture(rtsp_url)
        ok, frame = cap.read()
        cap.release()
        if ok:
            return {
                'ip': ip,
                'port': port,
                'user': user,
                'pwd': pwd,
                'status': 'ERİŞİM BAŞARILI'
            }
    # Hiçbir kombinasyon işe yaramadıysa
    return {
        'ip': ip,
        'port': port,
        'user': None,
        'pwd': None,
        'status': 'ERİŞİM BAŞARISIZ'
    }


def load_camera_list(file_path):
    """
    Kamera listesini yükler. Her satır IP ve port (virgülle ayrılmış).
    """
    cams = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(',')
            ip = parts[0].strip()
            port = int(parts[1].strip()) if len(parts) > 1 else 554
            cams.append((ip, port))
    return cams


def main():
    # Argüman ayarları
    parser = argparse.ArgumentParser(description='CCTV Güvenlik Tarayıcısı')
    parser.add_argument('--input', '-i', required=True, help='Kamera listesi dosyası (IP,port)')
    parser.add_argument('--output', '-o', default='results.csv', help='Sonuç CSV dosyası')
    parser.add_argument('--threads', '-t', type=int, default=5, help='Eş zamanlı iş parçacığı sayısı')
    args = parser.parse_args()

    # Kamera listesini yükle
    cameras = load_camera_list(args.input)
    print(f"Toplam {len(cameras)} kamera yükleniyor...")

    results = []
    # Çoklu iş parçacıklı tarama
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {executor.submit(check_camera, ip, port, default_creds): (ip, port) for ip, port in cameras}
        for future in tqdm(as_completed(futures), total=len(futures), desc='Tarama'):  # ilerleme çubuğu
            res = future.result()
            results.append(res)

    # Sonuçları DataFrame'e yükle ve kaydet
    df = pd.DataFrame(results)
    df.to_csv(args.output, index=False)
    print(f"Tarama tamamlandı, sonuçlar '{args.output}' dosyasına kaydedildi.")


if __name__ == '__main__':
    main()
