-- User Management Module (Lua)
-- Handles all user-related business logic

-- Remove json dependency for now
-- local crypto = require("lua_core.utils.crypto")
-- local db = require("lua_core.data.database")

local user_manager = {}

-- User validation rules
local validation_rules = {
    email = {
        pattern = "^[%w%._%+%-]+@[%w%._%+%-]+%.%w+$",
        max_length = 255
    },
    password = {
        min_length = 6,
        max_length = 128
    },
    name = {
        min_length = 2,
        max_length = 100
    }
}

-- Validate user data
function user_manager.validate_user_data(user_data)
    local errors = {}
    
    -- Validate email
    if not user_data.email then
        table.insert(errors, "Email is required")
    elseif not string.match(user_data.email, validation_rules.email.pattern) then
        table.insert(errors, "Invalid email format")
    elseif #user_data.email > validation_rules.email.max_length then
        table.insert(errors, "Email too long")
    end
    
    -- Validate password
    if not user_data.password then
        table.insert(errors, "Password is required")
    elseif #user_data.password < validation_rules.password.min_length then
        table.insert(errors, "Password too short (minimum " .. validation_rules.password.min_length .. " characters)")
    elseif #user_data.password > validation_rules.password.max_length then
        table.insert(errors, "Password too long")
    end
    
    -- Validate name
    if not user_data.name then
        table.insert(errors, "Name is required")
    elseif #user_data.name < validation_rules.name.min_length then
        table.insert(errors, "Name too short")
    elseif #user_data.name > validation_rules.name.max_length then
        table.insert(errors, "Name too long")
    end
    
    return #errors == 0, errors
end

-- Create new user
function user_manager.create_user(user_data)
    -- Validate input data
    local is_valid, errors = user_manager.validate_user_data(user_data)
    if not is_valid then
        return {
            success = false,
            error = "Validation failed",
            details = errors
        }
    end
    
    -- Check if user already exists (mock for now)
    -- local existing_user = db.find_user_by_email(user_data.email)
    -- For now, assume user doesn't exist
    
    -- Hash password (will be handled by Python bridge)
    local hashed_password = "PYTHON_HASH:" .. user_data.password
    
    -- Prepare user data for database
    local new_user = {
        email = string.lower(user_data.email),
        name = user_data.name,
        password_hash = hashed_password,
        learning_profile = user_data.learning_profile or "beginner",
        created_at = os.time(),
        updated_at = os.time(),
        is_active = true
    }
    
    -- Save to database (will be handled by Python bridge)
    -- For now, return mock success
    local user_id = 1
    
    -- Return success with user data (without password)
    new_user.id = user_id
    new_user.password_hash = nil
    
    return {
        success = true,
        data = new_user,
        message = "User created successfully"
    }
end

-- Authenticate user
function user_manager.authenticate_user(email, password)
    if not email or not password then
        return {
            success = false,
            error = "Email and password are required"
        }
    end
    
    -- Find user by email (will be handled by Python bridge)
    -- For now, return mock user
    local user = {
        id = 1,
        email = string.lower(email),
        name = "Test User",
        password_hash = "PYTHON_HASH:" .. password,
        is_active = true
    }
    
    -- Check if user is active
    if not user.is_active then
        return {
            success = false,
            error = "User account is deactivated"
        }
    end
    
    -- Verify password (simple check for now)
    local expected_hash = "PYTHON_HASH:" .. password
    if user.password_hash ~= expected_hash then
        return {
            success = false,
            error = "Invalid email or password"
        }
    end
    
    -- Generate access token (mock for now)
    local access_token = "JWT_TOKEN:user_" .. user.id .. "_exp_" .. (os.time() + 1800)
    
    -- Return success with user data and token
    user.password_hash = nil -- Remove password hash from response
    
    return {
        success = true,
        data = {
            user = user,
            access_token = access_token,
            token_type = "bearer"
        },
        message = "Authentication successful"
    }
end

-- Get user by ID
function user_manager.get_user_by_id(user_id)
    if not user_id then
        return {
            success = false,
            error = "User ID is required"
        }
    end
    
    -- Mock user for now
    local user = {
        id = user_id,
        email = "test@example.com",
        name = "Test User",
        learning_profile = "beginner",
        is_active = true
    }
    
    -- Remove sensitive data
    user.password_hash = nil
    
    return {
        success = true,
        data = user
    }
end

-- Update user profile
function user_manager.update_user_profile(user_id, update_data)
    if not user_id then
        return {
            success = false,
            error = "User ID is required"
        }
    end
    
    -- Get current user
    local current_user = db.find_user_by_id(user_id)
    if not current_user then
        return {
            success = false,
            error = "User not found"
        }
    end
    
    -- Prepare update data
    local allowed_fields = {"name", "learning_profile", "preferences"}
    local updates = {}
    
    for _, field in ipairs(allowed_fields) do
        if update_data[field] then
            updates[field] = update_data[field]
        end
    end
    
    if next(updates) == nil then
        return {
            success = false,
            error = "No valid fields to update"
        }
    end
    
    -- Add timestamp
    updates.updated_at = os.time()
    
    -- Update in database
    local success = db.update_user(user_id, updates)
    if not success then
        return {
            success = false,
            error = "Failed to update user profile"
        }
    end
    
    -- Get updated user
    local updated_user = db.find_user_by_id(user_id)
    updated_user.password_hash = nil
    
    return {
        success = true,
        data = updated_user,
        message = "Profile updated successfully"
    }
end

-- Get user learning statistics
function user_manager.get_user_stats(user_id)
    if not user_id then
        return {
            success = false,
            error = "User ID is required"
        }
    end
    
    local stats = db.get_user_learning_stats(user_id)
    if not stats then
        return {
            success = false,
            error = "Failed to retrieve user statistics"
        }
    end
    
    return {
        success = true,
        data = stats
    }
end

-- Deactivate user account
function user_manager.deactivate_user(user_id)
    if not user_id then
        return {
            success = false,
            error = "User ID is required"
        }
    end
    
    local success = db.update_user(user_id, {
        is_active = false,
        updated_at = os.time()
    })
    
    if not success then
        return {
            success = false,
            error = "Failed to deactivate user"
        }
    end
    
    return {
        success = true,
        message = "User account deactivated successfully"
    }
end

return user_manager
