-- Client start-up.
local StarterGui = game:GetService("StarterGui")

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

HotbarUI.init()
BuildController.init(HotbarUI)
DebugUI.init()
