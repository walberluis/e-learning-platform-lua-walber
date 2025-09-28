-- Trilha Generator Module (Lua)
-- Handles creation and management of personalized learning paths with AI-generated content

-- Note: json and db functionality will be handled by Python bridge
-- local json = require("json")
-- local db = require("lua_core.data.database")
-- local utils = require("lua_core.utils.helpers")

local trilha_generator = {}

-- Mock database functions (will be replaced by Python bridge)
local db = {
    create_trilha = function(data) return 1 end,
    create_conteudo = function(data) return 1 end,
    create_user_trilha_enrollment = function(data) return 1 end,
    get_user_created_trilhas = function(user_id) return {} end,
    get_user_active_trilhas = function(user_id) return {} end,
    count_trilha_modules = function(trilha_id) return 0 end,
    count_trilha_enrollments = function(trilha_id) return 0 end,
    get_trilha_completion_rate = function(trilha_id) return 0 end
}

-- Mock utils functions
local utils = {
    capitalize_first_letter = function(str)
        return str:sub(1,1):upper() .. str:sub(2)
    end
}

-- Difficulty levels mapping
local difficulty_levels = {
    iniciante = "beginner",
    intermediario = "intermediate", 
    avancado = "advanced"
}

-- Subject categories for better content organization
local subject_categories = {
    programacao = "programming",
    web_development = "web_development",
    data_science = "data_science",
    machine_learning = "machine_learning",
    mobile_development = "mobile_development",
    devops = "devops",
    design = "design",
    business = "business",
    languages = "languages",
    mathematics = "mathematics"
}

-- Validate trilha creation request
function trilha_generator.validate_trilha_request(request_data)
    local errors = {}
    
    -- Validate user_id
    if not request_data.user_id then
        table.insert(errors, "User ID is required")
    end
    
    -- Validate topic
    if not request_data.topic then
        table.insert(errors, "Learning topic is required")
    elseif #request_data.topic < 5 then
        table.insert(errors, "Topic description too short (minimum 5 characters)")
    elseif #request_data.topic > 500 then
        table.insert(errors, "Topic description too long (maximum 500 characters)")
    end
    
    -- Validate difficulty level
    if not request_data.difficulty then
        table.insert(errors, "Difficulty level is required")
    elseif not difficulty_levels[request_data.difficulty] then
        table.insert(errors, "Invalid difficulty level. Must be: iniciante, intermediario, or avancado")
    end
    
    return #errors == 0, errors
end

-- Generate trilha structure based on user input
function trilha_generator.generate_trilha_structure(request_data)
    local is_valid, errors = trilha_generator.validate_trilha_request(request_data)
    if not is_valid then
        return {
            success = false,
            error = "Validation failed",
            details = errors
        }
    end
    
    -- Create base trilha structure
    local trilha_data = {
        titulo = trilha_generator.generate_trilha_title(request_data.topic, request_data.difficulty),
        descricao = trilha_generator.generate_trilha_description(request_data.topic, request_data.difficulty),
        dificuldade = difficulty_levels[request_data.difficulty],
        categoria = trilha_generator.detect_category(request_data.topic),
        user_id = request_data.user_id,
        topic_request = request_data.topic,
        is_ai_generated = true,
        created_at = os.time(),
        updated_at = os.time()
    }
    
    -- Generate learning modules structure
    local modules = trilha_generator.generate_learning_modules(request_data.topic, request_data.difficulty)
    
    return {
        success = true,
        trilha_data = trilha_data,
        modules = modules,
        estimated_duration = trilha_generator.calculate_estimated_duration(modules),
        total_questions = #modules * 10 -- Each module will have 10 questions
    }
end

-- Generate trilha title based on topic and difficulty
function trilha_generator.generate_trilha_title(topic, difficulty)
    local difficulty_labels = {
        iniciante = "Fundamentos",
        intermediario = "Intermediário",
        avancado = "Avançado"
    }
    
    -- Clean and capitalize topic
    local clean_topic = utils.capitalize_first_letter(topic)
    local difficulty_label = difficulty_labels[difficulty] or "Básico"
    
    return string.format("%s - %s", clean_topic, difficulty_label)
end

-- Generate trilha description
function trilha_generator.generate_trilha_description(topic, difficulty)
    local templates = {
        iniciante = "Aprenda os conceitos fundamentais de %s de forma prática e estruturada. Esta trilha foi criada especialmente para iniciantes.",
        intermediario = "Aprofunde seus conhecimentos em %s com conteúdo intermediário e exercícios práticos desafiadores.",
        avancado = "Domine %s com conteúdo avançado, técnicas especializadas e projetos complexos."
    }
    
    local template = templates[difficulty] or templates.iniciante
    return string.format(template, topic)
