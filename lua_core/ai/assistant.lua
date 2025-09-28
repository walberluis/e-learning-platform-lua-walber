-- AI Assistant Module (Lua)
-- Handles intelligent chatbot and recommendation features

local json = require("json")
local db = require("lua_core.data.database")
local utils = require("lua_core.utils.helpers")

local assistant = {}

-- Intent patterns for message analysis
local intent_patterns = {
    recommendation = {
        "recommend", "suggest", "what should", "help me find", "preciso de", "me ajude",
        "recomende", "sugira", "o que devo", "que curso"
    },
    progress = {
        "progress", "how am i doing", "my performance", "stats", "progresso",
        "como estou", "meu desempenho", "estatisticas", "como vou"
    },
    help = {
        "help", "how to", "explain", "what is", "ajuda", "como fazer",
        "explique", "o que é", "como funciona"
    },
    greeting = {
        "hello", "hi", "hey", "good morning", "good afternoon", "ola", "oi",
        "olá", "bom dia", "boa tarde", "boa noite"
    },
    course_info = {
        "course", "trilha", "content", "material", "curso", "conteudo",
        "materia", "aula", "licao"
    },
    completion = {
        "complete", "finish", "done", "completed", "completei", "terminei",
        "finalizei", "acabei", "concluí"
    }
}

-- Learning topics for keyword extraction
local learning_topics = {
    "python", "javascript", "java", "programming", "web development",
    "data science", "machine learning", "ai", "database", "sql",
    "react", "angular", "vue", "nodejs", "backend", "frontend",
    "programacao", "desenvolvimento web", "ciencia de dados",
    "aprendizado de maquina", "banco de dados", "inteligencia artificial"
}

-- Response templates
local response_templates = {
    recommendation = "Olá {user_name}! Ficarei feliz em recomendar conteúdo de aprendizado para você.",
    progress = "Vou verificar seu progresso de aprendizado, {user_name}.",
    help = "Estou aqui para ajudá-lo, {user_name}! Deixe-me explicar isso para você.",
    greeting = "Olá {user_name}! Como posso ajudá-lo com seus estudos hoje?",
    course_info = "Posso fornecer informações sobre cursos e materiais de aprendizado, {user_name}.",
    completion = "Parabéns pelo seu progresso, {user_name}! Deixe-me ajudá-lo com os próximos passos.",
    general = "Entendo, {user_name}. Deixe-me ajudá-lo com isso."
}

-- Initialize AI assistant
function assistant.init()
    print("🤖 Initializing AI Assistant...")
    -- Load any necessary models or configurations
    print("✅ AI Assistant initialized")
end

-- Analyze user message intent
function assistant.analyze_intent(message)
    local message_lower = string.lower(message)
    
    for intent, patterns in pairs(intent_patterns) do
        for _, pattern in ipairs(patterns) do
            if string.find(message_lower, pattern, 1, true) then
                return intent
            end
        end
    end
    
    return "general"
end

-- Extract keywords from message
function assistant.extract_keywords(message)
    local keywords = {}
    local message_lower = string.lower(message)
    
    for _, topic in ipairs(learning_topics) do
        if string.find(message_lower, topic, 1, true) then
            table.insert(keywords, topic)
        end
    end
    
    return keywords
end

-- Generate response template
function assistant.generate_response_template(intent, user_name)
    local template = response_templates[intent] or response_templates.general
    return string.gsub(template, "{user_name}", user_name or "Estudante")
end

-- Calculate response confidence
function assistant.calculate_confidence(intent, keywords_count, user_context)
    local base_confidence = 0.7
    
    -- Increase confidence based on clear intent
    if intent ~= "general" then
        base_confidence = base_confidence + 0.1
    end
    
    -- Increase confidence based on keywords found
    if keywords_count > 0 then
        base_confidence = base_confidence + (keywords_count * 0.05)
    end
    
    -- Increase confidence if user context is available
    if user_context and user_context.learning_level then
        base_confidence = base_confidence + 0.1
    end
    
    return math.min(base_confidence, 1.0)
end

