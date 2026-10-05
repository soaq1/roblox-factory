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

-- Says the same thing twice: to the test server, and to Studio's output. Inside a play test the
-- request may be refused (a running game needs HTTP turned on for the place), and then the printed
-- line is the only trace left.
local function post(path, body)
	local ok, text = pcall(HttpService.JSONEncode, HttpService, body)
	print("FactorySelfTest " .. path .. " " .. (if ok then text else "(could not be written out)"))
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
	-- Always say what came through. Reading nothing here used to end quietly, which left the play
	-- test running for ever with no scenario and nothing reported.
	local described = if type(args) == "table"
		then (pcall(HttpService.JSONEncode, HttpService, args) and HttpService:JSONEncode(args) or "a table")
		else type(args) .. " " .. tostring(args)
	post("/result", { stage = "args", ok = ok, args = described })
	if not ok or type(args) ~= "table" or type(args.scenario) ~= "string" then
		-- Ending the test is what stops play mode, so do it even when there is nothing to run.
		pcall(function()
			StudioTestService:EndTest(HttpService:JSONEncode({
				pass = false,
				problems = { "the test arguments did not reach the game: " .. described },
			}))
		end)
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
				post("/result", { stage = "starting", id = command.id, cmd = command.cmd, args = command.args })
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
