-- Quiz Manager Module (Lua)
-- Handles quiz creation, management, and user interactions

-- Note: json and db functionality will be handled by Python bridge
-- local json = require("json")
-- local db = require("lua_core.data.database")
-- local utils = require("lua_core.utils.helpers")

local quiz_manager = {}

-- Mock database functions (will be replaced by Python bridge)
local db = {
    get_conteudo_by_id = function(id) return {id = id, trilha_id = 1} end,
    get_module_questions = function(module_id) return {} end,
    get_active_quiz_session = function(user_id, module_id) return nil end,
    create_quiz_session = function(data) return 1 end,
    get_quiz_session = function(session_id) return {id = session_id, user_id = 1, module_id = 1, status = "started", started_at = os.time(), time_limit = 1800, current_question = 1, total_questions = 10, correct_answers = 0, wrong_answers = 0} end,
    create_quiz_answer = function(data) return 1 end,
    update_quiz_session = function(session_id, updates) return true end,
    get_user_content_performance = function(user_id, content_id) return nil end,
    create_desempenho = function(data) return 1 end,
    update_desempenho = function(id, data) return true end,
    get_trilha_modules = function(trilha_id) return {} end,
    update_user_trilha_enrollment = function(user_id, trilha_id, updates) return true end,
    get_session_answers = function(session_id) return {} end,
    get_user_quiz_sessions = function(user_id, limit) return {} end,
    get_trilha_by_id = function(trilha_id) return {id = trilha_id, titulo = "Test Trilha"} end
}

-- Quiz session states
local session_states = {
    STARTED = "started",
    IN_PROGRESS = "in_progress", 
    COMPLETED = "completed",
    ABANDONED = "abandoned"
}

-- Answer validation
function quiz_manager.validate_answer_data(answer_data)
    local errors = {}
    
    if not answer_data.user_id then
        table.insert(errors, "User ID is required")
    end
    
    if not answer_data.question_id then
        table.insert(errors, "Question ID is required")
    end
    
    if not answer_data.selected_answer then
        table.insert(errors, "Selected answer is required")
    elseif not string.match(answer_data.selected_answer, "^[abcde]$") then
        table.insert(errors, "Selected answer must be a, b, c, d, or e")
    end
    
    return #errors == 0, errors
end

-- Start a new quiz session
function quiz_manager.start_quiz_session(user_id, module_id)
    if not user_id or not module_id then
        return {
            success = false,
            error = "User ID and Module ID are required"
        }
    end
    
    -- Check if module exists and has questions
    local module = db.get_conteudo_by_id(module_id)
    if not module then
        return {
            success = false,
            error = "Module not found"
        }
    end
    
    -- Get questions for this module
    local questions = db.get_module_questions(module_id)
    if not questions or #questions == 0 then
        return {
            success = false,
            error = "No questions found for this module"
        }
    end
    
    -- Check if user has an active session for this module
    local existing_session = db.get_active_quiz_session(user_id, module_id)
    if existing_session then
        return {
            success = true,
            session = existing_session,
            message = "Resuming existing quiz session"
        }
    end
    
    -- Create new quiz session
    local session_data = {
        user_id = user_id,
        module_id = module_id,
        trilha_id = module.trilha_id,
        total_questions = #questions,
        current_question = 1,
        correct_answers = 0,
        wrong_answers = 0,
        status = session_states.STARTED,
        started_at = os.time(),
        time_limit = 30 * 60, -- 30 minutes
        created_at = os.time()
    }
    
    local session_id = db.create_quiz_session(session_data)
    if not session_id then
        return {
            success = false,
            error = "Failed to create quiz session"
        }
    end
    
    session_data.id = session_id
    session_data.questions = questions
    
    return {
        success = true,
        session = session_data,
        message = "Quiz session started successfully"
    }
end

-- Get current question for a quiz session
function quiz_manager.get_current_question(session_id, user_id)
    if not session_id or not user_id then
        return {
            success = false,
            error = "Session ID and User ID are required"
        }
    end
    
    -- Get session
    local session = db.get_quiz_session(session_id)
    if not session then
        return {
            success = false,
            error = "Quiz session not found"
        }
    end
    
    -- Verify user owns this session
    if session.user_id ~= user_id then
        return {
            success = false,
            error = "Unauthorized access to quiz session"
        }
    end
    
    -- Check if session is still active
    if session.status == session_states.COMPLETED then
        return {
            success = false,
            error = "Quiz session already completed"
        }
    end
    
    -- Check time limit
    local current_time = os.time()
    local elapsed_time = current_time - session.started_at
    if elapsed_time > session.time_limit then
        -- Auto-complete session due to timeout
        quiz_manager.complete_quiz_session(session_id, user_id, "timeout")
        return {
            success = false,
            error = "Quiz session timed out"
        }
    end
    
    -- Get questions for this session
    local questions = db.get_module_questions(session.module_id)
    if not questions or session.current_question > #questions then
        return {
            success = false,
            error = "No more questions available"
        }
    end
    
    local current_question = questions[session.current_question]
    
    -- Remove correct answer from response (security)
    local safe_question = {
        id = current_question.id,
        pergunta = current_question.pergunta,
        alternativas = current_question.alternativas,
        ordem = session.current_question,
        total = #questions
    }
    
    return {
        success = true,
        question = safe_question,
        session_info = {
            id = session.id,
            current_question = session.current_question,
            total_questions = session.total_questions,
            correct_answers = session.correct_answers,
            wrong_answers = session.wrong_answers,
            time_remaining = session.time_limit - elapsed_time
        }
    }
