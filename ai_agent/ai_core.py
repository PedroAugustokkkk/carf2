# ai_agent/ai_core.py
import os 
import json 
from io import BytesIO

# Dependências da IA
from google import genai
from google.genai import types

# Dependências de Áudio e Produtividade (Leitura de Documentos e TTS)
from gtts import gTTS
import base64
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document 

# Define o nome da variável de ambiente para a chave da API
API_KEY_VAR = "GEMINI_API_KEY"

# Define os modelos a serem usados (o flash é rápido para Hackathon)
MODELO_CHAT = 'gemini-2.5-flash'
MODELO_SUGESTAO = 'gemini-2.5-flash'

# Contexto Institucional do CARF (Núcleo de Conhecimento para a IA)
CONTEXTO_CARF = """
O Conselho Administrativo de Recursos Fiscais (CARF) é um órgão colegiado do Ministério da Fazenda, responsável por julgar em segunda e última instância administrativa os litígios tributários federais entre contribuintes e o Fisco.
Função Primária: Assegurar a imparcialidade, a segurança jurídica e a celeridade na solução dos litígios tributários.
Atribuições: Julgamento de Recursos Voluntários e de Ofício, análise de Súmulas e Resoluções, e uniformização da jurisprudência administrativa.
Foco de Produtividade (RH Mínimo): O RH do CARF é enxuto (1 servidor + 2 terceirizados). Todas as sugestões do CARF.AI devem focar em alívio de carga operacional, automação, excelência técnica, e redução de estoque processual.
"""

# --- Funções Auxiliares de Sistema ---

def _get_client_and_check_key():
    """Verifica a chave da API e retorna o cliente Gemini."""
    api_key = os.getenv(API_KEY_VAR)
    # Lança exceção se a chave não estiver no .env
    if not api_key:
        raise ValueError(f"API Key '{API_KEY_VAR}' não configurada.") 
    return genai.Client(api_key=api_key)

def _generate_tts_base64(texto: str) -> str:
    """Função de Áudio (Text-to-Speech): Converte texto em áudio MP3 e retorna Base64."""
    try:
        # Cria um objeto de áudio TTS
        tts = gTTS(texto, lang='pt')
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        # Codifica o conteúdo em Base64, pronto para ser consumido pelo Front-end
        return base64.b64encode(mp3_fp.read()).decode('utf-8')
    except Exception as e:
        print(f"Erro ao gerar áudio TTS: {e}")
        return ""

