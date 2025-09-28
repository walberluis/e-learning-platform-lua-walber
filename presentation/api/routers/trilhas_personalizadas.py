"""
Trilhas Personalizadas (Custom Learning Paths) API endpoints.
Presentation Layer - API Package
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from pydantic import BaseModel, Field
from presentation.api.schemas.user_schemas import APIResponse
from lua_bridge.lua_engine import get_lua_engine
from infrastructure.integration.gemini_client import gemini_client
import json
import asyncio

router = APIRouter()

# Variável global para simular trilhas criadas dinamicamente
created_trilhas_cache = []

# Variável global para trilhas excluídas (incluindo trilhas base)
deleted_trilhas_ids = []

@router.post("/quiz/generate", response_model=APIResponse)
async def generate_quiz_questions(request: dict):
    """
    Generate quiz questions for a module using AI.
    """
    try:
        trilha_id = request.get('trilha_id')
        module_id = request.get('module_id')
        topic = request.get('topic', 'Programação')
        difficulty = request.get('difficulty', 'iniciante')
        count = request.get('count', 10)
        
        # Tentar usar LLM para gerar questões de qualidade
        try:
            questions = await generate_questions_with_llm(topic, difficulty, count)
        except Exception as e:
            print(f"Erro ao gerar questões com LLM: {e}")
            # Fallback para questões melhoradas
            questions = generate_improved_mock_questions(topic, difficulty, count)
        
        return APIResponse(
            success=True,
            message="Questões geradas com sucesso",
            data={
                "questions": questions,
                "module_id": module_id,
                "trilha_id": trilha_id,
                "topic": topic,
                "difficulty": difficulty,
                "total_questions": len(questions)
            }
        )
        
    except Exception as e:
        print(f"Error generating quiz questions: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar questões do quiz")

# Generate questions using LLM
async def generate_questions_with_llm(topic: str, difficulty: str, count: int):
    """Generate high-quality questions using Gemini AI"""
    
    difficulty_map = {
        "iniciante": "básico",
        "intermediario": "intermediário", 
        "avancado": "avançado"
    }
    
    difficulty_pt = difficulty_map.get(difficulty, difficulty)
    
    prompt = f"""Crie {count} questões de múltipla escolha sobre "{topic}" para nível {difficulty_pt}.

FORMATO EXATO para cada questão:
QUESTÃO: [pergunta clara e específica]
A) [alternativa]
B) [alternativa] 
C) [alternativa]
D) [alternativa]
E) [alternativa]
RESPOSTA: [letra da resposta correta]
EXPLICAÇÃO: [explicação detalhada da resposta]

REGRAS:
- Questões práticas e específicas sobre {topic}
- Uma alternativa correta e quatro incorretas plausíveis
- Explicações educativas de 2-3 linhas
- Linguagem clara e objetiva
- Foque em conceitos importantes de {topic}

Exemplo para Python básico:
QUESTÃO: Qual é a forma correta de declarar uma variável em Python?
A) var nome = "João"
B) nome = "João"
C) string nome = "João"
D) let nome = "João"
E) declare nome = "João"
RESPOSTA: B
EXPLICAÇÃO: Em Python, variáveis são declaradas simplesmente atribuindo um valor, sem necessidade de palavras-chave como 'var' ou declaração de tipo.