end

-- Submit answer for current question
function quiz_manager.submit_answer(session_id, user_id, answer_data)
    local is_valid, errors = quiz_manager.validate_answer_data(answer_data)
    if not is_valid then
        return {
            success = false,
            error = "Validation failed",
            details = errors
        }
    end
    
    -- Get session
    local session = db.get_quiz_session(session_id)
    if not session then
        return {
            success = false,
            error = "Quiz session not found"
        }
    end
    
    -- Verify user owns this session
    if session.user_id ~= user_id then
        return {
            success = false,
            error = "Unauthorized access to quiz session"
        }
    end
    
    -- Get current question
    local questions = db.get_module_questions(session.module_id)
    local current_question = questions[session.current_question]
    
    if not current_question then
        return {
            success = false,
            error = "Current question not found"
        }
    end
    
    -- Check if answer is correct
    local is_correct = current_question.resposta_correta == answer_data.selected_answer
    
    -- Record the answer
    local answer_record = {
        session_id = session_id,
        question_id = current_question.id,
        user_id = user_id,
        selected_answer = answer_data.selected_answer,
        correct_answer = current_question.resposta_correta,
        is_correct = is_correct,
        answered_at = os.time()
    }
    
    local answer_id = db.create_quiz_answer(answer_record)
    if not answer_id then
        return {
            success = false,
            error = "Failed to record answer"
        }
    end
    
    -- Update session statistics
    local session_updates = {
        current_question = session.current_question + 1,
        updated_at = os.time()
    }
    
    if is_correct then
        session_updates.correct_answers = session.correct_answers + 1
    else
        session_updates.wrong_answers = session.wrong_answers + 1
    end
    
    -- Check if this was the last question
    local is_last_question = session.current_question >= session.total_questions
    if is_last_question then
        session_updates.status = session_states.COMPLETED
        session_updates.completed_at = os.time()
    else
        session_updates.status = session_states.IN_PROGRESS
    end
    
    -- Update session
    local update_success = db.update_quiz_session(session_id, session_updates)
    if not update_success then
        return {
            success = false,
            error = "Failed to update quiz session"
        }
    end
    
    -- Prepare response
    local response = {
        success = true,
        answer_result = {
            is_correct = is_correct,
            correct_answer = current_question.resposta_correta,
            explanation = current_question.explicacao,
            selected_answer = answer_data.selected_answer
        },
        session_info = {
            current_question = session_updates.current_question,
            total_questions = session.total_questions,
            correct_answers = session_updates.correct_answers,
            wrong_answers = session_updates.wrong_answers,
            is_completed = is_last_question
        }
    }
    
    -- If quiz is completed, add final results
    if is_last_question then
        response.final_results = quiz_manager.calculate_quiz_results(session_id)
        
        -- Update user progress
        quiz_manager.update_user_progress(user_id, session.module_id, response.final_results)
    end
    
    return response
end

-- Calculate final quiz results
function quiz_manager.calculate_quiz_results(session_id)
    local session = db.get_quiz_session(session_id)
    if not session then
        return nil
    end
    
    local total_questions = session.total_questions
    local correct_answers = session.correct_answers
    local wrong_answers = session.wrong_answers
    local score_percentage = math.floor((correct_answers / total_questions) * 100)
    
    -- Calculate time taken
    local time_taken = session.completed_at - session.started_at
    local time_taken_minutes = math.floor(time_taken / 60)
    local time_taken_seconds = time_taken % 60
    
    -- Determine performance level
    local performance_level = "Precisa Melhorar"
    if score_percentage >= 90 then
        performance_level = "Excelente"
    elseif score_percentage >= 80 then
        performance_level = "Muito Bom"
    elseif score_percentage >= 70 then
        performance_level = "Bom"
    elseif score_percentage >= 60 then
        performance_level = "Regular"
    end
    
    return {
        total_questions = total_questions,
        correct_answers = correct_answers,
        wrong_answers = wrong_answers,
        score_percentage = score_percentage,
        performance_level = performance_level,
        time_taken_minutes = time_taken_minutes,
        time_taken_seconds = time_taken_seconds,
        time_taken_total = time_taken,
        completed_at = session.completed_at
    }
end