-- Process user message
function assistant.process_message(user_id, message, context)
    context = context or {}
    
    -- Get user information
    local user_result = db.find_user_by_id(user_id)
    if not user_result then
        return {
            success = false,
            error = "User not found"
        }
    end
    
    local user = user_result
    
    -- Analyze message
    local intent = assistant.analyze_intent(message)
    local keywords = assistant.extract_keywords(message)
    local keywords_count = #keywords
    
    -- Generate response template
    local response_template = assistant.generate_response_template(intent, user.name)
    
    -- Calculate confidence
    local user_context = {learning_level = user.learning_profile}
    local confidence = assistant.calculate_confidence(intent, keywords_count, user_context)
    
    -- Generate detailed response based on intent
    local detailed_response = assistant.generate_intent_response(user_id, intent, keywords, message, context)
    
    -- Combine template with detailed response
    local full_response = response_template .. "\n\n" .. detailed_response
    
    -- Store conversation history
    assistant.store_conversation(user_id, message, full_response, intent)
    
    return {
        success = true,
        response = full_response,
        metadata = {
            intent = intent,
            keywords = keywords,
            confidence = confidence,
            user_name = user.name,
            timestamp = os.time()
        }
    }
end

-- Generate detailed response based on intent
function assistant.generate_intent_response(user_id, intent, keywords, original_message, context)
    if intent == "recommendation" then
        return assistant.handle_recommendation_request(user_id, keywords)
    elseif intent == "progress" then
        return assistant.handle_progress_request(user_id)
    elseif intent == "help" then
        return assistant.handle_help_request(keywords, original_message)
    elseif intent == "greeting" then
        return assistant.handle_greeting(user_id)
    elseif intent == "course_info" then
        return assistant.handle_course_info_request(keywords)
    elseif intent == "completion" then
        return assistant.handle_completion_request(user_id)
    else
        return assistant.handle_general_request(user_id, original_message, context)
    end
end

-- Handle recommendation requests
function assistant.handle_recommendation_request(user_id, keywords)
    -- Get course recommendations
    local course_manager = require("lua_core.business.course_manager")
    local recommendations = course_manager.get_recommendations(user_id, 3)
    
    if not recommendations.success then
        return "Estou com dificuldades para gerar recomendações agora. Tente novamente mais tarde."
    end
    
    local response = "Aqui estão minhas recomendações personalizadas para você:\n\n"
    
    local courses = recommendations.data
    for i, course in ipairs(courses) do
        response = response .. string.format("%d. 📚 **%s**\n", i, course.titulo)
        response = response .. string.format("   🎯 Dificuldade: %s\n", course.dificuldade)
        response = response .. string.format("   📖 Perfeito para seu nível de aprendizado!\n\n")
    end
    
    if #courses == 0 then
        response = "No momento não tenho recomendações específicas, mas posso ajudá-lo a encontrar cursos interessantes!"
    end
    
    return response
end

-- Handle progress requests
function assistant.handle_progress_request(user_id)
    local stats = db.get_user_learning_stats(user_id)
    
    if not stats then
        return "Ainda não tenho dados suficientes sobre seu progresso. Comece a estudar algum conteúdo e poderei acompanhar seu progresso!"
    end
    
    local response = "📊 **Seu Progresso de Aprendizado:**\n\n"
    response = response .. string.format("🎯 Taxa de Conclusão: %.1f%%\n", stats.completion_rate or 0)
    response = response .. string.format("📚 Atividades Totais: %d\n", stats.total_activities or 0)
    response = response .. string.format("⭐ Nota Média: %.1f/100\n", stats.average_grade or 0)
    response = response .. string.format("⏱️ Tempo Total de Estudo: %.1f horas\n", stats.total_study_time or 0)
    response = response .. string.format("🔥 Sequência de Aprendizado: %d dias\n\n", stats.learning_streak or 0)
    
    -- Add motivational message
    local completion_rate = stats.completion_rate or 0
    if completion_rate > 80 then
        response = response .. "🌟 Excelente trabalho! Você está indo muito bem com a conclusão do seu conteúdo de aprendizado!"
    elseif completion_rate > 60 then
        response = response .. "👍 Bom progresso! Tente completar mais conteúdo para aumentar sua eficácia de aprendizado."
    else
        response = response .. "💪 Continue assim! Foque em completar o conteúdo que você começou para melhores resultados de aprendizado."
    end
    
    return response
end

