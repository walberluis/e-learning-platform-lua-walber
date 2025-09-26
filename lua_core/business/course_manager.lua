-- Course Management Module (Lua)
-- Handles all course and learning path related business logic

local json = require("json")
local db = require("lua_core.data.database")
local utils = require("lua_core.utils.helpers")

local course_manager = {}

-- Course difficulty levels
local difficulty_levels = {
    "iniciante",
    "intermediario", 
    "avancado"
}

-- Course categories
local categories = {
    "programacao",
    "web_development",
    "data_science",
    "machine_learning",
    "mobile_development",
    "devops",
    "design",
    "business"
}

-- Validate course data
function course_manager.validate_course_data(course_data)
    local errors = {}
    
    -- Validate title
    if not course_data.titulo then
        table.insert(errors, "Course title is required")
    elseif #course_data.titulo < 3 then
        table.insert(errors, "Course title too short")
    elseif #course_data.titulo > 200 then
        table.insert(errors, "Course title too long")
    end
    
    -- Validate description
    if not course_data.descricao then
        table.insert(errors, "Course description is required")
    elseif #course_data.descricao < 10 then
        table.insert(errors, "Course description too short")
    end
    
    -- Validate difficulty
    if course_data.dificuldade then
        local valid_difficulty = false
        for _, level in ipairs(difficulty_levels) do
            if course_data.dificuldade == level then
                valid_difficulty = true
                break
            end
        end
        if not valid_difficulty then
            table.insert(errors, "Invalid difficulty level")
        end
    end
    
    -- Validate category
    if course_data.categoria then
        local valid_category = false
        for _, cat in ipairs(categories) do
            if course_data.categoria == cat then
                valid_category = true
                break
            end
        end
        if not valid_category then
            table.insert(errors, "Invalid category")
        end
    end
    
    return #errors == 0, errors
end

-- Create new course
function course_manager.create_course(course_data)
    -- Validate input data
    local is_valid, errors = course_manager.validate_course_data(course_data)
    if not is_valid then
        return {
            success = false,
            error = "Validation failed",
            details = errors
        }
    end
    
    -- Prepare course data
    local new_course = {
        titulo = course_data.titulo,
        descricao = course_data.descricao,
        dificuldade = course_data.dificuldade or "iniciante",
        categoria = course_data.categoria or "programacao",
        duracao_estimada = course_data.duracao_estimada or 0,
        pre_requisitos = course_data.pre_requisitos or "",
        objetivos = course_data.objetivos or "",
        is_active = true,
        created_at = os.time(),
        updated_at = os.time()
    }
    
    -- Save to database
    local course_id = db.create_course(new_course)
    if not course_id then
        return {
            success = false,
            error = "Failed to create course in database"
        }
    end
    
    new_course.id = course_id
    
    return {
        success = true,
        data = new_course,
        message = "Course created successfully"
    }
end

-- Get all courses with filters
function course_manager.get_courses(filters)
    filters = filters or {}
    
    local courses = db.get_courses(filters)
    if not courses then
        return {
            success = false,
            error = "Failed to retrieve courses"
        }
    end
    
    -- Add computed fields
    for _, course in ipairs(courses) do
        course.enrollment_count = db.get_course_enrollment_count(course.id) or 0
        course.average_rating = db.get_course_average_rating(course.id) or 0
        course.completion_rate = db.get_course_completion_rate(course.id) or 0
    end
    
    return {
        success = true,
        data = courses,
        total = #courses
    }
end

-- Get course by ID
function course_manager.get_course_by_id(course_id)
    if not course_id then
        return {
            success = false,
            error = "Course ID is required"
        }
    end
    
    local course = db.find_course_by_id(course_id)
    if not course then
        return {
            success = false,
            error = "Course not found"
        }
    end
    
    -- Add additional information
    course.enrollment_count = db.get_course_enrollment_count(course_id) or 0
    course.average_rating = db.get_course_average_rating(course_id) or 0
    course.completion_rate = db.get_course_completion_rate(course_id) or 0
    course.contents = db.get_course_contents(course_id) or {}
    
    return {
        success = true,
        data = course
    }
end

-- Enroll user in course
function course_manager.enroll_user(user_id, course_id)
    if not user_id or not course_id then
        return {
            success = false,
            error = "User ID and Course ID are required"
        }
    end
    
    -- Check if course exists
    local course = db.find_course_by_id(course_id)
    if not course then
        return {
            success = false,
            error = "Course not found"
        }
    end
    
    -- Check if user is already enrolled
    local existing_enrollment = db.get_user_enrollment(user_id, course_id)
    if existing_enrollment then
        return {
            success = false,
            error = "User is already enrolled in this course"
        }
    end
    
    -- Create enrollment
    local enrollment_data = {
        user_id = user_id,
        course_id = course_id,
        enrolled_at = os.time(),
        progress = 0,
        status = "active"
    }
    
    local enrollment_id = db.create_enrollment(enrollment_data)
    if not enrollment_id then
        return {
            success = false,
            error = "Failed to enroll user in course"
        }
    end
    
    return {
        success = true,
        data = {
            enrollment_id = enrollment_id,
            course = course,
            enrolled_at = enrollment_data.enrolled_at
        },
        message = "User enrolled successfully"
    }
