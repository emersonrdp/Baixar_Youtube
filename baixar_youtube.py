from pytubefix import YouTube, Playlist
from pytubefix.cli import on_progress
from pathlib import Path
import os
import shutil
import subprocess
import unicodedata
import re

from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from mutagen.mp4 import MP4, MP4Tags
from mutagen import File

# Pastas de saída
destino_video = Path("pasta_video")
destino_audio = Path("pasta_audio")
destino_video.mkdir(exist_ok=True)
destino_audio.mkdir(exist_ok=True)


# util: sanitizar nomes (para Windows)
def sanitize_path_name(name: str, replacement: str = "_", max_length: int = 200) -> str:
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, name)
    name = re.sub(r"\s+", " ", name).strip().strip(". ")
    name = name.replace(" ", replacement)
    if len(name) > max_length:
        name = name[:max_length].rstrip(". ")
    return name or "item"


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def convert_to_mp3(input_path: Path, output_path: Path) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vn",
        "-ab", "192k",
        "-ar", "44100",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# tagging helpers
def tag_mp3(filepath: Path, title: str, artist: str, album: str, track: int = None, total: int = None):
    try:
        audio = EasyID3(str(filepath))
    except ID3NoHeaderError:
        audiofile = File(str(filepath), easy=True)
        if audiofile is None:
            raise RuntimeError("Mutagen não conseguiu abrir o arquivo para escrever ID3.")
        if audiofile.tags is None:
            audiofile.add_tags()
        audio = EasyID3(str(filepath))

    audio["title"] = title
    audio["artist"] = artist
    audio["album"] = album
    if track is not None:
        audio["tracknumber"] = f"{track}/{total}" if total else str(track)
    audio.save(str(filepath))


def tag_m4a(filepath: Path, title: str, artist: str, album: str, track: int = None, total: int = None):
    mp4file = MP4(str(filepath))
    if mp4file.tags is None:
        mp4file.tags = MP4Tags()
    tags = mp4file.tags
    tags["\xa9nam"] = title
    tags["\xa9ART"] = artist
    tags["\xa9alb"] = album
    if track is not None:
        tags["trkn"] = [(track, total if total else 0)]
    mp4file.save()


# Função para baixar áudio em MP3 com tags (melhorada)
def baixar_mp3(yt, destino, prefixo="", faixa=None, total_faixas=None):
    audio_stream = yt.streams.filter(only_audio=True).first()
    if audio_stream is None:
        print("Nenhum stream de áudio disponível para:", yt.watch_url if hasattr(yt, "watch_url") else yt.title)
        return

    arquivo_baixado = audio_stream.download(output_path=str(destino), filename_prefix=prefixo)
    caminho = Path(arquivo_baixado)
    # renomeia conteúdo para nome sanitizado (mantendo extensão)
    novo_nome = destino / (sanitize_path_name(f"{prefixo}{yt.title}") + caminho.suffix)
    if caminho != novo_nome:
        # evita sobrescrever
        if novo_nome.exists():
            # adiciona sufixo incremental
            i = 1
            base = novo_nome.stem
            while novo_nome.exists():
                novo_nome = destino / f"{base}_{i}{caminho.suffix}"
                i += 1
        caminho.rename(novo_nome)
        caminho = novo_nome

    ext = caminho.suffix.lower()
    titulo = yt.title
    artista = getattr(yt, "author", "") or ""
    album = "YouTube Playlist"

    # Caso arquivo já seja mp3: grava ID3
    if ext == ".mp3":
        try:
            tag_mp3(caminho, titulo, artista, album, faixa, total_faixas)
            print(f"Áudio salvo em: {caminho}")
            return
        except Exception as e:
            print("Erro ao gravar ID3 no mp3:", e)

    # Se ffmpeg disponível, converte para mp3 e grava ID3 (preferencial)
    if ffmpeg_available():
        mp3_path = caminho.with_suffix(".mp3")
        try:
            convert_to_mp3(caminho, mp3_path)
            try:
                caminho.unlink()  # remove original convertido
            except Exception:
                pass
            tag_mp3(mp3_path, titulo, artista, album, faixa, total_faixas)
            print(f"Áudio convertido e salvo em: {mp3_path}")
            return
        except subprocess.CalledProcessError:
            print("Conversão via ffmpeg falhou; tentando gravar tags no arquivo original...")

    # Se for m4a/mp4, grava tags MP4 (Explorer lê)
    if ext in {".m4a", ".mp4"}:
        try:
            tag_m4a(caminho, titulo, artista, album, faixa, total_faixas)
            print(f"Áudio salvo em (m4a/mp4 com tags): {caminho}")
            return
        except Exception as e:
            print("Falha ao gravar tags MP4:", e)

    # Fallback: tenta renomear para mp3 e gravar ID3 (pode não funcionar para webm)
    try:
        fallback = caminho.with_suffix(".mp3")
        caminho.rename(fallback)
        tag_mp3(fallback, titulo, artista, album, faixa, total_faixas)
        print(f"Áudio renomeado e tags aplicadas (fallback): {fallback}")
        return
    except Exception as e:
        print("Falha final ao aplicar tags:", e)
        print("Arquivo salvo em:", caminho)


