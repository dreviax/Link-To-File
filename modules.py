import os
import subprocess
import yt_dlp
import glob
import shutil
import requests
import re
from pytubefix import YouTube

# Получение реального разрешения и длительности видео
def get_video_info(path):
    try:
        output = subprocess.check_output([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            path
        ]).decode().splitlines()
        width = int(output[0])
        height = int(output[1])
        duration = int(float(output[2]))
        return width, height, duration
    except Exception:
        return 720, 1280, 0  # значение по умолчанию

# Сжатие видео под целевой размер
def compress_video(input_path, target_size_mb=50):
    output_path = f"compressed_{os.path.basename(input_path)}"
    try:
        duration = float(subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', input_path
        ]))
        target_bitrate = f"{int((target_size_mb * 8000) / duration)}k"
    except Exception:
        target_bitrate = "1000k"

    subprocess.run([
        'ffmpeg', '-y', '-i', input_path,
        '-c:v', 'libx264', '-preset', 'fast',
        '-b:v', target_bitrate, '-maxrate', target_bitrate,
        '-bufsize', target_bitrate,
        '-vf', 'scale=720:-2',
        '-movflags', '+faststart',
        '-c:a', 'aac', '-b:a', '128k',
        '-f', 'mp4', output_path
    ], check=True)

    return output_path

# Загрузка видео с YouTube
def Download_Video_Youtube(url):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4', resolution='720p').first()
        if not stream:
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if not stream:
            raise Exception("Нет доступных потоков")

        temp_file = stream.download(filename=f"temp_{yt.video_id}.mp4")

        optimized_file = f"yt_{yt.video_id}.mp4"
        subprocess.run([
            'ffmpeg', '-y', '-i', temp_file,
            '-c', 'copy',
            '-movflags', '+faststart',
            optimized_file
        ], check=True)
        os.remove(temp_file)

        file_size = os.path.getsize(optimized_file) / (1024 * 1024)
        if file_size > 50:
            compressed_file = compress_video(optimized_file)
            os.remove(optimized_file)
            width, height, duration = get_video_info(compressed_file)
            return compressed_file, width, height, duration

        width, height, duration = get_video_info(optimized_file)
        return optimized_file, width, height, duration

    except Exception as e:
        raise Exception(f"Ошибка загрузки YouTube: {str(e)}")

# Загрузка аудио с SoundCloud
def Download_Music_SoundCloud(url):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = os.path.splitext(ydl.prepare_filename(info))[0] + '.mp3'
            return filename if os.path.exists(filename) else None
    except Exception as e:
        raise Exception(f"SoundCloud: {str(e)}")



# Загрузка аудио с Spotify
def Download_Music_Spotify(url):
    temp_folder = "spotify_download_temp"
    os.makedirs(temp_folder, exist_ok=True)
    subprocess.run([
        'spotdl', url, '--output', temp_folder
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    mp3_files = glob.glob(os.path.join(temp_folder, '*.mp3'))
    if mp3_files:
        final_filename = os.path.basename(mp3_files[0])
        shutil.move(mp3_files[0], final_filename)
        shutil.rmtree(temp_folder)
        return final_filename
    shutil.rmtree(temp_folder)
    return None

# Загрузка видео с TikTok
def Download_Video_TikTok(url):
    try:
        ydl_opts = {
            'format': 'mp4',
            'outtmpl': '%(id)s_tiktok_raw.%(ext)s',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            raw_file = ydl.prepare_filename(info)

        # Прогон через ffmpeg для faststart и оптимизации
        optimized_file = f"tiktok_{info['id']}.mp4"
        subprocess.run([
            'ffmpeg', '-y', '-i', raw_file,
            '-c', 'copy',
            '-movflags', '+faststart',
            optimized_file
        ], check=True)
        os.remove(raw_file)

        # Сжатие при необходимости
        file_size = os.path.getsize(optimized_file) / (1024 * 1024)
        if file_size > 50:
            compressed = compress_video(optimized_file)
            os.remove(optimized_file)
            width, height, duration = get_video_info(compressed)
            return compressed, width, height, duration

        width, height, duration = get_video_info(optimized_file)
        return optimized_file, width, height, duration

    except Exception as e:
        raise Exception(f"Ошибка загрузки TikTok: {str(e)}")

# Загрузка видео с Pinterest
def Download_Video_Pinterest(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    matches = re.findall(r'(https://[^"]+\.mp4)', response.text)
    if matches:
        video_url = matches[0]
        video_response = requests.get(video_url, stream=True)
        if video_response.status_code == 200:
            filename = "pinterest_video.mp4"
            with open(filename, 'wb') as f:
                for chunk in video_response.iter_content(1024):
                    f.write(chunk)
            return filename
    return None

