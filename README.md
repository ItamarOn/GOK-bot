# for local development
```
.venv/bin/uvicorn main:app --reload
# Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

ngrok http 8000
# Forwarding   https://obdulia-elucidative-dorthey.ngrok-free.dev -> http://localhost:8000
```

# config in Twillio Console: the ngrok url + /process