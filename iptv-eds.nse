description = [[
Check if the EDS server
]]

author = ""
license = "WTFPL"
categories = {"discovery", "safe"}

local url = require "url"
local http = require "http"
local stdnse = require "stdnse"
local shortport = require "shortport"

hostrule = function(host)
    local path
    local match
    local response
    local output = {}
    local port = {number=8082}
    path = '/EDS/jsp/AuthenticationURL?Action=Login'
    
    -- Make HTTP GET request
    stdnse.print_debug("%s: %s GET %s",
                       SCRIPT_NAME,
                       host.targetname or host.ip,
                       path)
    local rd = function(host,port) return function(url) return false end end
    response = http.get(host, port.number, path, {redirect_ok=rd})
        
    -- Request failed (not an HTTP server)
    if response.status == nil then
        -- Bad response
        stdnse.print_debug("%s: %s GET %s - REQUEST FAILED",
                           SCRIPT_NAME,
                           host.targetname or host.ip,
                           path)
        -- Exit
        return false
    end

    stdnse.print_debug("%s: %s GET %s - %d", 
                           SCRIPT_NAME,
                           host.targetname or host.ip,
                           path,
                           response.status)
    if #response.cookies == 1 then
        print(host.ip..'   '..'ok')
    end
    return false

end
action = function(host,port)
    return('ok')
end
