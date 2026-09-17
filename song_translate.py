"""
song_translate.py
------------------
Baixa audio de videos do YouTube, transcreve com faster-whisper (deteccao
automatica de idioma) e traduz sempre para portugues brasileiro (PT-BR),
usando DeepL (online) ou Argos Translate (offline/local).

Requisitos:
    pip install faster-whisper yt-dlp requests
    # se for usar o engine "argos":
    pip install argostranslate

Uso basico (uma unica musica):
    python song_translate.py --urls "https://youtube.com/watch?v=XXXX" --engine deepl --deepl-key SUACHAVE

Uso em lote (varias musicas, um arquivo .txt com uma URL por linha):
    python song_translate.py --urls-file lista.txt --engine argos --model small

Saida:
    Para cada musica, gera dois arquivos em --output-dir (padrao: ./saida):
        <nome>_original.txt   -> transcricao no idioma original
        <nome>_pt-br.txt      -> traducao para PT-BR
    Um resumo final mostra sucessos e falhas. Erros individuais nao
    interrompem o lote.
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()  # carrega variaveis do arquivo .env na pasta do projeto, se existir
except ImportError:
    pass  # python-dotenv e opcional; sem ele, so funciona com variavel de ambiente do sistema

# --------------------------------------------------------------------------
# Configuracao de logging
# --------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("song_translate")


# --------------------------------------------------------------------------
# Utilitarios
# --------------------------------------------------------------------------
def slugify(text: str, maxlen: int = 60) -> str:
    """Transforma um titulo em um nome de arquivo seguro."""
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip()
    text = re.sub(r"[\s]+", "_", text)
    return text[:maxlen] if text else "musica"


def read_urls(args: argparse.Namespace) -> list[str]:
    urls: list[str] = []
    if args.urls:
        urls.extend(args.urls)
    if args.urls_file:
        path = Path(args.urls_file)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de URLs nao encontrado: {path}")
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    if not urls:
        raise ValueError("Nenhuma URL fornecida. Use --urls ou --urls-file.")
    return urls


# --------------------------------------------------------------------------
# Etapa 1: download do audio
# --------------------------------------------------------------------------
def download_audio(url: str, workdir: Path) -> Path:
    """Baixa o audio do video como mp3 usando yt-dlp e retorna o caminho."""
    out_template = str(workdir / "%(title)s.%(ext)s")

    # Pega o titulo primeiro, pra sabermos o nome final do arquivo.
    title_proc = subprocess.run(
        ["yt-dlp", "--get-title", url],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if title_proc.returncode != 0:
        raise RuntimeError(f"yt-dlp falhou ao obter titulo: {title_proc.stderr.strip()}")
    title = title_proc.stdout.strip() or "musica"

    dl_proc = subprocess.run(
        [
            "yt-dlp", "-x", "--audio-format", "mp3",
            "-o", out_template, url,
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if dl_proc.returncode != 0:
        raise RuntimeError(f"yt-dlp falhou ao baixar audio: {dl_proc.stderr.strip()}")

    mp3_path = workdir / f"{title}.mp3"
    if not mp3_path.exists():
        # yt-dlp as vezes sanitiza o nome de forma diferente; procura o mp3 mais recente.
        candidates = sorted(workdir.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            raise FileNotFoundError("Audio baixado nao foi encontrado apos o download.")
        mp3_path = candidates[0]

    return mp3_path


# --------------------------------------------------------------------------
# Etapa 2: transcricao com faster-whisper
# --------------------------------------------------------------------------
def transcribe(audio_path: Path, model_size: str) -> tuple[str, str]:
    """Transcreve o audio e retorna (texto, idioma_detectado)."""
    from faster_whisper import WhisperModel

    # int8 reduz bastante o uso de RAM/CPU, importante para hardware sem GPU
    # dedicada e com pouca memoria livre.
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(str(audio_path), beam_size=5)
    text_lines = [seg.text.strip() for seg in segments]
    full_text = "\n".join(text_lines)

    if not full_text.strip():
        raise RuntimeError("Transcricao retornou vazia (audio pode estar corrompido ou mudo).")

    return full_text, info.language


# --------------------------------------------------------------------------
# Etapa 3: traducao
# --------------------------------------------------------------------------
def translate_deepl(text: str, api_key: str, source_lang: str | None) -> str:
    if not api_key:
        raise ValueError("Chave da API DeepL nao fornecida (--deepl-key ou variavel DEEPL_API_KEY).")

    headers = {
        "Authorization": f"DeepL-Auth-Key {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "text": [text],
        "target_lang": "PT-BR",
    }
    # Deixa o DeepL autodetectar se nao tivermos certeza do codigo de idioma.
    if source_lang:
        deepl_source = source_lang.upper()
        # DeepL nao aceita todos os codigos ISO do whisper 1:1; nesses casos,
        # e mais seguro deixar o DeepL autodetectar.
        if deepl_source in {"EN", "DE", "ES", "FR", "IT", "JA", "PT", "RU", "ZH"}:
            body["source_lang"] = deepl_source

    resp = requests.post(
        "https://api-free.deepl.com/v2/translate",
        headers=headers,
        data=json.dumps(body),
        timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"DeepL retornou erro {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    return data["translations"][0]["text"]


_ARGOS_INSTALLED_PAIRS: set[tuple[str, str]] = set()


def _ensure_argos_package(source_lang: str, target_lang: str = "pt") -> None:
    """Garante que o pacote de idioma necessario esteja instalado no Argos."""
    import argostranslate.package
    import argostranslate.translate

    pair = (source_lang, target_lang)
    if pair in _ARGOS_INSTALLED_PAIRS:
        return

    installed = argostranslate.translate.get_installed_languages()
    has_pair = any(
        lang.code == source_lang and any(t.to_lang.code == target_lang for t in lang.translations_from)
        for lang in installed
    )
    if has_pair:
        _ARGOS_INSTALLED_PAIRS.add(pair)
        return

    log.info(f"Baixando pacote de idioma Argos: {source_lang} -> {target_lang} ...")
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    match = next(
        (p for p in available if p.from_code == source_lang and p.to_code == target_lang),
        None,
    )
    if match is None:
        raise RuntimeError(
            f"Nao ha pacote Argos direto para {source_lang}->{target_lang}. "
            "Tente o engine DeepL para esse idioma."
        )
    argostranslate.package.install_from_path(match.download())
    _ARGOS_INSTALLED_PAIRS.add(pair)


def translate_argos(text: str, source_lang: str) -> str:
    import argostranslate.translate

    # whisper usa codigos tipo "en", "de", "es" -- compativel com argos na maioria dos casos.
    _ensure_argos_package(source_lang, "pt")
    return argostranslate.translate.translate(text, source_lang, "pt")


# --------------------------------------------------------------------------
# Pipeline principal (por musica)
# --------------------------------------------------------------------------
def process_one(url: str, args: argparse.Namespace, output_dir: Path, workdir: Path) -> None:
    log.info(f"Processando: {url}")

    audio_path = download_audio(url, workdir)
    log.info(f"Audio baixado: {audio_path.name}")

    original_text, detected_lang = transcribe(audio_path, args.model)
    log.info(f"Transcrito ({len(original_text)} caracteres). Idioma detectado: {detected_lang}")

    if args.engine == "deepl":
        translated_text = translate_deepl(original_text, args.deepl_key, detected_lang)
    else:
        translated_text = translate_argos(original_text, detected_lang)

    base_name = slugify(audio_path.stem)
    (output_dir / f"{base_name}_original.txt").write_text(original_text, encoding="utf-8")
    (output_dir / f"{base_name}_pt-br.txt").write_text(translated_text, encoding="utf-8")

    log.info(f"OK -> {base_name}_pt-br.txt")

    if not args.keep_audio:
        try:
            audio_path.unlink()
        except OSError:
            pass


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Transcreve e traduz musicas do YouTube para PT-BR.")
    parser.add_argument("--urls", nargs="*", help="Uma ou mais URLs do YouTube.")
    parser.add_argument("--urls-file", help="Arquivo .txt com uma URL por linha.")
    parser.add_argument("--engine", choices=["deepl", "argos"], default="deepl",
                         help="Motor de traducao: deepl (online, melhor qualidade) ou argos (offline).")
    parser.add_argument("--deepl-key", default=None, help="Chave da API DeepL (ou defina DEEPL_API_KEY).")
    parser.add_argument("--model", default="small",
                         help="Modelo do faster-whisper: tiny, base, small, medium, large-v3. "
                              "Recomendado 'small' para CPU sem GPU dedicada.")
    parser.add_argument("--output-dir", default="saida", help="Pasta de saida dos arquivos traduzidos.")
    parser.add_argument("--keep-audio", action="store_true", help="Mantem os arquivos .mp3 baixados.")
    args = parser.parse_args()

    if args.deepl_key is None:
        args.deepl_key = os.environ.get("DEEPL_API_KEY")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    workdir = output_dir / "_audio_tmp"
    workdir.mkdir(parents=True, exist_ok=True)

    urls = read_urls(args)
    log.info(f"{len(urls)} musica(s) na fila. Engine de traducao: {args.engine}")

    sucesso: list[str] = []
    falha: list[tuple[str, str]] = []

    for i, url in enumerate(urls, start=1):
        log.info(f"--- [{i}/{len(urls)}] ---")
        try:
            process_one(url, args, output_dir, workdir)
            sucesso.append(url)
        except Exception as exc:  # noqa: BLE001 - queremos continuar o lote mesmo com erro
            log.error(f"Falhou: {url} -> {exc}")
            falha.append((url, str(exc)))
            continue

    log.info("=" * 50)
    log.info(f"Concluido: {len(sucesso)} sucesso(s), {len(falha)} falha(s).")
    if falha:
        log.info("Musicas com erro:")
        for url, err in falha:
            log.info(f"  - {url}: {err}")

    if not args.keep_audio:
        try:
            workdir.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        log.error(f"Erro fatal: {exc}")
        sys.exit(1)
