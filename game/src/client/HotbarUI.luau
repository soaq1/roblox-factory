-- The nine quick slots, the creative palette, and the bag read-out.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared:WaitForChild("Defs"))
local Net = require(Shared:WaitForChild("Net"))

local HotbarUI = {}

local SLOT = 66
local PANEL = Color3.fromRGB(36, 39, 44)
local LINE = Color3.fromRGB(70, 76, 85)
local TEXT = Color3.fromRGB(233, 234, 236)
local PICK = Color3.fromRGB(240, 180, 41)
local MACHINE = Color3.fromRGB(194, 190, 183)

local slots = table.clone(Defs.DefaultHotbar)
local selected = 1
local slotFrames: { Frame } = {}
local palette: Frame
local bagLabel: TextLabel
local toast: TextLabel
local toastToken = 0

local function colorOf(id: string): Color3
	local block = Defs.Blocks[id]
	if block then
		return Color3.fromRGB(block.color[1], block.color[2], block.color[3])
	end
	return MACHINE
end

local function round(parent: Instance, radius: number)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, radius)
	corner.Parent = parent
end

local function label(parent: Instance, text: string, size: number): TextLabel
	local item = Instance.new("TextLabel")
	item.BackgroundTransparency = 1
	item.Font = Enum.Font.GothamMedium
	item.TextSize = size
	item.TextColor3 = TEXT
	item.TextWrapped = true
	item.Text = text
	item.Parent = parent
	return item
end

-- A tile showing one placeable: a colour swatch with its name underneath.
local function tile(parent: Instance, id: string): Frame
	local frame = Instance.new("Frame")
	frame.BackgroundColor3 = PANEL
	frame.BorderSizePixel = 0
	round(frame, 8)
	local stroke = Instance.new("UIStroke")
	stroke.Color = LINE
	stroke.Thickness = 1
	stroke.Parent = frame
	local swatch = Instance.new("Frame")
	swatch.Name = "Swatch"
	swatch.Size = UDim2.new(1, -20, 0, 22)
	swatch.Position = UDim2.fromOffset(10, 8)
	swatch.BorderSizePixel = 0
	swatch.BackgroundColor3 = colorOf(id)
	swatch.Parent = frame
	round(swatch, 4)
	local name = label(frame, Defs.name(id), 11)
	name.Name = "Name"
	name.Size = UDim2.new(1, -6, 1, -34)
	name.Position = UDim2.fromOffset(3, 32)
	frame.Parent = parent
	return frame
end

local function redraw()
	for i, frame in slotFrames do
		local id = slots[i]
		local swatch = frame:FindFirstChild("Swatch") :: Frame
		local name = frame:FindFirstChild("Name") :: TextLabel
		local stroke = frame:FindFirstChildOfClass("UIStroke") :: UIStroke
		swatch.BackgroundColor3 = colorOf(id)
		name.Text = Defs.name(id)
		stroke.Color = if i == selected then PICK else LINE
		stroke.Thickness = if i == selected then 3 else 1
	end
end

function HotbarUI.selected(): string
	return slots[selected]
end

function HotbarUI.select(index: number)
	if index >= 1 and index <= #slots then
		selected = index
		redraw()
	end
end

function HotbarUI.isPaletteOpen(): boolean
	return palette.Visible
end

function HotbarUI.togglePalette()
	palette.Visible = not palette.Visible
end

function HotbarUI.notify(text: string)
	toastToken += 1
	local token = toastToken
	toast.Text = text
	toast.Visible = true
	task.delay(5, function()
		if token == toastToken then
			toast.Visible = false
		end
	end)
end

local function showBag(bag: { [string]: number })
	local parts = {}
	for id, count in bag do
		table.insert(parts, Defs.name(id) .. " " .. count)
	end
	table.sort(parts)
	bagLabel.Text = if #parts > 0
		then "가방: " .. table.concat(parts, "  ·  ")
		else "가방: 비어 있음"
end

