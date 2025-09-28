-- Database Module (Lua)
-- Handles all database operations and data persistence

local json = require("json")

local database = {}

-- Database connection (will be initialized from Python)
local db_connection = nil

-- Initialize database connection
function database.init()
    print("🗄️  Initializing database connection...")
    -- Database connection will be injected from Python side
    print("✅ Database connection ready")
end

-- Set database connection (called from Python)
function database.set_connection(connection)
    db_connection = connection
end

-- Execute SQL query (interface with Python)
local function execute_query(query, params)
    if not db_connection then
        error("Database connection not initialized")
    end
    
    -- This will be handled by Python bridge
    return db_connection.execute(query, params or {})
end

-- User operations
function database.create_user(user_data)
    local query = [[
        INSERT INTO usuarios (email, nome, senha, perfil_aprend, created_at, updated_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ]]
    
    local params = {
        user_data.email,
        user_data.name,
        user_data.password_hash,
        user_data.learning_profile,
        user_data.created_at,
        user_data.updated_at,
        user_data.is_active and 1 or 0
    }
    
    local result = execute_query(query, params)
    return result and result.lastrowid or nil
end

function database.find_user_by_email(email)
    local query = "SELECT * FROM usuarios WHERE email = ? AND is_active = 1"
    local result = execute_query(query, {email})
    return result and result.rows[1] or nil
end

function database.find_user_by_id(user_id)
    local query = "SELECT * FROM usuarios WHERE id = ? AND is_active = 1"
    local result = execute_query(query, {user_id})
    return result and result.rows[1] or nil
end

function database.update_user(user_id, updates)
    local set_clauses = {}
    local params = {}
    
    for field, value in pairs(updates) do
        table.insert(set_clauses, field .. " = ?")
        table.insert(params, value)
    end
    
    if #set_clauses == 0 then
        return false
    end
    
    local query = "UPDATE usuarios SET " .. table.concat(set_clauses, ", ") .. " WHERE id = ?"
    table.insert(params, user_id)
    
    local result = execute_query(query, params)
    return result and result.rowcount > 0
end

function database.update_user_last_login(user_id)
    local query = "UPDATE usuarios SET last_login = ? WHERE id = ?"
    local result = execute_query(query, {os.time(), user_id})
    return result and result.rowcount > 0
end

-- Course operations
function database.create_course(course_data)
    local query = [[
        INSERT INTO trilhas (titulo, descricao, dificuldade, categoria, duracao_estimada, 
                           pre_requisitos, objetivos, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ]]
    
    local params = {
        course_data.titulo,
        course_data.descricao,
        course_data.dificuldade,
        course_data.categoria,
        course_data.duracao_estimada,
        course_data.pre_requisitos,
        course_data.objetivos,
        course_data.is_active and 1 or 0,
        course_data.created_at,
        course_data.updated_at
    }
    
    local result = execute_query(query, params)
    return result and result.lastrowid or nil
end

function database.get_courses(filters)
    local query = "SELECT * FROM trilhas WHERE is_active = 1"
    local params = {}
    
    if filters.categoria then
        query = query .. " AND categoria = ?"
        table.insert(params, filters.categoria)
    end
    
    if filters.dificuldade then
        query = query .. " AND dificuldade = ?"
        table.insert(params, filters.dificuldade)
    end
    
    query = query .. " ORDER BY created_at DESC"
    
    if filters.limit then
        query = query .. " LIMIT ?"
        table.insert(params, filters.limit)
    end
    
    local result = execute_query(query, params)
    return result and result.rows or {}
end

function database.find_course_by_id(course_id)
    local query = "SELECT * FROM trilhas WHERE id = ? AND is_active = 1"
    local result = execute_query(query, {course_id})
    return result and result.rows[1] or nil
end

function database.search_courses(filters)
    local query = [[
        SELECT * FROM trilhas 
        WHERE is_active = 1 
        AND (titulo LIKE ? OR descricao LIKE ?)
    ]]
    local search_term = "%" .. filters.search_query .. "%"
    local params = {search_term, search_term}
    
    if filters.categoria then
        query = query .. " AND categoria = ?"
        table.insert(params, filters.categoria)
    end
    
    if filters.dificuldade then
        query = query .. " AND dificuldade = ?"
        table.insert(params, filters.dificuldade)
    end
    
    query = query .. " ORDER BY titulo"
    
    local result = execute_query(query, params)
    return result and result.rows or {}
end

-- Enrollment operations
function database.create_enrollment(enrollment_data)
    local query = [[
        INSERT INTO user_trilha (user_id, trilha_id, enrolled_at, progress, status)
        VALUES (?, ?, ?, ?, ?)
    ]]
    
    local params = {
        enrollment_data.user_id,
        enrollment_data.course_id,
        enrollment_data.enrolled_at,
        enrollment_data.progress,
        enrollment_data.status
    }
    
    local result = execute_query(query, params)
    return result and result.lastrowid or nil
end

function database.get_user_enrollment(user_id, course_id)
    local query = "SELECT * FROM user_trilha WHERE user_id = ? AND trilha_id = ?"
    local result = execute_query(query, {user_id, course_id})
    return result and result.rows[1] or nil
end

function database.get_user_enrollments(user_id)
    local query = [[
        SELECT ut.*, t.titulo, t.descricao, t.dificuldade 
        FROM user_trilha ut
        JOIN trilhas t ON ut.trilha_id = t.id
        WHERE ut.user_id = ? AND t.is_active = 1
        ORDER BY ut.enrolled_at DESC
    ]]
    
    local result = execute_query(query, {user_id})
    return result and result.rows or {}
end

function database.update_enrollment(user_id, course_id, updates)
    local set_clauses = {}
    local params = {}
    
    for field, value in pairs(updates) do
        table.insert(set_clauses, field .. " = ?")
        table.insert(params, value)
    end
    
    if #set_clauses == 0 then
        return false
    end
    
    local query = "UPDATE user_trilha SET " .. table.concat(set_clauses, ", ") .. " WHERE user_id = ? AND trilha_id = ?"
    table.insert(params, user_id)
    table.insert(params, course_id)
    
    local result = execute_query(query, params)
    return result and result.rowcount > 0
end

-- Statistics and analytics
function database.get_user_learning_stats(user_id)
    local stats_query = [[
        SELECT 
            COUNT(*) as total_enrollments,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_courses,
            AVG(progress) as avg_progress,
            MAX(enrolled_at) as last_enrollment
        FROM user_trilha 
        WHERE user_id = ?
    ]]
    
    local result = execute_query(stats_query, {user_id})
    if not result or not result.rows[1] then
        return nil
    end
    
    local stats = result.rows[1]
    
    -- Calculate completion rate
    local completion_rate = 0
    if stats.total_enrollments > 0 then
        completion_rate = (stats.completed_courses / stats.total_enrollments) * 100
    end
    
    -- Get performance data
    local performance_query = [[
        SELECT AVG(nota) as average_grade, COUNT(*) as total_activities
        FROM desempenhos 
        WHERE user_id = ?
    ]]
    
    local perf_result = execute_query(performance_query, {user_id})
    local performance = perf_result and perf_result.rows[1] or {}
    
    return {
        completion_rate = completion_rate,
        total_activities = performance.total_activities or 0,
        average_grade = performance.average_grade or 0,
        total_study_time_hours = 0, -- Would need to track this separately
        learning_streak = 0 -- Would need to calculate based on activity dates
    }
end

function database.get_course_enrollment_count(course_id)
    local query = "SELECT COUNT(*) as count FROM user_trilha WHERE trilha_id = ?"
    local result = execute_query(query, {course_id})
    return result and result.rows[1] and result.rows[1].count or 0
end

function database.get_course_average_rating(course_id)
    -- Would need a ratings table for this
    return 0
end

function database.get_course_completion_rate(course_id)
    local query = [[
        SELECT 
            COUNT(*) as total_enrollments,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_enrollments
        FROM user_trilha 
        WHERE trilha_id = ?
    ]]
    
    local result = execute_query(query, {course_id})
    if not result or not result.rows[1] then
        return 0
    end
    
    local stats = result.rows[1]
    if stats.total_enrollments == 0 then
        return 0
    end
    
    return (stats.completed_enrollments / stats.total_enrollments) * 100
end

function database.get_course_contents(course_id)
    local query = "SELECT * FROM conteudos WHERE trilha_id = ? ORDER BY ordem"
    local result = execute_query(query, {course_id})
    return result and result.rows or {}
end

-- Recommendations
function database.get_course_recommendations(user_id, options)
    options = options or {}
    
    local query = [[
        SELECT t.* FROM trilhas t
        WHERE t.is_active = 1
    ]]
    local params = {}
    
    if options.exclude_enrolled then
        query = query .. [[
            AND t.id NOT IN (
                SELECT trilha_id FROM user_trilha WHERE user_id = ?
            )
        ]]
        table.insert(params, user_id)
    end
    
    if options.preferred_difficulty then
        query = query .. " AND t.dificuldade = ?"
        table.insert(params, options.preferred_difficulty)
    end
    
    query = query .. " ORDER BY t.created_at DESC"
    
    if options.limit then
        query = query .. " LIMIT ?"
        table.insert(params, options.limit)
    end
    
    local result = execute_query(query, params)
    return result and result.rows or {}
end

-- Conversation history
function database.store_conversation(conversation_entry)
    local query = [[
        INSERT INTO chatbot_interactions (user_id, user_message, bot_response, intent, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ]]
    
    local params = {
        conversation_entry.user_id,
        conversation_entry.user_message,
        conversation_entry.bot_response,
        conversation_entry.intent,
        conversation_entry.timestamp
    }
    
    local result = execute_query(query, params)
    return result and result.lastrowid or nil
end

function database.get_conversation_history(user_id, limit)
    local query = [[
        SELECT user_message, bot_response, intent, timestamp
        FROM chatbot_interactions 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ]]
    
    local result = execute_query(query, {user_id, limit})
    return result and result.rows or {}
end

function database.clear_conversation_history(user_id)
    local query = "DELETE FROM chatbot_interactions WHERE user_id = ?"
    local result = execute_query(query, {user_id})
    return result and result.rowcount >= 0
end

return database

