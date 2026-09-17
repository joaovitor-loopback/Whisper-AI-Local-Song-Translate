# 🎵 Whisper AI Local Song Translate

CLI local para transcrição e tradução automática de faixas de áudio do YouTube (EN/DE/ES/etc. → PT-BR), usando `faster-whisper` (CTranslate2) para ASR e DeepL API ou Argos Translate como back-end de tradução.

Pipeline: `yt-dlp` (download) → `faster-whisper` (ASR + language detection) → DeepL API / Argos Translate (MT) → output em `.txt`.

---

## Stack

- **ASR:** [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) (CTranslate2), `compute_type="int8"`, inferência CPU-only.
- **Download:** `yt-dlp`, extração de áudio via FFmpeg (`--audio-format mp3`).
- **MT:** DeepL REST API (`api-free.deepl.com/v2/translate`) ou Argos Translate (offline, pivot automático via pacotes de idioma).
- **Config:** `python-dotenv`, variáveis carregadas de `.env` em runtime.
- **Execução:** batch com isolamento de falha por item (try/except por música, sem abortar o lote), logging estruturado via `logging`.

---

## Requisitos

- Python ≥ 3.10
- FFmpeg no PATH
- ~2GB livres de RAM para o modelo `small` em int8 (ajuste conforme hardware — ver seção de performance)

```bash
git clone https://github.com/SEU_USUARIO/song-translate.git
cd song-translate
python -m venv venv && source venv/bin/activate   # ou .\venv\Scripts\Activate.ps1 no Windows
pip install -r requirements.txt
```

`requirements.txt`:
```
faster-whisper
yt-dlp
requests
python-dotenv
argostranslate   # opcional, apenas para --engine argos
```

---

## Configuração

```bash
cp .env.example .env
```

```
DEEPL_API_KEY=xxxxxxxxxxxxxxxx
```

Necessário apenas para `--engine deepl`. `.env` está no `.gitignore` — não versionar chaves.

---

## Uso

```bash
# item único
python song_translate.py --urls "<url>" --engine deepl --model small

# batch (um recurso por linha em arquivo texto)
python song_translate.py --urls-file urls.txt --engine argos --model small

# manter os artefatos de áudio intermediários (debug)
python song_translate.py --urls-file urls.txt --keep-audio
```

### Flags

| Flag | Tipo | Default | Descrição |
|---|---|---|---|
| `--urls` | `list[str]` | — | URLs via argumento posicional |
| `--urls-file` | `str` | — | Path para arquivo com uma URL/linha |
| `--engine` | `{deepl,argos}` | `deepl` | Back-end de tradução |
| `--deepl-key` | `str` | `$DEEPL_API_KEY` | Override da chave sem usar `.env` |
| `--model` | `str` | `small` | Modelo faster-whisper (`tiny`\|`base`\|`small`\|`medium`\|`large-v3`) |
| `--output-dir` | `str` | `saida` | Diretório de saída |
| `--keep-audio` | `flag` | `False` | Não remove os `.mp3` intermediários |

### Output

```
saida/
├── <slug>_original.txt
└── <slug>_pt-br.txt
```

Nome do arquivo é derivado do título do vídeo via `slugify()` (regex, sem dependência externa).

---

## Notas de performance / seleção de modelo

Sem GPU dedicada (Iris Xe / UHD / equivalente), `faster-whisper` com `compute_type=int8` no modelo `small` é o ponto de equilíbrio recomendado entre latência e WER para faixas de 3–5min. `medium`/`large-v3` aumentam consumo de RAM significativamente (~5GB+ para `medium` em fp32; menos em int8, mas ainda expressivo) — avalie o headroom de memória disponível antes de escalar o modelo, principalmente em máquinas já sob pressão de memória (IDE + browser + containers rodando em paralelo).

Se necessário rodar em CI ou container com recursos restritos, `tiny`/`base` são viáveis para triagem, com queda perceptível de precisão em trechos cantados/melismáticos.

---

## Tratamento de erro / idempotência

- Cada URL é processada em bloco `try/except` isolado; falha em um item não aborta o restante do batch.
- Resumo final: contagem de sucesso/falha + lista de erros por URL.
- Download de pacotes de idioma do Argos é lazy e cacheado em memória de processo (`_ARGOS_INSTALLED_PAIRS`) para evitar round-trips repetidos no mesmo lote.
- Sem retry automático em falhas de rede (DeepL/yt-dlp) — se necessário, wrap externo com backoff.

---

## Limitações conhecidas

- `source_lang` no DeepL é restrito a um allowlist de códigos ISO compatíveis; idiomas fora dessa lista caem em auto-detecção do próprio DeepL.
- Argos Translate depende de pacote de idioma disponível no índice oficial para o par `<lang>→pt`; sem pacote direto, falha (não implementa pivot manual via inglês).
- Sem suporte a diarização ou timestamps por linha no output atual (transcrição é concatenada em texto corrido por segmento).

---

## Escopo de uso

Projeto para uso pessoal/local — não realiza redistribuição, cache público ou hospedagem de letras de terceiros. Toda transcrição/tradução é gerada e mantida localmente pelo usuário a partir de áudio processado na própria máquina.
## Licença

MIT (ou ajuste conforme sua preferência).