function HotbarUI.init()
	local gui = Instance.new("ScreenGui")
	gui.Name = "FactoryUI"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = false

	local bar = Instance.new("Frame")
	bar.BackgroundTransparency = 1
	bar.AnchorPoint = Vector2.new(0.5, 1)
	bar.Position = UDim2.new(0.5, 0, 1, -14)
	bar.Size = UDim2.fromOffset(#slots * (SLOT + 6), SLOT)
	bar.Parent = gui
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.Padding = UDim.new(0, 6)
	layout.Parent = bar

	for i, id in slots do
		local frame = tile(bar, id)
		frame.Size = UDim2.fromOffset(SLOT, SLOT)
		frame.LayoutOrder = i
		local number = label(frame, tostring(i), 11)
		number.Size = UDim2.fromOffset(14, 14)
		number.Position = UDim2.fromOffset(2, 0)
		number.TextColor3 = Color3.fromRGB(154, 160, 168)
		local button = Instance.new("TextButton")
		button.BackgroundTransparency = 1
		button.Text = ""
		button.Size = UDim2.fromScale(1, 1)
		button.Parent = frame
		button.Activated:Connect(function()
			HotbarUI.select(i)
		end)
		slotFrames[i] = frame
	end

	bagLabel = label(gui, "", 14)
	bagLabel.AnchorPoint = Vector2.new(0.5, 1)
	bagLabel.Position = UDim2.new(0.5, 0, 1, -(SLOT + 22))
	bagLabel.Size = UDim2.fromOffset(700, 20)
	bagLabel.TextStrokeTransparency = 0.5

	local hint = label(
		gui,
		"좌클릭 부수기 · 우클릭 놓기 · R 돌리기 · 1~9 고르기 · E 목록 · F 줍기",
		14
	)
	hint.AnchorPoint = Vector2.new(0.5, 0)
	hint.Position = UDim2.new(0.5, 0, 0, 8)
	hint.Size = UDim2.fromOffset(700, 20)
	hint.TextStrokeTransparency = 0.5

	toast = label(gui, "", 16)
	toast.AnchorPoint = Vector2.new(0.5, 0)
	toast.Position = UDim2.new(0.5, 0, 0, 40)
	toast.Size = UDim2.fromOffset(640, 44)
	toast.BackgroundTransparency = 0.15
	toast.BackgroundColor3 = PANEL
	toast.Visible = false
	round(toast, 8)

	palette = Instance.new("Frame")
	palette.AnchorPoint = Vector2.new(0.5, 0.5)
	palette.Position = UDim2.fromScale(0.5, 0.45)
	palette.Size = UDim2.fromOffset(5 * 96 + 28, 330)
	palette.BackgroundColor3 = Color3.fromRGB(28, 30, 34)
	palette.BorderSizePixel = 0
	palette.Visible = false
	palette.Parent = gui
	round(palette, 12)
	local title = label(palette, "고른 것이 지금 선택된 칸에 들어갑니다", 14)
	title.Size = UDim2.new(1, 0, 0, 30)
	title.Position = UDim2.fromOffset(0, 6)
	local grid = Instance.new("Frame")
	grid.BackgroundTransparency = 1
	grid.Position = UDim2.fromOffset(14, 40)
	grid.Size = UDim2.new(1, -28, 1, -50)
	grid.Parent = palette
	local gridLayout = Instance.new("UIGridLayout")
	gridLayout.CellSize = UDim2.fromOffset(88, 80)
	gridLayout.CellPadding = UDim2.fromOffset(8, 8)
	gridLayout.SortOrder = Enum.SortOrder.LayoutOrder
	gridLayout.Parent = grid
	for order, id in Defs.Palette do
		local frame = tile(grid, id)
		frame.LayoutOrder = order
		local button = Instance.new("TextButton")
		button.BackgroundTransparency = 1
		button.Text = ""
		button.Size = UDim2.fromScale(1, 1)
		button.Parent = frame
		button.Activated:Connect(function()
			slots[selected] = id
			redraw()
		end)
	end

	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	redraw()
	showBag({})
	Net.get("Bag").OnClientEvent:Connect(showBag)
	Net.get("Notify").OnClientEvent:Connect(HotbarUI.notify)
end

return HotbarUI
