# api/server.py
import uvicorn  # Servidor ASGI para FastAPI
from fastapi import FastAPI # Framework web rápido
from fastapi.middleware.cors import CORSMiddleware # Middleware para CORS
from dotenv import load_dotenv # Para carregar variáveis do .env
from .routes import router as api_router # Importa o router de rotas
import os # Para verificar o ambiente

# Carrega as variáveis de ambiente do arquivo .env (deve estar na pasta /backend/)
load_dotenv()

# Cria a instância da aplicação FastAPI
app = FastAPI(
    title="CARF.AI Back-end API",
    description="API para Gestão de Competências e Produtividade - Hackathon CARF.",
    version="1.0.0",
)

# Configuração do CORS (Crucial para o Front-end)
# Permite o Front-end (ex: localhost:8080 ou a URL do Ngrok) acessar o Back-end
origins = [
    "http://localhost",
    "http://localhost:8080",  # Porta padrão do Front-end Vite
    "http://127.0.0.1:8080",
    "*" # Permite qualquer origem durante o Hackathon para evitar bugs de rede
]

# Adiciona o middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Permite as origens definidas
    allow_credentials=True, # Permite cookies (se necessário)
    allow_methods=["*"], # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"], # Permite todos os headers
)

# Inclui as rotas da API com o prefixo /api
app.include_router(api_router, prefix="/api")

# Função para iniciar o servidor
def start():
    """Inicia o servidor Uvicorn."""
    # O reload=True é ótimo para desenvolvimento, reiniciando a cada mudança
    uvicorn.run("api.server:app", host="0.0.0.0", port=8001, reload=True) 

# Bloco de execução principal
if __name__ == "__main__":
    start()