end

-- Detect category based on topic keywords
function trilha_generator.detect_category(topic)
    local topic_lower = string.lower(topic)
    
    -- Programming keywords
    if string.find(topic_lower, "python") or string.find(topic_lower, "javascript") or 
       string.find(topic_lower, "java") or string.find(topic_lower, "programação") or
       string.find(topic_lower, "código") or string.find(topic_lower, "algoritmo") then
        return "programming"
    end
    
    -- Web development keywords
    if string.find(topic_lower, "web") or string.find(topic_lower, "html") or 
       string.find(topic_lower, "css") or string.find(topic_lower, "react") or
       string.find(topic_lower, "frontend") or string.find(topic_lower, "backend") then
        return "web_development"
    end
    
    -- Data science keywords
    if string.find(topic_lower, "dados") or string.find(topic_lower, "data") or 
       string.find(topic_lower, "análise") or string.find(topic_lower, "estatística") then
        return "data_science"
    end
    
    -- Machine learning keywords
    if string.find(topic_lower, "machine learning") or string.find(topic_lower, "ia") or 
       string.find(topic_lower, "inteligência artificial") or string.find(topic_lower, "ai") then
        return "machine_learning"
    end
    
    -- Default category
    return "programming"
end

-- Generate learning modules for the trilha
function trilha_generator.generate_learning_modules(topic, difficulty)
    local modules = {}
    local base_modules_count = {
        iniciante = 3,
        intermediario = 4,
        avancado = 5
    }
    
    local modules_count = base_modules_count[difficulty] or 3
    
    for i = 1, modules_count do
        local module = {
            ordem = i,
            titulo = trilha_generator.generate_module_title(topic, difficulty, i, modules_count),
            descricao = trilha_generator.generate_module_description(topic, difficulty, i),
            tipo = "quiz", -- All modules will be quiz-based
            duracao_estimada = 30, -- 30 minutes per module
            questions_count = 10,
            created_at = os.time()
        }
        table.insert(modules, module)
    end
    
    return modules
end

