from pytubefix import YouTube
import os
import subprocess
import yt_dlp
import glob
import shutil
import requests
import re

#func for downloading video from YouTube
def Download_Video_Youtube(url):
    yt = YouTube(url)
    video_stream = yt.streams.filter(adaptive=True, only_video=True, file_extension='mp4').order_by('resolution').desc().first()
    audio_stream = yt.streams.filter(adaptive=True, only_audio=True, file_extension='mp4').order_by('abr').desc().first()
    video_path = video_stream.download(filename="video_temp.mp4")
    audio_path = audio_stream.download(filename="audio_temp.mp4")
    output_filename = yt.title.replace(' ', '_').replace('/', '_') + ".mp4"
    subprocess.run([
        'ffmpeg', '-y',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental',
        output_filename
    ])
    os.remove(video_path)
    os.remove(audio_path)
    return output_filename

#func for downloading music from SoundCloud
def Download_Music_SoundCloud(url):
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
        filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
    return filename

#func for downloading music from Spotify
def Download_Music_Spotify(url):
    temp_folder = "spotify_download_temp"
    os.makedirs(temp_folder, exist_ok=True)
    subprocess.run([
        'spotdl', url, '--output', temp_folder
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    mp3_files = glob.glob(os.path.join(temp_folder, '*.mp3'))
    if mp3_files:
        filename = mp3_files[0]
        final_filename = os.path.basename(filename)
        shutil.move(filename, final_filename)
        shutil.rmtree(temp_folder)
        return final_filename
    else:
        shutil.rmtree(temp_folder)
        return None

#func for downloading video from TikTok
def Download_Video_TikTok(url):
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': '%(title)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return filename


#func for downloading video from Pinterest
def Download_Video_Pinterest(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
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
        else:
            return None
    else:
        return None
