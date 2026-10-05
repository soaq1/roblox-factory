-- Measurement tools for this test build: live numbers for the client to show, and chat commands.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TextChatService = game:GetService("TextChatService")
local Workspace = game:GetService("Workspace")

local ItemService = require(script.Parent.ItemService)
local MachineService = require(script.Parent.MachineService)
local Extractor = require(script.Parent.machines.Extractor)

local DebugService = {}

local function setSpeed(text: string)
	local n = tonumber(string.match(text, "([%d%.]+)"))
	if n then
		Extractor.speed = math.clamp(n, 0.1, 50)
		Workspace:SetAttribute("DbgSpeed", Extractor.speed)
	end
end

local function clearItems()
	ItemService.clearWhere(function()
		return false
	end)
end

local function command(alias: string, run: (string) -> ())
	local cmd = Instance.new("TextChatCommand")
	cmd.Name = "Cmd" .. alias
	cmd.PrimaryAlias = "/" .. alias
	cmd.Triggered:Connect(function(_source, text)
		run(text)
	end)
	cmd.Parent = TextChatService
end

function DebugService.start()
	Workspace:SetAttribute("DbgSpeed", 1)
	command("speed", setSpeed)
	command("clear", clearItems)
	-- The older chat system does not run TextChatCommands, so listen there as well.
	local function watch(player: Player)
		player.Chatted:Connect(function(message)
			if string.sub(message, 1, 6) == "/speed" then
				setSpeed(message)
			elseif string.sub(message, 1, 6) == "/clear" then
				clearItems()
			end
		end)
	end
	Players.PlayerAdded:Connect(watch)
	for _, player in Players:GetPlayers() do
		watch(player)
	end

	local beats, since = 0, os.clock()
	RunService.Heartbeat:Connect(function()
		beats += 1
		local now = os.clock()
		if now - since >= 1 then
			Workspace:SetAttribute("DbgHz", math.floor(beats / (now - since) + 0.5))
			Workspace:SetAttribute("DbgItems", ItemService.count())
			Workspace:SetAttribute("DbgMachines", MachineService.count())
			beats, since = 0, now
		end
	end)
end

return DebugService
