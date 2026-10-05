-- The settings screen: one switch for each setting. What the switches mean is decided by the code
-- that reads them (Settings.get); this screen only shows them and flips them.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Prefs = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Prefs"))
local Screens = require(script.Parent.Screens)
local Settings = require(script.Parent.Settings)
local UIKit = require(script.Parent.UIKit)

local SettingsUI = {}

local ROW = 58

-- The settings in the order they are shown, with what each one does in a few words.
local LIST = {
	{
		key = "holdToRepeat",
		name = "누르고 있으면 계속 치기",
		note = "버튼이나 손가락을 떼지 않으면 도구를 계속 휘두릅니다",
	},
	{
		key = "dragPlace",
		name = "누른 채 움직이면 계속 놓기",
		note = "누른 채로 옮겨 가면 새 칸마다 하나씩 놓습니다",
	},
	{
		key = "profilePublic",
		name = "내 정보 공개",
		note = "다른 플레이어가 나를 눌렀을 때 내 정보를 볼 수 있습니다",
	},
}

local switches: { [string]: TextButton } = {}

local function redraw()
	for key, switch in switches do
		local on = Settings.get(key)
		switch.Text = if on then "켜짐" else "꺼짐"
		switch.BackgroundColor3 = if on then UIKit.GOOD else UIKit.PANEL
		switch.TextColor3 = if on then UIKit.BACK else UIKit.DIM
	end
end

local function row(list: Instance, order: number, key: string, name: string, note: string)
	local frame = Instance.new("Frame")
	frame.Size = UDim2.new(1, -8, 0, ROW)
	frame.BackgroundColor3 = UIKit.PANEL
	frame.BorderSizePixel = 0
	frame.LayoutOrder = order
	frame.Parent = list
	UIKit.round(frame, 8)

	local title = UIKit.label(frame, name, 14)
	title.TextXAlignment = Enum.TextXAlignment.Left
	title.TextWrapped = false
	title.TextTruncate = Enum.TextTruncate.AtEnd
	title.Position = UDim2.fromOffset(12, 8)
	title.Size = UDim2.new(1, -116, 0, 20)

	local detail = UIKit.label(frame, note, 12)
	detail.TextColor3 = UIKit.DIM
	detail.TextXAlignment = Enum.TextXAlignment.Left
	detail.TextWrapped = false
	detail.TextTruncate = Enum.TextTruncate.AtEnd
	detail.Position = UDim2.fromOffset(12, 30)
	detail.Size = UDim2.new(1, -116, 0, 18)

	local switch = UIKit.button(frame, "", 14)
	switch.AutoButtonColor = false
	switch.AnchorPoint = Vector2.new(1, 0.5)
	switch.Position = UDim2.new(1, -10, 0.5, 0)
	switch.Size = UDim2.fromOffset(84, 40)
	UIKit.stroke(switch)
	switch.Activated:Connect(function()
		Settings.set(key, not Settings.get(key))
	end)
	switches[key] = switch
end

function SettingsUI.init(_hotbar)
	local _, body = UIKit.window("settings", "설정", 520, 300, nil, redraw)
	local list = UIKit.scroller(body, nil, 6)
	list.Size = UDim2.fromScale(1, 1)

	local listed = {}
	for order, entry in LIST do
		if Prefs.DEFAULTS[entry.key] ~= nil then
			listed[entry.key] = true
			row(list, order, entry.key, entry.name, entry.note)
		end
	end
	-- A setting added later shows up here under its own name until it is given a proper one.
	local rest = {}
	for key in Prefs.DEFAULTS do
		if not listed[key] then
			table.insert(rest, key)
		end
	end
	table.sort(rest)
	for i, key in rest do
		row(list, #LIST + i, key, key, "")
	end

	redraw()
	Settings.onChange(function()
		if Screens.isOpen("settings") then
			redraw()
		end
	end)
end

return SettingsUI
