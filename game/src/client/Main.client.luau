-- Client start-up.
local StarterGui = game:GetService("StarterGui")

local HotbarUI = require(script.Parent.HotbarUI)
local BuildController = require(script.Parent.BuildController)
local DebugUI = require(script.Parent.DebugUI)

-- Roblox's own backpack bar uses the number keys; this game has its own.
pcall(function()
	StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, false)
end)

HotbarUI.init()
BuildController.init(HotbarUI)
DebugUI.init()