def read_document_content(file_path: str, file_mime_type: str) -> str:
    """
    Função de Leitura de Documentos: Extrai conteúdo de diversos formatos.
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    # Lista de extensões suportadas
    try:
        if file_extension == '.pdf':
            reader = PdfReader(file_path)
            # Extrai texto da primeira página como snippet (limita a 1000 chars para não sobrecarregar o Gemini)
            return reader.pages[0].extract_text()[:1000] 
        
        elif file_extension == '.docx':
            document = Document(file_path)
            # Concatena o texto dos parágrafos
            return "\n".join([p.text for p in document.paragraphs])[:1000]

        elif file_extension in ['.xlsx', '.csv']:
            # Usa Pandas para ler dados estruturados
            if file_extension == '.xlsx':
                df = pd.read_excel(file_path)
            else: 
                df = pd.read_csv(file_path)
            
            # Retorna as primeiras 5 linhas como representação do conteúdo para a IA
            return f"Dados estruturados (primeiras 5 linhas):\n{df.head().to_string()}"

        else:
            # Se o arquivo não é suportado
            return f"Tipo de arquivo '{file_extension}' não suportado pelo Agente de Produtividade."
            
    except Exception as e:
        # Erro ao abrir/processar o arquivo
        return f"Erro na leitura do arquivo {file_path}: {str(e)}"


# --- Agentes de IA Principais ---

def sugerir_cursos_gemini(perfil_servidor: dict, catalogo_cursos: list) -> dict:
    """Gera uma trilha de desenvolvimento personalizada (Agente de Cursos)."""
    try:
        cliente = _get_client_and_check_key()
    except ValueError as e:
        return {"error": str(e), "details": "Configuração de API Key ausente."}

    # ... (lógica de formatação de prompt e chamada ao Gemini) ...
    # (Usando o prompt que já havíamos definido para o curso)

    gaps_str = "\n".join([f"- {g['competencia']} (Lacuna: {g['lacuna_percentual']}%)" for g in perfil_servidor.get('lacunas_identificadas', [])])
    catalogo_str = "\n".join([f"- {curso}" for curso in catalogo_cursos])

    prompt = f"""
    {CONTEXTO_CARF}
    
    Você é o Agente de Desenvolvimento de Competências (CSUA) do CARF.
    Sua missão é criar uma "Trilha de Cursos Otimizada" para o servidor. A solução deve ser autônoma (self-service) para aliviar a carga do RH.

    ## Perfil do Servidor
    Nome: {perfil_servidor.get('nome')}
    Função: {perfil_servidor.get('funcao')}
    
    ## Lacunas Críticas Identificadas (Gaps)
    {gaps_str}

    ## Catálogo de Cursos Disponíveis
    {catalogo_str}

    ## Instruções de Saída:
    1. Crie no máximo 4 passos, priorizando os Gaps mais críticos e estratégicos.
    2. Garanta que a sugestão seja o curso EXATO do Catálogo e relacione o curso diretamente com a produtividade e a função no CARF.
    3. A saída deve ser um JSON VÁLIDO.
    
    Exemplo do formato JSON que você DEVE retornar:
    {{
      "servidor_id": {perfil_servidor.get('id')},
      "trilha_sugerida": [
        {{
          "passo": 1,
          "curso_sugerido": "Nome do Curso EXATO",
          "justificativa": "Esta é a justificativa de alto impacto para o CARF, focada em produtividade e redução de lacunas."
        }}
      ]
    }}
    """
    
    try:
        response = cliente.models.generate_content(
            model=MODELO_SUGESTAO,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        return json.loads(response.text)
    
    except Exception as e:
        return {"error": "Erro ao gerar sugestão de curso", "details": str(e)}

def processar_chat_institucional(pergunta: str, anexo_texto: str = None, gerar_audio: bool = False) -> dict:
    """
    Processa a pergunta do chat (Agente Conversacional), usando o contexto do CARF e o anexo opcional.
    """
    try:
        cliente = _get_client_and_check_key()
    except ValueError as e:
        return {"error": str(e), "details": "Configuração de API Key ausente."}

    # Prepara o texto do anexo no prompt
    anexo_info = f"--- Conteúdo do Documento Anexo (Produtividade Direta):\n{anexo_texto}\n---" if anexo_texto else "Nenhum documento anexo fornecido."

    # Monta o prompt de análise de produtividade/institucional
    prompt_base = f"""
    {CONTEXTO_CARF}
    
    Você é o CARF.AI, um Agente de Suporte Institucional e Produtividade. Responda à pergunta do servidor.
    
    ## Instruções de Resposta:
    1. Responda de forma clara e concisa.
    2. Se houver anexo, utilize-o para fornecer a resposta de produtividade direta. Exemplo: Se o anexo for uma planilha de processos, sugira a melhor forma de priorizar os 5 processos mais antigos.
    3. Mantenha o tom formal e técnico.
    
    {anexo_info}
    
    ## Pergunta do Servidor:
    {pergunta}
    """
    
    try:
        response = cliente.models.generate_content(
            model=MODELO_CHAT,
            contents=prompt_base
        )
        resposta_texto = response.text
        
        # 1. Preparar a Resposta
        resultado = {"remetente": "assistant", "texto": resposta_texto, "audio_base64": None}
        
        # 2. Geração de Áudio (Text-to-Speech)
        if gerar_audio:
            # Codifica o áudio e adiciona ao resultado
            resultado["audio_base64"] = _generate_tts_base64(resposta_texto)
            
        return resultado
        
    except Exception as e:
        return {"error": "Erro ao processar a pergunta com o Gemini", "details": str(e)}