# api/routes.py
import json # Para desserializar JSON
import os # Para caminhos de arquivo
import traceback # Para capturar o log de erro completo

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel # Para validação de dados de entrada

# Importa o core de IA (ai_core.py)
from ai_agent.ai_core import ( 
    sugerir_cursos_gemini, 
    processar_chat_institucional
) 

router = APIRouter()

# --- Configuração de Dados e Schemas ---

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
SERVIDORES_FILE = os.path.join(DATA_PATH, 'servidores.json')
CATALOGO_FILE = os.path.join(DATA_PATH, 'catalogo_cursos.json')

def load_data(file_path: str):
    """Carrega dados de um arquivo JSON local."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Arquivo de dados não encontrado: {file_path}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Erro ao decodificar JSON do arquivo: {file_path}")

class PerfilInput(BaseModel):
    id: int 
    gaps: list

# CRÍTICO: Novo modelo de entrada para o chat (só texto/áudio)
class ChatInput(BaseModel):
    pergunta: str 
    gerar_audio: bool = False

# --- Endpoints da API ---

# Endpoint 1: Dados do Dashboard e Perfil (GET /api/dashboard_data)
@router.get("/dashboard_data")
def get_dashboard_data():
    """Retorna métricas, perfil do servidor e dados de gráficos."""
    servidores = load_data(SERVIDORES_FILE)
    
    if not servidores:
        raise HTTPException(status_code=404, detail="Nenhum servidor encontrado nos dados mock.")

    servidor = servidores[0]
    
    return {
        "metricas_gerais": servidor["metricas_gerais"],
        "perfil": {
            "nome": servidor["nome"],
            "funcao": servidor["funcao"],
            "vinculo": servidor["vinculo"],
            "competencias_concluidas_percentual": servidor["competencias_concluidas_percentual"],
            "competencias_principais": servidor["competencias_principais"]
        },
        "lacunas": servidor["lacunas_identificadas"],
        "trilhas": servidor["trilhas_em_andamento"],
        "engajamento": servidor["engajamento_mensal"]
    }


# Endpoint 2: Sugestão de Trilhas de Capacitação (POST /api/sugerir_trilha)
@router.post("/sugerir_trilha")
def post_sugerir_trilha(perfil_input: PerfilInput):
    """Gera uma trilha de desenvolvimento personalizada usando o Agente Gemini (CSUA)."""
    
    try:
        servidores = load_data(SERVIDORES_FILE)
        catalogo = load_data(CATALOGO_FILE)
        
        perfil_completo = next((s for s in servidores if s["id"] == perfil_input.id), None)
        
        if not perfil_completo:
            raise HTTPException(status_code=404, detail=f"Servidor com ID {perfil_input.id} não encontrado.")
        
        resultado_ia = sugerir_cursos_gemini(perfil_completo, catalogo)
        
        if "error" in resultado_ia:
            raise HTTPException(status_code=500, detail=resultado_ia["details"])

        return resultado_ia
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n--- ERRO CRÍTICO NA ROTA /sugerir_trilha ---\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erro interno na IA: {str(e)}. Verifique o log do Back-end.")


# Endpoint 3: Assistente Conversacional (POST /api/chat_institucional)
# CRÍTICO: Recebe apenas o ChatInput JSON
@router.post("/chat_institucional")
def post_chat_institucional(input: ChatInput):
    """
    Processa o chat: apenas mensagens de texto e opção de áudio (TTS).
    """
    
    texto_anexo = None # Anexo permanentemente desativado
    
    try:
        # Processamento da Pergunta (e Áudio)
        resultado_ia = processar_chat_institucional(input.pergunta, texto_anexo, input.gerar_audio)
        
        if "error" in resultado_ia:
            raise HTTPException(status_code=500, detail=resultado_ia["details"])
            
        return resultado_ia
    except HTTPException:
        raise
    except Exception as e:
        # Este bloco garante que o erro aparece no terminal
        print(f"\n--- ERRO CRÍTICO NA ROTA /chat_institucional ---\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}. Verifique o log do Back-end.")