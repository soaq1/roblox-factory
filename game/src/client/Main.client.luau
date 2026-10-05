-- Client start-up.
local StarterGui = game:GetService("StarterGui")

local Screens = require(script.Parent.Screens)
local Settings = require(script.Parent.Settings)
local HotbarUI = require(script.Parent.HotbarUI)
local BuildController = require(script.Parent.BuildController)
local DebugUI = require(script.Parent.DebugUI)

-- Roblox's own backpack bar uses the number keys; this game has its own.
pcall(function()
	StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, false)
end)

-- The palette draws machine models, so everything shared has to have arrived first.
if not game:IsLoaded() then
	game.Loaded:Wait()
end

Screens.init()
Settings.init()
HotbarUI.init()
BuildController.init(HotbarUI)
DebugUI.init()

-- Every other screen and controller: any module in this folder with an init() of its own.
local STARTED = { Screens = true, Settings = true, HotbarUI = true, BuildController = true, DebugUI = true }
for _, source in script.Parent:GetChildren() do
	if source:IsA("ModuleScript") and not STARTED[source.Name] then
		local ok, err = pcall(function()
			local module = require(source) :: any
			if type(module) == "table" and type(module.init) == "function" then
				module.init(HotbarUI)
			end
		end)
		if not ok then
			warn(source.Name .. " did not start: " .. tostring(err))
		end
	end
end
