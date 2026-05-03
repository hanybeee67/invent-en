#!/bin/bash

# Caddy 역방향 프록시 다운로드 (API와 화면을 하나의 포트로 연결해줌)
if [ ! -f caddy ]; then
    curl -L "https://caddyserver.com/api/download?os=linux&arch=amd64" -o caddy
    chmod +x caddy
fi

# Caddy 설정 파일 생성
cat << CONFIG_EOF > Caddyfile
:$PORT {
    handle /api/* {
        reverse_proxy 127.0.0.1:8000
    }
    handle {
        reverse_proxy 127.0.0.1:8501
    }
}
CONFIG_EOF

# 1. FastAPI 서버 실행 (백그라운드)
uvicorn api_server:app --host 127.0.0.1 --port 8000 &

# 2. Streamlit 화면 실행 (백그라운드)
streamlit run app-en.py --server.port 8501 --server.address 127.0.0.1 &

# 3. Caddy 실행 (포그라운드 - Render.com에 포트 노출)
./caddy run
