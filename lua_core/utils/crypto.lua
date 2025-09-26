-- Cryptography Utilities (Lua)
-- Handles password hashing and JWT token operations
-- Note: This interfaces with Python's cryptography libraries

local crypto = {}

-- Password hashing (interfaces with Python's Argon2)
function crypto.hash_password(password)
    -- This will be implemented as a bridge to Python's argon2-cffi
    -- For now, return a placeholder that will be replaced by Python bridge
    return "PYTHON_HASH:" .. password
end

function crypto.verify_password(password, hashed_password)
    -- This will be implemented as a bridge to Python's argon2-cffi
    -- For now, simple comparison for testing
    return hashed_password == "PYTHON_HASH:" .. password
end

-- JWT token operations (interfaces with Python's python-jose)
function crypto.generate_jwt_token(payload)
    -- This will be implemented as a bridge to Python's python-jose
    -- For now, return a placeholder token
    local token_data = {
        user_id = payload.user_id,
        email = payload.email,
        exp = payload.exp
    }
    
    -- Simple base64-like encoding for testing
    local token_string = string.format("user_%d_exp_%d", payload.user_id, payload.exp)
    return "JWT_TOKEN:" .. token_string
end

function crypto.verify_jwt_token(token)
    -- This will be implemented as a bridge to Python's python-jose
    -- For now, simple verification for testing
    if not token or not string.match(token, "^JWT_TOKEN:") then
        return nil, "Invalid token format"
    end
    
    local token_data = string.gsub(token, "^JWT_TOKEN:", "")
    local user_id, exp = string.match(token_data, "user_(%d+)_exp_(%d+)")
    
    if not user_id or not exp then
        return nil, "Invalid token data"
    end
    
    -- Check expiration
    if tonumber(exp) < os.time() then
        return nil, "Token expired"
    end
    
    return {
        user_id = tonumber(user_id),
        exp = tonumber(exp)
    }, nil
end

function crypto.decode_jwt_token(token)
    -- This will be implemented as a bridge to Python's python-jose
    local payload, error = crypto.verify_jwt_token(token)
    return payload, error
end

-- Random string generation for secrets
function crypto.generate_secret_key(length)
    length = length or 32
    
    local chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    local result = ""
    
    math.randomseed(os.time())
    
    for i = 1, length do
        local rand_index = math.random(1, #chars)
        result = result .. string.sub(chars, rand_index, rand_index)
    end
    
    return result
end

-- Hash functions for general use
function crypto.simple_hash(data)
    -- Simple hash function for non-security purposes
    local hash = 0
    for i = 1, #data do
        local char = string.byte(data, i)
        hash = ((hash << 5) - hash) + char
        hash = hash & 0xFFFFFFFF -- Keep it 32-bit
    end
    return string.format("%08x", hash)
end

-- Encryption/Decryption utilities (placeholder for future implementation)
function crypto.encrypt_data(data, key)
    -- Placeholder for AES encryption
    -- Would interface with Python's cryptography library
    return "ENCRYPTED:" .. data
end

function crypto.decrypt_data(encrypted_data, key)
    -- Placeholder for AES decryption
    -- Would interface with Python's cryptography library
    if string.match(encrypted_data, "^ENCRYPTED:") then
        return string.gsub(encrypted_data, "^ENCRYPTED:", "")
    end
    return nil
end

-- Session token generation
function crypto.generate_session_token()
    local timestamp = os.time()
    local random_part = crypto.generate_secret_key(16)
    return string.format("session_%d_%s", timestamp, random_part)
end

-- API key generation
function crypto.generate_api_key()
    local prefix = "elearn"
    local random_part = crypto.generate_secret_key(24)
    return string.format("%s_%s", prefix, random_part)
end

-- Password strength validation
function crypto.validate_password_strength(password)
    local errors = {}
    
    if #password < 8 then
        table.insert(errors, "Password must be at least 8 characters long")
    end
    
    if not string.match(password, "%d") then
        table.insert(errors, "Password must contain at least one number")
    end
    
    if not string.match(password, "%l") then
        table.insert(errors, "Password must contain at least one lowercase letter")
    end
    
    if not string.match(password, "%u") then
        table.insert(errors, "Password must contain at least one uppercase letter")
    end
    
    if not string.match(password, "[%W_]") then
        table.insert(errors, "Password must contain at least one special character")
    end
    
    local strength = "weak"
    if #errors == 0 then
        if #password >= 12 then
            strength = "strong"
        else
            strength = "medium"
        end
    end
    
    return {
        is_valid = #errors == 0,
        errors = errors,
        strength = strength
    }
end

-- Rate limiting helpers
function crypto.generate_rate_limit_key(user_id, action)
    return string.format("rate_limit_%s_%d_%d", action, user_id, math.floor(os.time() / 60))
end

-- CSRF token generation
function crypto.generate_csrf_token()
    return crypto.generate_secret_key(32)
end

-- One-time password generation
function crypto.generate_otp(length)
    length = length or 6
    local digits = "0123456789"
    local result = ""
    
    math.randomseed(os.time())
    
    for i = 1, length do
        local rand_index = math.random(1, #digits)
        result = result .. string.sub(digits, rand_index, rand_index)
    end
    
    return result
end

return crypto