-- Update user progress based on quiz results
function quiz_manager.update_user_progress(user_id, module_id, quiz_results)
    if not user_id or not module_id or not quiz_results then
        return false
    end
    
    -- Get module information
    local module = db.get_conteudo_by_id(module_id)
    if not module then
        return false
    end
    
    -- Calculate progress percentage (100% if completed)
    local progress_percentage = 100
    
    -- Create or update performance record
    local performance_data = {
        usuario_id = user_id,
        conteudo_id = module_id,
        progresso = progress_percentage,
        nota = quiz_results.score_percentage,
        tempo_estudo = math.floor(quiz_results.time_taken_total / 60), -- Convert to minutes
        completed_at = quiz_results.completed_at,
        updated_at = os.time()
    }
    
    -- Check if performance record exists
    local existing_performance = db.get_user_content_performance(user_id, module_id)
    
    local success = false
    if existing_performance then
        -- Update existing record
        success = db.update_desempenho(existing_performance.id, performance_data)
    else
        -- Create new record
        performance_data.created_at = os.time()
        local performance_id = db.create_desempenho(performance_data)
        success = performance_id ~= nil
    end
    
    -- Update trilha progress if this module completion affects it
    if success then
        quiz_manager.update_trilha_progress(user_id, module.trilha_id)
    end
    
    return success
end

-- Update overall trilha progress
function quiz_manager.update_trilha_progress(user_id, trilha_id)
    if not user_id or not trilha_id then
        return false
    end
    
    -- Get all modules in this trilha
    local trilha_modules = db.get_trilha_modules(trilha_id)
    if not trilha_modules then
        return false
    end
    
    -- Count completed modules
    local completed_modules = 0
    local total_score = 0
    local total_study_time = 0
    
    for _, module in ipairs(trilha_modules) do
        local performance = db.get_user_content_performance(user_id, module.id)
        if performance and performance.progresso >= 100 then
            completed_modules = completed_modules + 1
            total_score = total_score + (performance.nota or 0)
            total_study_time = total_study_time + (performance.tempo_estudo or 0)
        end
    end
    
    -- Calculate trilha completion percentage
    local completion_percentage = math.floor((completed_modules / #trilha_modules) * 100)
    local average_score = completed_modules > 0 and math.floor(total_score / completed_modules) or 0
    
    -- Update user-trilha enrollment record
    local enrollment_updates = {
        progress = completion_percentage,
        average_score = average_score,
        total_study_time = total_study_time,
        completed_modules = completed_modules,
        updated_at = os.time()
    }
    
    -- Mark as completed if all modules are done
    if completion_percentage >= 100 then
        enrollment_updates.status = "completed"
        enrollment_updates.completed_at = os.time()
    end
    
    return db.update_user_trilha_enrollment(user_id, trilha_id, enrollment_updates)
end

-- Get quiz session results
function quiz_manager.get_quiz_results(session_id, user_id)
    if not session_id or not user_id then
        return {
            success = false,
            error = "Session ID and User ID are required"
        }
    end
    
    local session = db.get_quiz_session(session_id)
    if not session then
        return {
            success = false,
            error = "Quiz session not found"
        }
    end
    
    if session.user_id ~= user_id then
        return {
            success = false,
            error = "Unauthorized access to quiz session"
        }
    end
    
    if session.status ~= session_states.COMPLETED then
        return {
            success = false,
            error = "Quiz session not completed yet"
        }
    end
    
    local results = quiz_manager.calculate_quiz_results(session_id)
    local answers = db.get_session_answers(session_id)
    
    return {
        success = true,
        results = results,
        answers = answers,
        session = session
    }
end

-- Complete quiz session (for timeout or abandonment)
function quiz_manager.complete_quiz_session(session_id, user_id, reason)
    reason = reason or "manual"
    
    local session_updates = {
        status = reason == "timeout" and "abandoned" or session_states.COMPLETED,
        completed_at = os.time(),
        updated_at = os.time()
    }
    
    return db.update_quiz_session(session_id, session_updates)
end

-- Get user's quiz history
function quiz_manager.get_user_quiz_history(user_id, limit)
    limit = limit or 10
    
    if not user_id then
        return {
            success = false,
            error = "User ID is required"
        }
    end
    
    local sessions = db.get_user_quiz_sessions(user_id, limit)
    if not sessions then
        return {
            success = false,
            error = "Failed to retrieve quiz history"
        }
    end
    
    -- Enrich sessions with additional information
    for _, session in ipairs(sessions) do
        if session.status == session_states.COMPLETED then
            session.results = quiz_manager.calculate_quiz_results(session.id)
        end
        
        -- Get module and trilha information
        local module = db.get_conteudo_by_id(session.module_id)
        if module then
            session.module_title = module.titulo
            local trilha = db.get_trilha_by_id(module.trilha_id)
            if trilha then
                session.trilha_title = trilha.titulo
            end
        end
    end
    
    return {
        success = true,
        sessions = sessions,
        total = #sessions
    }
end

return quiz_manager