# Função para baixar vídeo (melhorando nome)
def baixar_video(yt, destino, prefixo=""):
    stream = yt.streams.get_highest_resolution()
    arquivo_baixado = stream.download(output_path=str(destino), filename_prefix=prefixo)
    caminho = Path(arquivo_baixado)
    novo_nome = destino / (sanitize_path_name(f"{prefixo}{yt.title}") + caminho.suffix)
    if caminho != novo_nome:
        if novo_nome.exists():
            i = 1
            base = novo_nome.stem
            while novo_nome.exists():
                novo_nome = destino / f"{base}_{i}{caminho.suffix}"
                i += 1
        caminho.rename(novo_nome)
        caminho = novo_nome
    print(f"Vídeo salvo em: {caminho}")


# Função para processar um único link
def processar_url(url, opcao, prefixo="", faixa=None, total_faixas=None):
    yt = YouTube(url, on_progress_callback=on_progress)
    print(f"\nTítulo: {yt.title}\nDuração: {yt.length}s")

    if opcao == "1":
        baixar_video(yt, destino_video, prefixo)
    elif opcao == "2":
        baixar_mp3(yt, destino_audio, prefixo, faixa, total_faixas)
    elif opcao == "3":
        baixar_video(yt, destino_video, prefixo)
        baixar_mp3(yt, destino_audio, prefixo, faixa, total_faixas)
    else:
        print("Opção inválida! Escolha 1, 2 ou 3.")


# ----------------------
# Menu principal
# ----------------------
print("Escolha o que deseja fazer:")
print("1 - Baixar Vídeo")
print("2 - Baixar MP3")
print("3 - Baixar Ambos")
print("4 - Baixar Lista de URLs (arquivo .txt)")
print("5 - Baixar Playlist do YouTube")

opcao = input("Digite sua opção: ").strip()

if opcao in ["1", "2", "3"]:
    url = input("Digite a URL do vídeo do YouTube: ").strip()
    processar_url(url, opcao)

elif opcao == "4":
    arquivo_lista = input("Digite o caminho do arquivo .txt com as URLs: ").strip()
    if not os.path.exists(arquivo_lista):
        print("Arquivo não encontrado!")
    else:
        subopcao = input("Salvar como:\n1 - Vídeo\n2 - MP3\n3 - Ambos\nDigite sua opção: ").strip()
        with open(arquivo_lista, "r", encoding="utf-8") as f:
            urls = [linha.strip() for linha in f if linha.strip()]
        print(f"\nTotal de links encontrados: {len(urls)}\n")
        for url in urls:
            try:
                processar_url(url, subopcao)
            except Exception as e:
                print(f"Erro ao processar {url}: {e}")

elif opcao == "5":
    playlist_url = input("Digite a URL da playlist do YouTube: ").strip()
    subopcao = input("Salvar como:\n1 - Vídeo\n2 - MP3\n3 - Ambos\nDigite sua opção: ").strip()
    numerar = input("Deseja numerar os arquivos da playlist? (s/n): ").strip().lower()

    try:
        pl = Playlist(playlist_url)
        print(f"\nPlaylist encontrada: {pl.title}")
        print(f"Total de vídeos: {len(pl.video_urls)}\n")

        # cria subpastas organizadas por playlist (nome sanitizado)
        pasta_playlist = Path("downloads") / sanitize_path_name(pl.title)
        pasta_playlist.mkdir(parents=True, exist_ok=True)
        pasta_video_playlist = pasta_playlist / "videos"
        pasta_audio_playlist = pasta_playlist / "audios"
        pasta_video_playlist.mkdir(exist_ok=True)
        pasta_audio_playlist.mkdir(exist_ok=True)

        total = len(pl.video_urls)
        pad = max(2, len(str(total)))

        for i, url in enumerate(pl.video_urls, start=1):
            prefixo = f"{i:0{pad}d} - " if numerar == "s" else ""
            try:
                processar_url(url, subopcao, prefixo, faixa=i if subopcao in ["2", "3"] else None, total_faixas=(total if subopcao in ["2","3"] else None))
            except Exception as e:
                print(f"Erro ao processar {url}: {e}")

    except Exception as e:
        print(f"Erro ao carregar a playlist: {e}")

else:
    print("Opção inválida! Escolha 1, 2, 3, 4 ou 5.")