-- Generate module title
function trilha_generator.generate_module_title(topic, difficulty, module_number, total_modules)
    local templates = {
        iniciante = {
            "Introdução a %s",
            "Conceitos Básicos de %s", 
            "Primeiros Passos em %s"
        },
        intermediario = {
            "Fundamentos de %s",
            "Técnicas Intermediárias de %s",
            "Aplicações Práticas de %s",
            "Aprofundando em %s"
        },
        avancado = {
            "Conceitos Avançados de %s",
            "Técnicas Especializadas em %s",
            "Arquitetura e Design em %s",
            "Otimização e Performance em %s",
            "Projetos Complexos com %s"
        }
    }
    
    local difficulty_templates = templates[difficulty] or templates.iniciante
    local template_index = ((module_number - 1) % #difficulty_templates) + 1
    local template = difficulty_templates[template_index]
    
    return string.format(template, topic)
end

-- Generate module description
function trilha_generator.generate_module_description(topic, difficulty, module_number)
    local templates = {
        iniciante = "Módulo %d: Aprenda os conceitos essenciais através de questões práticas e exemplos simples.",
        intermediario = "Módulo %d: Teste seus conhecimentos com questões de nível intermediário e cenários reais.",
        avancado = "Módulo %d: Desafie-se com questões complexas e situações avançadas do mundo real."
    }
    
    local template = templates[difficulty] or templates.iniciante
    return string.format(template, module_number)
end

-- Calculate estimated duration for the entire trilha
function trilha_generator.calculate_estimated_duration(modules)
    local total_minutes = 0
    for _, module in ipairs(modules) do
        total_minutes = total_minutes + (module.duracao_estimada or 30)
    end
    return total_minutes
end

-- Create trilha in database
function trilha_generator.create_trilha_with_modules(trilha_structure)
    if not trilha_structure.success then
        return trilha_structure
    end
    
    -- Start transaction (mock - would be implemented in actual database layer)
    local transaction_success = true
    local trilha_id = nil
    local created_modules = {}
    
    -- Create trilha record
    trilha_id = db.create_trilha(trilha_structure.trilha_data)
    if not trilha_id then
        return {
            success = false,
            error = "Failed to create trilha in database"
        }
    end
    
    -- Create modules for the trilha
    for _, module_data in ipairs(trilha_structure.modules) do
        module_data.trilha_id = trilha_id
        local module_id = db.create_conteudo(module_data)
        
        if not module_id then
            transaction_success = false
            break
        end
        
        module_data.id = module_id
        table.insert(created_modules, module_data)
    end
    
    -- If transaction failed, cleanup (in real implementation)
    if not transaction_success then
        -- db.rollback_transaction()
        return {
            success = false,
            error = "Failed to create trilha modules"
        }
    end
    
    -- Auto-enroll user in the created trilha
    local enrollment_result = trilha_generator.enroll_user_in_trilha(trilha_structure.trilha_data.user_id, trilha_id)
    
    return {
        success = true,
        trilha = {
            id = trilha_id,
            titulo = trilha_structure.trilha_data.titulo,
            descricao = trilha_structure.trilha_data.descricao,
            dificuldade = trilha_structure.trilha_data.dificuldade,
            categoria = trilha_structure.trilha_data.categoria,
            modules = created_modules,
            estimated_duration = trilha_structure.estimated_duration,
            total_questions = trilha_structure.total_questions,
            enrollment = enrollment_result
        },
        message = "Trilha criada com sucesso!"
    }
end

-- Enroll user in trilha
function trilha_generator.enroll_user_in_trilha(user_id, trilha_id)
    local enrollment_data = {
        user_id = user_id,
        trilha_id = trilha_id,
        enrolled_at = os.time(),
        progress = 0,
        status = "active"
    }
    
    local enrollment_id = db.create_user_trilha_enrollment(enrollment_data)
    
    if enrollment_id then
        return {
            success = true,
            enrollment_id = enrollment_id,
            enrolled_at = enrollment_data.enrolled_at
        }
    else
        return {
            success = false,
            error = "Failed to enroll user in trilha"
        }
    end
end

-- Get user's created trilhas
function trilha_generator.get_user_created_trilhas(user_id)
    if not user_id then
        return {
            success = false,
            error = "User ID is required"
        }
    end
    
    local trilhas = db.get_user_created_trilhas(user_id)
    if not trilhas then
        return {
            success = false,
            error = "Failed to retrieve user trilhas"
        }
    end
    
    -- Enrich trilhas with additional information
    for _, trilha in ipairs(trilhas) do
        trilha.modules_count = db.count_trilha_modules(trilha.id) or 0
        trilha.enrollment_count = db.count_trilha_enrollments(trilha.id) or 0
        trilha.completion_rate = db.get_trilha_completion_rate(trilha.id) or 0
    end
    
    return {
        success = true,
        trilhas = trilhas,
        total = #trilhas
    }
end

-- Check if user has active trilhas
function trilha_generator.check_user_active_trilhas(user_id)
    if not user_id then
        return {
            success = false,
            error = "User ID is required"
        }
    end
    
    local active_trilhas = db.get_user_active_trilhas(user_id)
    local has_active = active_trilhas and #active_trilhas > 0
    
    return {
        success = true,
        has_active_trilhas = has_active,
        active_trilhas = active_trilhas or {},
        count = has_active and #active_trilhas or 0
    }
end

-- Generate AI prompt for trilha content creation
function trilha_generator.generate_ai_prompt_for_trilha(topic, difficulty, module_title)
    local difficulty_descriptions = {
        iniciante = "nível iniciante (conceitos básicos, exemplos simples)",
        intermediario = "nível intermediário (conceitos mais complexos, aplicações práticas)",
        avancado = "nível avançado (conceitos especializados, cenários complexos)"
    }
    
    local difficulty_desc = difficulty_descriptions[difficulty] or difficulty_descriptions.iniciante
    
    local prompt = string.format([[
Crie 10 questões de múltipla escolha sobre "%s" com foco em "%s" para %s.

Cada questão deve ter:
- Uma pergunta clara e objetiva
- 5 alternativas (a, b, c, d, e)
- Apenas uma resposta correta
- Explicação da resposta correta

Formato esperado para cada questão:
{
  "pergunta": "Texto da pergunta",
  "alternativas": {
    "a": "Primeira opção",
    "b": "Segunda opção", 
    "c": "Terceira opção",
    "d": "Quarta opção",
    "e": "Quinta opção"
  },
  "resposta_correta": "a",
  "explicacao": "Explicação detalhada da resposta correta"
}

Retorne um JSON válido com array de 10 questões.
]], topic, module_title, difficulty_desc)
    
    return prompt
end

return trilha_generator
