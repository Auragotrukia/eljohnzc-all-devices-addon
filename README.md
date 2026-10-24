# Eljohnzc Lossless + Atmos (All Devices)

A BitChord-compatible wrapper around the supplied Eljohnzc addon. It intentionally omits `checkValidLossless`, so BitChord does not reject installation merely because a lossless-capable output device is not connected.

The wrapper forwards `quality`, `atmos`, `q`, and related request parameters to the upstream service and preserves upstream stream metadata. It does not manufacture Atmos metadata or transcode Atmos into stereo. If the upstream returns an Atmos-capable stream and the device supports it, BitChord may use it; otherwise the client/decoder must use a compatible stereo or lossless stream.

The upstream service was returning HTTP 502 during initial testing, so the wrapper cannot be considered healthy until its `/search` endpoint responds successfully again.

## Endpoints

- `GET /manifest.json`
- `GET /health`
- `GET /search?q=...&quality=...&atmos=...`
- `GET /stream/{id}?quality=...&atmos=...`

## Local test

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