-- Handle help requests
function assistant.handle_help_request(keywords, original_message)
    local response = "📖 **Aqui está o que posso explicar:**\n\n"
    
    if #keywords > 0 then
        response = response .. "Encontrei informações relacionadas a: " .. table.concat(keywords, ", ") .. "\n\n"
    end
    
    -- Basic explanations for common topics
    local explanations = {
        python = "Python é uma linguagem de programação versátil e fácil de aprender, ideal para iniciantes.",
        javascript = "JavaScript é a linguagem da web, usada para criar interatividade em sites e aplicações.",
        ["machine learning"] = "Machine Learning é uma área da IA que permite aos computadores aprenderem com dados.",
        ["web development"] = "Desenvolvimento web envolve criar sites e aplicações que funcionam na internet."
    }
    
    for _, keyword in ipairs(keywords) do
        if explanations[keyword] then
            response = response .. "• **" .. keyword .. "**: " .. explanations[keyword] .. "\n"
        end
    end
    
    response = response .. "\nHá algo específico que você gostaria que eu elaborasse mais?"
    
    return response
end

-- Handle greeting messages
function assistant.handle_greeting(user_id)
    local greetings = {
        "Bem-vindo de volta! Pronto para continuar sua jornada de aprendizado?",
        "Ótimo te ver! O que você gostaria de aprender hoje?",
        "Olá! Estou aqui para ajudá-lo com seus objetivos de aprendizado.",
        "Oi! Vamos fazer de hoje um dia produtivo de aprendizado!"
    }
    
    local greeting = greetings[math.random(#greetings)]
    
    return greeting .. "\n\n💡 Posso ajudá-lo com:\n• Encontrar novos cursos\n• Acompanhar seu progresso\n• Responder perguntas\n• Fornecer recomendações"
end

-- Handle course info requests
function assistant.handle_course_info_request(keywords)
    local response = "📚 **Informações sobre Cursos:**\n\n"
    
    if #keywords > 0 then
        response = response .. "Encontrei informações relacionadas a: " .. table.concat(keywords, ", ") .. "\n\n"
    end
    
    response = response .. "Posso ajudá-lo a encontrar cursos em vários tópicos, incluindo:\n"
    response = response .. "• Programação (Python, JavaScript, Java)\n"
    response = response .. "• Desenvolvimento Web (React, Angular, Node.js)\n"
    response = response .. "• Ciência de Dados e IA\n"
    response = response .. "• Gerenciamento de Banco de Dados\n"
    response = response .. "• E muito mais!\n\n"
    response = response .. "Que tópico específico te interessa?"
    
    return response
end

-- Handle completion requests
function assistant.handle_completion_request(user_id)
    return "🎉 **Parabéns pelo seu progresso!**\n\nCompletar conteúdo de aprendizado é uma grande conquista! Aqui está o que você pode fazer a seguir:\n\n• Revisar o que você aprendeu\n• Aplicar seu conhecimento na prática\n• Avançar para tópicos mais avançados\n• Compartilhar sua conquista com outros\n\nGostaria que eu recomendasse seu próximo passo de aprendizado?"
end

-- Handle general requests
function assistant.handle_general_request(user_id, message, context)
    return "Entendo sua pergunta. Como assistente de aprendizado, posso ajudá-lo com recomendações de cursos, acompanhar seu progresso, explicar conceitos e fornecer orientações de estudo. Como posso ajudá-lo especificamente hoje?"
end

-- Store conversation history
function assistant.store_conversation(user_id, user_message, bot_response, intent)
    local conversation_entry = {
        user_id = user_id,
        user_message = user_message,
        bot_response = bot_response,
        intent = intent,
        timestamp = os.time()
    }
    
    db.store_conversation(conversation_entry)
end

-- Get conversation history
function assistant.get_conversation_history(user_id, limit)
    limit = limit or 10
    
    local history = db.get_conversation_history(user_id, limit)
    if not history then
        return {
            success = false,
            error = "Failed to retrieve conversation history"
        }
    end
    
    return {
        success = true,
        user_id = user_id,
        conversation_count = #history,
        history = history
    }
end

-- Clear conversation history
function assistant.clear_conversation_history(user_id)
    local success = db.clear_conversation_history(user_id)
    
    if not success then
        return {
            success = false,
            error = "Failed to clear conversation history"
        }
    end
    
    return {
        success = true,
        message = "Conversation history cleared"
    }
end

return assistant