Agora crie {count} questões sobre {topic}:"""

    try:
        llm_response = await gemini_client.generate_content(prompt)
        
        if llm_response and len(llm_response.strip()) > 0:
            questions = parse_llm_questions(llm_response, count)
            if len(questions) > 0:
                return questions
        
        # Se não conseguiu parsear, usar fallback
        raise Exception("Não foi possível parsear as questões da LLM")
        
    except Exception as e:
        print(f"Erro na LLM: {e}")
        raise e

# Parse LLM response into structured questions
def parse_llm_questions(llm_response: str, expected_count: int):
    """Parse the LLM response into structured question format"""
    questions = []
    
    try:
        # Split by QUESTÃO: to get individual questions
        parts = llm_response.split("QUESTÃO:")
        
        for i, part in enumerate(parts[1:], 1):  # Skip first empty part
            if i > expected_count:
                break
                
            lines = [line.strip() for line in part.strip().split('\n') if line.strip()]
            
            if len(lines) < 7:  # Need at least question + 5 alternatives + answer + explanation
                continue
                
            # Extract question
            question_text = lines[0]
            
            # Extract alternatives
            alternatives = []
            answer_line_idx = -1
            
            for j, line in enumerate(lines[1:], 1):
                if line.startswith(('A)', 'B)', 'C)', 'D)', 'E)')):
                    letter = line[0].lower()
                    text = line[3:].strip()  # Remove "A) "
                    alternatives.append({"letter": letter, "text": text})
                elif line.startswith('RESPOSTA:'):
                    answer_line_idx = j
                    break
            
            if len(alternatives) != 5 or answer_line_idx == -1:
                continue
                
            # Extract correct answer
            answer_line = lines[answer_line_idx]
            correct_answer = answer_line.replace('RESPOSTA:', '').strip().lower()
            
            # Extract explanation
            explanation = ""
            for k in range(answer_line_idx + 1, len(lines)):
                if lines[k].startswith('EXPLICAÇÃO:'):
                    explanation = lines[k].replace('EXPLICAÇÃO:', '').strip()
                    # Include next lines if they're part of explanation
                    for m in range(k + 1, len(lines)):
                        if not lines[m].startswith(('QUESTÃO:', 'A)', 'B)', 'C)', 'D)', 'E)', 'RESPOSTA:')):
                            explanation += " " + lines[m]
                        else:
                            break
                    break
            
            if explanation and correct_answer in ['a', 'b', 'c', 'd', 'e']:
                question = {
                    "id": i,
                    "question": question_text,
                    "alternatives": alternatives,
                    "correct_answer": correct_answer,
                    "explanation": explanation
                }
                questions.append(question)
    
    except Exception as e:
        print(f"Erro ao parsear questões: {e}")
        
    return questions

# Generate improved mock questions as fallback
def generate_improved_mock_questions(topic: str, difficulty: str, count: int):
    """Generate better mock questions based on topic and difficulty"""
    
    # Question templates based on topic
    templates = {
        "python": [
            {
                "question": "Qual é a forma correta de criar uma lista em Python?",
                "alternatives": [
                    {"letter": "a", "text": "lista = []"},
                    {"letter": "b", "text": "lista = {}"},
                    {"letter": "c", "text": "lista = ()"},
                    {"letter": "d", "text": "lista = new List()"},
                    {"letter": "e", "text": "lista = array()"}
                ],
                "correct": "a",
                "explanation": "Em Python, listas são criadas usando colchetes []. Chaves {} criam dicionários, parênteses () criam tuplas."
            },
            {
                "question": "Como você imprime 'Olá Mundo' em Python?",
                "alternatives": [
                    {"letter": "a", "text": "print('Olá Mundo')"},
                    {"letter": "b", "text": "console.log('Olá Mundo')"},
                    {"letter": "c", "text": "echo 'Olá Mundo'"},
                    {"letter": "d", "text": "System.out.println('Olá Mundo')"},
                    {"letter": "e", "text": "printf('Olá Mundo')"}
                ],
                "correct": "a",
                "explanation": "A função print() é usada em Python para exibir texto na tela. As outras opções são de linguagens diferentes."
            },
            {
                "question": "Qual é o resultado de len([1, 2, 3, 4, 5]) em Python?",
                "alternatives": [
                    {"letter": "a", "text": "5"},
                    {"letter": "b", "text": "4"},
                    {"letter": "c", "text": "15"},
                    {"letter": "d", "text": "Erro"},
                    {"letter": "e", "text": "[1, 2, 3, 4, 5]"}
                ],
                "correct": "a",
                "explanation": "A função len() retorna o número de elementos em uma sequência. A lista tem 5 elementos, então len() retorna 5."
            },
            {
                "question": "Como comentar uma linha em Python?",
                "alternatives": [
                    {"letter": "a", "text": "# Este é um comentário"},
                    {"letter": "b", "text": "// Este é um comentário"},
                    {"letter": "c", "text": "/* Este é um comentário */"},
                    {"letter": "d", "text": "<!-- Este é um comentário -->"},
                    {"letter": "e", "text": "-- Este é um comentário"}
                ],
                "correct": "a",
                "explanation": "Em Python, comentários de linha única começam com #. As outras sintaxes são de outras linguagens de programação."
            }
        ],
        "javascript": [
            {
                "question": "Como declarar uma variável em JavaScript ES6+?",
                "alternatives": [
                    {"letter": "a", "text": "let variavel = 'valor'"},
                    {"letter": "b", "text": "variable variavel = 'valor'"},
                    {"letter": "c", "text": "variavel = 'valor'"},
                    {"letter": "d", "text": "string variavel = 'valor'"},
                    {"letter": "e", "text": "declare variavel = 'valor'"}
                ],
                "correct": "a",
                "explanation": "Em JavaScript ES6+, usamos 'let' ou 'const' para declarar variáveis com escopo de bloco."
            },
            {
                "question": "Qual será o resultado de console.log(typeof null) em JavaScript?",
                "alternatives": [
                    {"letter": "a", "text": "'object'"},
                    {"letter": "b", "text": "'null'"},
                    {"letter": "c", "text": "'undefined'"},
                    {"letter": "d", "text": "'boolean'"},
                    {"letter": "e", "text": "'string'"}
                ],
                "correct": "a",
                "explanation": "Em JavaScript, typeof null retorna 'object'. Isso é considerado um bug histórico da linguagem que foi mantido por compatibilidade."
            },
            {
                "question": "Como criar um array em JavaScript?",
                "alternatives": [
                    {"letter": "a", "text": "let arr = []"},
                    {"letter": "b", "text": "let arr = {}"},
                    {"letter": "c", "text": "let arr = ()"},
                    {"letter": "d", "text": "let arr = new Array"},
                    {"letter": "e", "text": "let arr = list()"}
                ],
                "correct": "a",
                "explanation": "Arrays em JavaScript são criados usando colchetes [] ou o construtor new Array(). A forma mais comum e recomendada é usar []."
            }
        ],
        "default": [
            {
                "question": f"Qual é um conceito fundamental em {topic}?",
                "alternatives": [
                    {"letter": "a", "text": f"Entender os princípios básicos de {topic}"},
                    {"letter": "b", "text": "Ignorar a documentação"},
                    {"letter": "c", "text": "Copiar código sem entender"},
                    {"letter": "d", "text": "Pular os fundamentos"},
                    {"letter": "e", "text": "Não praticar"}
                ],
                "correct": "a",
                "explanation": f"É essencial entender os princípios básicos de {topic} antes de avançar para conceitos mais complexos."
            }
        ]
    }
    
    # Determine which template set to use
    topic_lower = topic.lower()
    if "python" in topic_lower:
        question_set = templates["python"]
    elif "javascript" in topic_lower:
        question_set = templates["javascript"]
    else:
        question_set = templates["default"]
    
    questions = []
    for i in range(count):
        template_idx = i % len(question_set)
        template = question_set[template_idx]
        
        question = {
            "id": i + 1,
            "question": template["question"],
            "alternatives": template["alternatives"],
            "correct_answer": template["correct"],
            "explanation": template["explanation"]
        }
        questions.append(question)
    
    return questions

# Pydantic schemas for trilhas personalizadas
class TrilhaPersonalizadaRequest(BaseModel):
    """Request model for creating personalized learning paths"""
    user_id: int = Field(..., description="ID do usuário")
    topic: str = Field(..., min_length=5, max_length=500, description="Tópico que deseja aprender")
    difficulty: str = Field(..., description="Nível de dificuldade: iniciante, intermediario, avancado")

class QuizSessionRequest(BaseModel):
    """Request model for starting a quiz session"""
    user_id: int = Field(..., description="ID do usuário")
    module_id: int = Field(..., description="ID do módulo/conteúdo")

class QuizAnswerRequest(BaseModel):
    """Request model for submitting quiz answers"""
    user_id: int = Field(..., description="ID do usuário")
    question_id: int = Field(..., description="ID da questão")
    selected_answer: str = Field(..., pattern="^[abcde]$", description="Resposta selecionada (a, b, c, d, e)")

@router.post("/create", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_trilha_personalizada(request: TrilhaPersonalizadaRequest):
    """
    Criar uma nova trilha de aprendizado personalizada usando IA.
    
    - **user_id**: ID do usuário que está criando a trilha
    - **topic**: Tópico que o usuário deseja aprender (ex: "conceitos fundamentais da linguagem Python")
    - **difficulty**: Nível de dificuldade (iniciante, intermediario, avancado)
    
    O sistema irá:
    1. Gerar estrutura da trilha usando Lua business logic
    2. Criar módulos de aprendizado com quizzes
    3. Usar IA (Gemini) para gerar questões personalizadas
    4. Inscrever automaticamente o usuário na trilha
    """
    try:
        # Por enquanto, usar implementação mock para testar a interface
        # TODO: Implementar integração completa com Lua e IA quando estiver pronto
        
        # Simular delay de processamento
        import asyncio
        import time
        await asyncio.sleep(2)
        
        # Timestamp atual
        current_time = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Gerar estrutura mock da trilha
        difficulty_labels = {
            "iniciante": "Fundamentos",
            "intermediario": "Intermediário",
            "avancado": "Avançado"
        }
        
        modules_count = {
            "iniciante": 3,
            "intermediario": 4,
            "avancado": 5
        }
        
        # Melhorar/corrigir o título da trilha (versão simples + LLM como fallback)
        def improve_title_simple(topic):
            """Correções básicas de títulos comuns"""
            corrections = {
                'phyton': 'Python',
                'pyton': 'Python', 
                'python': 'Python',
                'java script': 'JavaScript',
                'javascript': 'JavaScript',
                'html': 'HTML',
                'css': 'CSS',
                'react': 'React',
                'vue': 'Vue.js',
                'angular': 'Angular',
                'node': 'Node.js',
                'nodejs': 'Node.js',
                'basico': 'Básico',
                'básico': 'Básico',
                'avancado': 'Avançado',
                'avançado': 'Avançado',
                'intermediario': 'Intermediário',
                'intermediário': 'Intermediário',
                'fundamentos': 'Fundamentos',
                'conceitos': 'Conceitos',
                'introducao': 'Introdução',
                'introdução': 'Introdução'
            }
            
            improved = topic.lower()
            for wrong, correct in corrections.items():
                improved = improved.replace(wrong, correct)
            
            # Capitalizar primeira letra de cada palavra importante
            words = improved.split()
            capitalized_words = []
            for word in words:
                if word.lower() in ['de', 'da', 'do', 'das', 'dos', 'e', 'para', 'com', 'em', 'na', 'no']:
                    capitalized_words.append(word.lower())
                else:
                    capitalized_words.append(word.capitalize())
            
            return ' '.join(capitalized_words)
        
        # Aplicar correções básicas
        improved_topic = improve_title_simple(request.topic)
        
        # Tentar usar LLM para melhorias adicionais
        try:
            if gemini_client:  # Verificar se cliente existe
                improved_title_prompt = f"""Melhore este título de curso: "{improved_topic}"

