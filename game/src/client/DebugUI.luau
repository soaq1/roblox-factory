-- Shows the server's live numbers in the corner of the screen.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local DebugUI = {}

function DebugUI.init()
	local gui = Instance.new("ScreenGui")
	gui.Name = "DebugUI"
	gui.ResetOnSpawn = false
	local text = Instance.new("TextLabel")
	text.BackgroundTransparency = 0.35
	text.BackgroundColor3 = Color3.fromRGB(28, 30, 34)
	text.BorderSizePixel = 0
	text.Position = UDim2.fromOffset(10, 10)
	text.Size = UDim2.fromOffset(200, 96)
	text.Font = Enum.Font.Code
	text.TextSize = 14
	text.TextColor3 = Color3.fromRGB(233, 234, 236)
	text.TextXAlignment = Enum.TextXAlignment.Left
	text.TextYAlignment = Enum.TextYAlignment.Top
	text.Text = ""
	text.Parent = gui
	local pad = Instance.new("UIPadding")
	pad.PaddingLeft = UDim.new(0, 8)
	pad.PaddingTop = UDim.new(0, 6)
	pad.Parent = text
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")

	task.spawn(function()
		while true do
			local function read(name: string): string
				local value = Workspace:GetAttribute(name)
				return if value == nil then "-" else tostring(value)
			end
			text.Text = string.format(
				"서버   %s 회/초\n물체   %s\n기계   %s\n추출   %s 배속\n저장   %s",
				read("DbgHz"),
				read("DbgItems"),
				read("DbgMachines"),
				read("DbgSpeed"),
				read("SaveMode")
			)
			task.wait(0.5)
		end
	end)
end

return DebugUI
