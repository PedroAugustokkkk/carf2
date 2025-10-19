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

VERCEL_FRONTEND_URL = os.environ.get("CORS_ORIGIN", "https://carf-insight-ai.vercel.app") 

# Lista de origens permitidas:
origins = [
    VERCEL_FRONTEND_URL, # O domínio do Vercel
    "http://localhost:3000", # Para desenvolvimento local (seu e do seu colega)
    "http://localhost:8000"  # Caso precisem de outra porta local
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
