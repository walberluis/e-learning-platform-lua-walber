-- Utility Helper Functions (Lua)
-- Common utility functions used throughout the application

local helpers = {}

-- String utilities
function helpers.trim(str)
    return str:match("^%s*(.-)%s*$")
end

function helpers.split(str, delimiter)
    local result = {}
    local pattern = string.format("([^%s]+)", delimiter)
    
    for match in string.gmatch(str, pattern) do
        table.insert(result, match)
    end
    
    return result
end

function helpers.starts_with(str, prefix)
    return string.sub(str, 1, string.len(prefix)) == prefix
end

function helpers.ends_with(str, suffix)
    return string.sub(str, -string.len(suffix)) == suffix
end

function helpers.capitalize(str)
    return string.upper(string.sub(str, 1, 1)) .. string.lower(string.sub(str, 2))
end

-- Table utilities
function helpers.table_length(tbl)
    local count = 0
    for _ in pairs(tbl) do
        count = count + 1
    end
    return count
end

function helpers.table_contains(tbl, value)
    for _, v in ipairs(tbl) do
        if v == value then
            return true
        end
    end
    return false
end

function helpers.table_merge(t1, t2)
    local result = {}
    
    for k, v in pairs(t1) do
        result[k] = v
    end
    
    for k, v in pairs(t2) do
        result[k] = v
    end
    
    return result
end

function helpers.table_keys(tbl)
    local keys = {}
    for k, _ in pairs(tbl) do
        table.insert(keys, k)
    end
    return keys
end

function helpers.table_values(tbl)
    local values = {}
    for _, v in pairs(tbl) do
        table.insert(values, v)
    end
    return values
end

-- Date and time utilities
function helpers.format_timestamp(timestamp)
    return os.date("%Y-%m-%d %H:%M:%S", timestamp)
end

function helpers.get_current_timestamp()
    return os.time()
end

function helpers.days_between(timestamp1, timestamp2)
    local diff = math.abs(timestamp2 - timestamp1)
    return math.floor(diff / (24 * 60 * 60))
end

function helpers.format_duration(seconds)
    local hours = math.floor(seconds / 3600)
    local minutes = math.floor((seconds % 3600) / 60)
    local secs = seconds % 60
    
    if hours > 0 then
        return string.format("%dh %dm %ds", hours, minutes, secs)
    elseif minutes > 0 then
        return string.format("%dm %ds", minutes, secs)
    else
        return string.format("%ds", secs)
    end
end

-- Validation utilities
function helpers.is_valid_email(email)
    local pattern = "^[%w%._%+%-]+@[%w%._%+%-]+%.%w+$"
    return string.match(email, pattern) ~= nil
end

function helpers.is_valid_password(password)
    return password and string.len(password) >= 6
end

function helpers.sanitize_string(str)
    if not str then return "" end
    
    -- Remove potentially dangerous characters
    str = string.gsub(str, "[<>\"'&]", "")
    
    -- Trim whitespace
    str = helpers.trim(str)
    
    return str
end

-- Math utilities
function helpers.round(num, decimals)
    local mult = 10^(decimals or 0)
    return math.floor(num * mult + 0.5) / mult
end

function helpers.clamp(value, min_val, max_val)
    return math.max(min_val, math.min(max_val, value))
end

function helpers.percentage(part, total)
    if total == 0 then return 0 end
    return (part / total) * 100
end

-- Array utilities
function helpers.array_map(array, func)
    local result = {}
    for i, v in ipairs(array) do
        result[i] = func(v, i)
    end
    return result
end

function helpers.array_filter(array, predicate)
    local result = {}
    for _, v in ipairs(array) do
        if predicate(v) then
            table.insert(result, v)
        end
    end
    return result
end

function helpers.array_find(array, predicate)
    for _, v in ipairs(array) do
        if predicate(v) then
            return v
        end
    end
    return nil
end

function helpers.array_reduce(array, func, initial)
    local accumulator = initial
    for _, v in ipairs(array) do
        accumulator = func(accumulator, v)
    end
    return accumulator
end

-- JSON utilities (assuming json library is available)
function helpers.json_encode(data)
    local json = require("json")
    return json.encode(data)
end

function helpers.json_decode(str)
    local json = require("json")
    local success, result = pcall(json.decode, str)
    if success then
        return result
    else
        return nil
    end
end

-- Logging utilities
function helpers.log_info(message)
    print(string.format("[INFO] %s: %s", os.date("%Y-%m-%d %H:%M:%S"), message))
end

function helpers.log_error(message)
    print(string.format("[ERROR] %s: %s", os.date("%Y-%m-%d %H:%M:%S"), message))
end

function helpers.log_warning(message)
    print(string.format("[WARNING] %s: %s", os.date("%Y-%m-%d %H:%M:%S"), message))
end

function helpers.log_debug(message)
    print(string.format("[DEBUG] %s: %s", os.date("%Y-%m-%d %H:%M:%S"), message))
end

-- Configuration utilities
function helpers.get_env_var(name, default_value)
    -- This would interface with Python's os.environ
    return default_value
end

function helpers.parse_boolean(value)
    if type(value) == "boolean" then
        return value
    elseif type(value) == "string" then
        local lower = string.lower(value)
        return lower == "true" or lower == "1" or lower == "yes"
    else
        return false
    end
end

-- Error handling utilities
function helpers.safe_call(func, ...)
    local success, result = pcall(func, ...)
    if success then
        return result, nil
    else
        return nil, result
    end
end

function helpers.create_error_response(message, code)
    return {
        success = false,
        error = message,
        error_code = code or "UNKNOWN_ERROR",
        timestamp = os.time()
    }
end

function helpers.create_success_response(data, message)
    return {
        success = true,
        data = data,
        message = message,
        timestamp = os.time()
    }
end

-- Performance utilities
function helpers.measure_time(func, ...)
    local start_time = os.clock()
    local result = func(...)
    local end_time = os.clock()
    local duration = end_time - start_time
    
    return result, duration
end

-- Random utilities
function helpers.generate_random_string(length)
    local chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    local result = ""
    
    math.randomseed(os.time())
    
    for i = 1, length do
        local rand_index = math.random(1, #chars)
        result = result .. string.sub(chars, rand_index, rand_index)
    end
    
    return result
end

function helpers.generate_uuid()
    -- Simple UUID v4 implementation
    math.randomseed(os.time())
    
    local template = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
    
    return string.gsub(template, "[xy]", function(c)
        local v = (c == "x") and math.random(0, 0xf) or math.random(8, 0xb)
        return string.format("%x", v)
    end)
end

return helpers
