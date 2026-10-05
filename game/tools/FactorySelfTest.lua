-- A Studio plugin that lets tests be started from outside Studio.
-- Copy to Studio's local plugin folder (macOS: ~/Documents/Roblox/Plugins) and restart Studio.
-- It talks only to localhost (game/tools/testserver.py). Studio asks once whether to allow that.
--
-- In the editor it asks the test server once a second for something to do, and when told to,
-- starts a play test with the given arguments. Inside that play test (plugins run there too) it
-- hands the arguments to the game by setting Workspace's "SelfTest" attribute, waits for the game
-- to set "SelfTestResult", and ends the test with that.
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local StudioTestService = game:GetService("StudioTestService")
local Workspace = game:GetService("Workspace")

local URL = "http://localhost:34873"

local function post(path, body)
	pcall(function()
		HttpService:RequestAsync({
			Url = URL .. path,
			Method = "POST",
			Headers = { ["Content-Type"] = "application/json" },
			Body = HttpService:JSONEncode(body),
		})
	end)
end

if RunService:IsRunning() then
	-- Inside a play test. Only the server side acts, and only for a test this plugin started.
	if not RunService:IsServer() then
		return
	end
	local ok, args = pcall(function()
		return StudioTestService:GetTestArgs()
	end)
	if not ok or type(args) ~= "table" or type(args.scenario) ~= "string" then
		return
	end
	Workspace:SetAttribute("SelfTest", HttpService:JSONEncode(args))
	local deadline = os.clock() + (tonumber(args.timeout) or 120)
	while os.clock() < deadline and Workspace:GetAttribute("SelfTestResult") == nil do
		task.wait(0.25)
	end
	local result = Workspace:GetAttribute("SelfTestResult") or '{"error":"the game did not finish in time"}'
	local ended, problem = pcall(function()
		StudioTestService:EndTest(result)
	end)
	if not ended then
		post("/result", { stage = "end", error = tostring(problem), result = result })
	end
	return
end

-- In the editor.
task.spawn(function()
	post("/result", { stage = "hello", place = game.Name })
	while true do
		local ok, response = pcall(function()
			return HttpService:RequestAsync({ Url = URL .. "/next", Method = "GET" })
		end)
		if ok and response.Success then
			local decoded, command = pcall(HttpService.JSONDecode, HttpService, response.Body)
			if decoded and type(command) == "table" and command.cmd then
				local started = os.clock()
				local ran, result = pcall(function()
					if command.cmd == "run" then
						return StudioTestService:ExecuteRunModeAsync(command.args or {})
					end
					return StudioTestService:ExecutePlayModeAsync(command.args or {})
				end)
				post("/result", {
					stage = "done",
					id = command.id,
					ok = ran,
					seconds = math.floor((os.clock() - started) * 10) / 10,
					result = if ran then result else tostring(result),
				})
			end
		end
		task.wait(1)
	end
end)
