-- E-Learning Platform - Lua Core
-- Main initialization file for Lua-based business logic

-- Global configuration
local config = {
    version = "1.0.0",
    name = "E-Learning Platform",
    debug = true
}

-- Load core modules (simplified)
local user_manager = require("lua_core.business.user_manager")
-- local course_manager = require("lua_core.business.course_manager")
-- local ai_assistant = require("lua_core.ai.assistant")
-- local database = require("lua_core.data.database")
-- local utils = require("lua_core.utils.helpers")

-- Initialize platform
local function init_platform()
    print("🎓 Initializing E-Learning Platform (Lua Core)")
    print("Version: " .. config.version)
    
    -- Simplified initialization
    print("✅ Platform initialized successfully")
end

-- Export main API (simplified)
local elearning = {
    -- Configuration
    config = config,
    
    -- Core business modules
    users = user_manager,
    -- courses = course_manager,
    -- ai = ai_assistant,
    
    -- Initialization
    init = init_platform
}

return elearning
