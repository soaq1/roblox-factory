-- Client start-up.
local StarterGui = game:GetService("StarterGui")

local Screens = require(script.Parent.Screens)
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
HotbarUI.init()
BuildController.init(HotbarUI)
DebugUI.init()

-- The other screens and controllers, each in its own file with an init() of its own.
for _, name in
	{ "BagUI", "CraftUI", "TradeUI", "ShopUI", "VisitUI", "MachineUI", "PowerUI", "WorldController" }
do
	local source = script.Parent:FindFirstChild(name)
	if source and source:IsA("ModuleScript") then
		local ok, err = pcall(function()
			(require(source) :: any).init(HotbarUI)
		end)
		if not ok then
			warn(name .. " did not start: " .. tostring(err))
		end
	end
end
