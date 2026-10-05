-- Measurement tools for this test build: live numbers for the client to show, and chat commands.
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Commands = require(script.Parent.Commands)
local ItemService = require(script.Parent.ItemService)
local MachineService = require(script.Parent.MachineService)
local Tuning = require(script.Parent.Tuning)

local DebugService = {}

local function setSpeed(text: string)
	local n = tonumber(string.match(text, "([%d%.]+)"))
	if n then
		Tuning.speed = math.clamp(n, 0.1, 50)
		Workspace:SetAttribute("DbgSpeed", Tuning.speed)
	end
end

local function clearItems()
	ItemService.clearWhere(function()
		return false
	end)
end

function DebugService.start()
	Workspace:SetAttribute("DbgSpeed", 1)
	Commands.register("speed", function(_player, args)
		setSpeed(args[1] or "")
	end)
	Commands.register("clear", clearItems)

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