Regras:
- Mantenha conciso (máximo 40 caracteres)
- Use termos técnicos corretos
- Não inclua nível de dificuldade

Responda APENAS o título melhorado:"""
                
                llm_result = await gemini_client.generate_content(improved_title_prompt)
                if llm_result and len(llm_result.strip()) > 0:
                    clean_title = llm_result.strip().replace('"', '').replace("'", "")
                    if len(clean_title) <= 50:  # Verificar tamanho razoável
                        improved_topic = clean_title
                        print(f"Título melhorado pela LLM: {improved_topic}")
        except Exception as e:
            print(f"LLM não disponível, usando correções básicas: {e}")
        
        trilha_title = f"{improved_topic} - {difficulty_labels.get(request.difficulty, 'Básico')}"
        print(f"Título final: {trilha_title}")
        
        import random
        trilha_id = random.randint(1000, 9999)  # ID único
        
        # Criar módulos mock
        modules = []
        for i in range(modules_count.get(request.difficulty, 3)):
            module = {
                "id": 100 + i,
                "titulo": f"Módulo {i+1}: {request.topic}",
                "descricao": f"Aprenda os conceitos do módulo {i+1}",
                "ordem": i + 1,
                "questions_count": 10
            }
            modules.append(module)
        
        # Simular criação da trilha
        trilha_data = {
            "id": trilha_id,
            "titulo": trilha_title,
            "descricao": f"Trilha personalizada sobre {request.topic} para nível {request.difficulty}",
            "dificuldade": request.difficulty,
            "categoria": "programming",
            "modules": modules,
            "estimated_duration": len(modules) * 30,
            "total_questions": len(modules) * 10,
            "enrollment": {
                "success": True,
                "enrollment_id": 888,
                "enrolled_at": "2024-01-01T00:00:00Z"
            }
        }
        
        # Adicionar ao cache de trilhas criadas (para aparecer na lista)
        global created_trilhas_cache
        trilha_for_list = {
            "id": trilha_id,
            "titulo": trilha_title,
            "descricao": f"Trilha personalizada sobre {request.topic} para nível {request.difficulty}",
            "dificuldade": request.difficulty,
            "categoria": "programming",
            "modules_count": len(modules),
            "enrollment_count": 1,
            "completion_rate": 0,
            "created_at": current_time
        }
        created_trilhas_cache.append(trilha_for_list)
        
        return APIResponse(
            success=True,
            message="Trilha personalizada criada com sucesso!",
            data=trilha_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/user/{user_id}/check-active", response_model=APIResponse)
async def check_user_active_trilhas(user_id: int):
    """
    Verificar se o usuário tem trilhas ativas.
    
    - **user_id**: ID do usuário
    
    Retorna informação sobre trilhas ativas do usuário para decidir se deve
    mostrar opção "criar nova trilha" ou "continuar trilha existente".
    """
    try:
        # Por enquanto, retornar dados mock para testar a interface
        # TODO: Implementar integração completa com Lua quando o bridge estiver pronto
        
        # Simular verificação de trilhas ativas
        result = {
            "success": True,
            "has_active_trilhas": True,  # Mudando para true para mostrar ambos os botões
            "active_trilhas": [
                {
                    "id": 999,
                    "titulo": "Python básico - Fundamentos",
                    "progress": 0
                }
            ],
            "count": 1
        }
        
        return APIResponse(
            success=True,
            data=result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/trilha/{trilha_id}/details", response_model=APIResponse)
async def get_trilha_details(trilha_id: int):
    """
    Get detailed information about a specific trilha.
    """
    try:
        # Por enquanto, buscar na lista de trilhas criadas
        global created_trilhas_cache
        
        # Buscar nas trilhas base + cache
        import time
        current_time = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        trilhas_base = [
            {
                "id": 999,
                "titulo": "Python básico - Fundamentos",
                "descricao": "Trilha personalizada sobre Python básico para nível iniciante",
                "dificuldade": "beginner",
                "categoria": "programming",
                "modules_count": 3,
                "enrollment_count": 1,
                "completion_rate": 0,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 998,
                "titulo": "JavaScript avançado - Avançado",
                "descricao": "Trilha personalizada sobre JavaScript avançado para nível avançado",
                "dificuldade": "advanced",
                "categoria": "programming",
                "modules_count": 5,
                "enrollment_count": 1,
                "completion_rate": 20,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 997,
                "titulo": "Trilha Recém-Criada - Fundamentos",
                "descricao": "Esta trilha foi criada recentemente para demonstrar a funcionalidade",
                "dificuldade": "beginner",
                "categoria": "programming",
                "modules_count": 3,
                "enrollment_count": 1,
                "completion_rate": 0,
                "created_at": current_time
            }
        ]
        
        # Filtrar trilhas excluídas
        global deleted_trilhas_ids
        available_base_trilhas = [trilha for trilha in trilhas_base if trilha["id"] not in deleted_trilhas_ids]
        all_trilhas = available_base_trilhas + created_trilhas_cache
        
        # Buscar trilha específica
        trilha = next((t for t in all_trilhas if t["id"] == trilha_id), None)
        
        if not trilha:
            raise HTTPException(status_code=404, detail="Trilha não encontrada")
        
        # Gerar módulos detalhados para a trilha
        modules = []
        for i in range(trilha["modules_count"]):
            module = {
                "id": trilha_id * 100 + i + 1,
                "titulo": f"Módulo {i+1}: {trilha['titulo'].split(' - ')[0]}",
                "descricao": f"Aprenda os conceitos fundamentais do módulo {i+1}",
                "ordem": i + 1,
                "questions_count": 10,
                "estimated_duration": 15
            }
            modules.append(module)
        
        # Dados detalhados da trilha
        detailed_trilha = {
            **trilha,
            "modules": modules,
            "estimated_duration": len(modules) * 15,
            "total_questions": len(modules) * 10,
            "enrollment": {
                "enrollment_count": trilha.get("enrollment_count", 0),
                "completion_rate": trilha.get("completion_rate", 0)
            }
        }
        
        return APIResponse(
            success=True,
            message="Detalhes da trilha carregados com sucesso",
            data=detailed_trilha
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting trilha details: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.delete("/trilha/{trilha_id}/delete", response_model=APIResponse)
async def delete_trilha(trilha_id: int):
    """
    Delete a specific trilha.
    """
    try:
        # Por enquanto, remover da lista de trilhas criadas
        global created_trilhas_cache
        
        # Buscar trilha no cache
        trilha_found = False
        for i, trilha in enumerate(created_trilhas_cache):
            if trilha["id"] == trilha_id:
                created_trilhas_cache.pop(i)
                trilha_found = True
                break
        
        if not trilha_found:
            # Verificar se é uma trilha base ou extra
            base_trilha_ids = [999, 998, 997]
            extra_trilha_ids = [990, 991, 992, 993, 994]  # IDs das trilhas extras
            all_system_trilhas = base_trilha_ids + extra_trilha_ids
            
            if trilha_id in all_system_trilhas:
                # Permitir exclusão de trilhas do sistema - adicionar à lista de excluídas
                global deleted_trilhas_ids
                if trilha_id not in deleted_trilhas_ids:
                    deleted_trilhas_ids.append(trilha_id)
                print(f"Trilha do sistema {trilha_id} foi marcada como excluída")
                trilha_found = True
            else:
                raise HTTPException(
                    status_code=404, 
                    detail="Trilha não encontrada"
                )
        
        return APIResponse(
            success=True,
            message="Trilha excluída com sucesso",
            data={"trilha_id": trilha_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting trilha: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/user/{user_id}/created", response_model=APIResponse)
async def get_user_created_trilhas(user_id: int):
    """
    Obter trilhas criadas pelo usuário.
    
    - **user_id**: ID do usuário
    
    Retorna todas as trilhas personalizadas criadas pelo usuário.
    """
    try:
        # Por enquanto, retornar trilhas mock para testar a interface
        # TODO: Implementar busca real no banco de dados
        
        # Simular trilhas base + trilhas criadas dinamicamente
        import time
        import random
        current_time = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Trilhas base (sempre presentes)
        trilhas_base = [
            {
                "id": 999,
                "titulo": "Python básico - Fundamentos",
                "descricao": "Trilha personalizada sobre Python básico para nível iniciante",
                "dificuldade": "beginner",
                "categoria": "programming",
                "modules_count": 3,
                "enrollment_count": 1,
                "completion_rate": 0,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 998,
                "titulo": "JavaScript avançado - Avançado",
                "descricao": "Trilha personalizada sobre JavaScript avançado para nível avançado",
                "dificuldade": "advanced",
                "categoria": "programming",
                "modules_count": 5,
                "enrollment_count": 1,
                "completion_rate": 20,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 997,
                "titulo": "Trilha Recém-Criada - Fundamentos",
                "descricao": "Esta trilha foi criada recentemente para demonstrar a funcionalidade",
                "dificuldade": "beginner",
                "categoria": "programming",
                "modules_count": 3,
                "enrollment_count": 1,
                "completion_rate": 0,
                "created_at": current_time
            }
        ]
        
        # Simular trilhas criadas recentemente (baseado no timestamp para variar)
        import hashlib
        user_seed = str(user_id) + str(int(time.time() // 300))  # Muda a cada 5 minutos
        hash_obj = hashlib.md5(user_seed.encode())
        random.seed(int(hash_obj.hexdigest()[:8], 16))
        
        trilhas_extras = []
        num_extras = random.randint(0, 3)  # 0 a 3 trilhas extras
        
        temas_exemplo = [
            ("React Hooks", "intermediario", "web_development"),
            ("Machine Learning", "avancado", "data_science"),
            ("Node.js APIs", "intermediario", "programming"),
            ("CSS Grid", "iniciante", "web_development"),
            ("Docker Básico", "intermediario", "devops"),
            ("Vue.js", "iniciante", "web_development")
        ]
        
        for i in range(num_extras):
            if i < len(temas_exemplo):
                tema, dif, cat = temas_exemplo[i]
                difficulty_labels = {
                    "iniciante": "Fundamentos",
                    "intermediario": "Intermediário",
                    "avancado": "Avançado"
                }
                modules_count = {"iniciante": 3, "intermediario": 4, "avancado": 5}
                
                trilha_extra = {
                    "id": 990 + i,
                    "titulo": f"{tema} - {difficulty_labels[dif]}",
                    "descricao": f"Trilha personalizada sobre {tema} para nível {dif}",
                    "dificuldade": dif,
                    "categoria": cat,
                    "modules_count": modules_count[dif],
                    "enrollment_count": 1,
                    "completion_rate": random.randint(0, 30),
                    "created_at": current_time
                }
                trilhas_extras.append(trilha_extra)
        
        # Combinar trilhas base + extras + trilhas criadas dinamicamente
        global created_trilhas_cache, deleted_trilhas_ids
        all_trilhas = trilhas_base + trilhas_extras + created_trilhas_cache
        
        # Filtrar trilhas excluídas
        trilhas_mock = [trilha for trilha in all_trilhas if trilha["id"] not in deleted_trilhas_ids]
        
        result = {
            "success": True,
            "trilhas": trilhas_mock,
            "total": len(trilhas_mock)
        }
        
        return APIResponse(
            success=True,
            data=result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/quiz/start", response_model=APIResponse)
async def start_quiz_session(request: QuizSessionRequest):
    """
    Iniciar uma sessão de quiz para um módulo.
    
    - **user_id**: ID do usuário
    - **module_id**: ID do módulo/conteúdo
    
    Inicia uma nova sessão de quiz ou retoma uma sessão existente.
    """
    try:
        lua_engine = get_lua_engine()
        
        result = lua_engine.lua.eval("""
            local quiz_manager = require('lua_core.business.quiz_manager')
            return quiz_manager.start_quiz_session
        """)(request.user_id, request.module_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to start quiz session")
            )
        
        return APIResponse(
            success=True,
            message=result.get("message", "Quiz session started"),
            data=result["session"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/quiz/session/{session_id}/question", response_model=APIResponse)
async def get_current_question(session_id: int, user_id: int):
    """
    Obter a questão atual de uma sessão de quiz.
    
    - **session_id**: ID da sessão de quiz
    - **user_id**: ID do usuário (para verificação de autorização)
    
    Retorna a questão atual e informações da sessão.
    """
    try:
        lua_engine = get_lua_engine()
        
        result = lua_engine.lua.eval("""
            local quiz_manager = require('lua_core.business.quiz_manager')
            return quiz_manager.get_current_question
        """)(session_id, user_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to get current question")
            )
        
        return APIResponse(
            success=True,
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/quiz/session/{session_id}/answer", response_model=APIResponse)
async def submit_quiz_answer(session_id: int, request: QuizAnswerRequest):
    """
    Submeter resposta para uma questão do quiz.
    
    - **session_id**: ID da sessão de quiz
    - **user_id**: ID do usuário
    - **question_id**: ID da questão
    - **selected_answer**: Resposta selecionada (a, b, c, d, e)
    
    Processa a resposta e retorna se está correta, explicação e próximos passos.
    """
    try:
        lua_engine = get_lua_engine()
        
        answer_data = {
            "user_id": request.user_id,
            "question_id": request.question_id,
            "selected_answer": request.selected_answer
        }
        
        result = lua_engine.lua.eval("""
            local quiz_manager = require('lua_core.business.quiz_manager')
            return quiz_manager.submit_answer
        """)(session_id, request.user_id, answer_data)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to submit answer")
            )
        
        return APIResponse(
            success=True,
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/quiz/session/{session_id}/results", response_model=APIResponse)
async def get_quiz_results(session_id: int, user_id: int):
    """
    Obter resultados finais de uma sessão de quiz completada.
    
    - **session_id**: ID da sessão de quiz
    - **user_id**: ID do usuário
    
    Retorna estatísticas completas do quiz: acertos, erros, tempo, nota.
    """
    try:
        lua_engine = get_lua_engine()
        
        result = lua_engine.lua.eval("""
            local quiz_manager = require('lua_core.business.quiz_manager')
            return quiz_manager.get_quiz_results
        """)(session_id, user_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to get quiz results")
            )
        
        return APIResponse(
            success=True,
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/quiz/user/{user_id}/history", response_model=APIResponse)
async def get_user_quiz_history(user_id: int, limit: int = 10):
    """
    Obter histórico de quizzes do usuário.
    
    - **user_id**: ID do usuário
    - **limit**: Número máximo de sessões a retornar (padrão: 10)
    
    Retorna histórico de sessões de quiz com resultados.
    """
    try:
        lua_engine = get_lua_engine()
        
        result = lua_engine.lua.eval("""
            local quiz_manager = require('lua_core.business.quiz_manager')
            return quiz_manager.get_user_quiz_history
        """)(user_id, limit)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to get quiz history")
            )
        
        return APIResponse(
            success=True,
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

def create_default_questions(topic: str, module_title: str) -> List[dict]:
    """
    Criar questões padrão caso a IA falhe.
    
    Args:
        topic: Tópico da trilha
        module_title: Título do módulo
        
    Returns:
        Lista de questões padrão
    """
    default_questions = []
    
    for i in range(1, 11):  # 10 questões
        question = {
            "pergunta": f"Questão {i} sobre {module_title} relacionada a {topic}",
            "alternativas": {
                "a": f"Primeira opção sobre {topic}",
                "b": f"Segunda opção sobre {topic}",
                "c": f"Terceira opção sobre {topic}",
                "d": f"Quarta opção sobre {topic}",
                "e": f"Quinta opção sobre {topic}"
            },
            "resposta_correta": "a",
            "explicacao": f"Esta é a explicação para a questão {i} sobre {module_title}."
        }
        default_questions.append(question)
    
    return default_questions