end

-- Get user's enrolled courses
function course_manager.get_user_courses(user_id)
    if not user_id then
        return {
            success = false,
            error = "User ID is required"
        }
    end
    
    local enrollments = db.get_user_enrollments(user_id)
    if not enrollments then
        return {
            success = false,
            error = "Failed to retrieve user courses"
        }
    end
    
    -- Enrich with course data
    local courses = {}
    for _, enrollment in ipairs(enrollments) do
        local course = db.find_course_by_id(enrollment.course_id)
        if course then
            course.enrollment_data = {
                enrolled_at = enrollment.enrolled_at,
                progress = enrollment.progress,
                status = enrollment.status,
                last_accessed = enrollment.last_accessed
            }
            table.insert(courses, course)
        end
    end
    
    return {
        success = true,
        data = courses,
        total = #courses
    }
end

-- Update course progress
function course_manager.update_progress(user_id, course_id, progress_data)
    if not user_id or not course_id then
        return {
            success = false,
            error = "User ID and Course ID are required"
        }
    end
    
    -- Check enrollment exists
    local enrollment = db.get_user_enrollment(user_id, course_id)
    if not enrollment then
        return {
            success = false,
            error = "User is not enrolled in this course"
        }
    end
    
    -- Calculate new progress
    local new_progress = progress_data.progress or enrollment.progress
    if new_progress < 0 then new_progress = 0 end
    if new_progress > 100 then new_progress = 100 end
    
    -- Update enrollment
    local updates = {
        progress = new_progress,
        last_accessed = os.time(),
        updated_at = os.time()
    }
    
    -- Mark as completed if progress is 100%
    if new_progress >= 100 then
        updates.status = "completed"
        updates.completed_at = os.time()
    end
    
    local success = db.update_enrollment(user_id, course_id, updates)
    if not success then
        return {
            success = false,
            error = "Failed to update course progress"
        }
    end
    
    return {
        success = true,
        data = {
            progress = new_progress,
            status = updates.status or enrollment.status
        },
        message = "Progress updated successfully"
    }
end

-- Get course recommendations for user
function course_manager.get_recommendations(user_id, limit)
    limit = limit or 5
    
    if not user_id then
        return {
            success = false,
            error = "User ID is required"
        }
    end
    
    -- Get user's learning profile and history
    local user = db.find_user_by_id(user_id)
    if not user then
        return {
            success = false,
            error = "User not found"
        }
    end
    
    local user_courses = db.get_user_enrollments(user_id) or {}
    local completed_categories = {}
    local user_level = user.learning_profile or "iniciante"
    
    -- Analyze user's completed courses
    for _, enrollment in ipairs(user_courses) do
        if enrollment.status == "completed" then
            local course = db.find_course_by_id(enrollment.course_id)
            if course then
                completed_categories[course.categoria] = true
            end
        end
    end
    
    -- Get recommendations based on user profile
    local recommendations = db.get_course_recommendations(user_id, {
        exclude_enrolled = true,
        preferred_difficulty = user_level,
        limit = limit
    })
    
    if not recommendations then
        recommendations = {}
    end
    
    -- Score and sort recommendations
    for _, course in ipairs(recommendations) do
        local score = 0
        
        -- Boost score for appropriate difficulty
        if course.dificuldade == user_level then
            score = score + 10
        end
        
        -- Boost score for categories user hasn't explored
        if not completed_categories[course.categoria] then
            score = score + 5
        end
        
        -- Boost score for popular courses
        local enrollment_count = db.get_course_enrollment_count(course.id) or 0
        score = score + math.min(enrollment_count / 10, 5)
        
        course.recommendation_score = score
    end
    
    -- Sort by score
    table.sort(recommendations, function(a, b)
        return a.recommendation_score > b.recommendation_score
    end)
    
    return {
        success = true,
        data = recommendations,
        total = #recommendations
    }
end

-- Search courses
function course_manager.search_courses(query, filters)
    if not query or #query < 2 then
        return {
            success = false,
            error = "Search query must be at least 2 characters"
        }
    end
    
    filters = filters or {}
    filters.search_query = query
    
    local courses = db.search_courses(filters)
    if not courses then
        return {
            success = false,
            error = "Search failed"
        }
    end
    
    return {
        success = true,
        data = courses,
        total = #courses,
        query = query
    }
end

return course_manager
