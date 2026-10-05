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
	-- The arguments come either way: GetTestArgs when Studio passes them through, and otherwise
	-- Workspace's "SelfTest" attribute, which the editor side wrote into the place before starting
	-- play. GetTestArgs only works some of the time -- one run had it, the next had nothing -- and
	-- the attribute is carried over because the play session is made from what is open in the editor.
	local ok, args = pcall(function()
		return StudioTestService:GetTestArgs()
	end)
	if not ok or type(args) ~= "table" or type(args.scenario) ~= "string" then
		local carried = Workspace:GetAttribute("SelfTest")
		if type(carried) == "string" then
			local read, decoded = pcall(HttpService.JSONDecode, HttpService, carried)
			args = if read and type(decoded) == "table" then decoded else args
		end
	end
	-- No arguments either way means a person pressed Play, not this plugin. Keep out of their way:
	-- ending a test they did not ask for would stop their game after a second.
	if type(args) ~= "table" then
		return
	end
	local described = if pcall(HttpService.JSONEncode, HttpService, args)
		then HttpService:JSONEncode(args)
		else "a table that could not be written out"
	post("/result", { stage = "args", args = described })
	if type(args.scenario) ~= "string" then
		-- Arguments arrived but name no scenario. Ending the test is what stops play mode, so do
		-- it rather than leave the session sitting there with nothing to run.
		pcall(function()
			StudioTestService:EndTest(HttpService:JSONEncode({
				pass = false,
				problems = { "no scenario was named: " .. described },
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
	-- Reported from in here, because what EndTest is given does not come back out of
	-- ExecutePlayModeAsync: the editor side only learns that the test ended.
	post("/result", { stage = "result", scenario = args.scenario, result = result })
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
				-- Write the arguments into the place as well. A play session is made from what is
				-- open in the editor, so this is already there when the game starts, whether or not
				-- Studio passes the arguments through its own channel. It leaves the open place
				-- marked as changed, which is why it is cleared again below.
				pcall(function()
					Workspace:SetAttribute("SelfTest", HttpService:JSONEncode(command.args or {}))
				end)
				local ran, result = pcall(function()
					if command.cmd == "run" then
						return StudioTestService:ExecuteRunModeAsync(command.args or {})
					end
					return StudioTestService:ExecutePlayModeAsync(command.args or {})
				end)
				-- So that pressing Play by hand later does not run the last test again.
				pcall(function()
					Workspace:SetAttribute("SelfTest", nil)
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
